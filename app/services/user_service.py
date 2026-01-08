"""
User Profile Service for user management operations.

Refactored from Supabase AsyncClient to SQLAlchemy AsyncSession.
Uses UserRepository for database operations.
"""
from typing import Optional, Tuple, List, Any
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.schemas.auth import UserResponse
from app.schemas.types import RoleType, RoleName
from app.models.user_profile import UserProfile
from app.models.role import Role
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.school import School
from app.models.major import Major
from app.models.class_ import Class
from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.utils.pagination import paginate_query


class UserProfileService:
    """
    Service for managing user profiles in public.user_profiles table.
    
    Note: User profiles are auto-created via database trigger when users register.
    This service is mainly for querying and updating existing profiles.
    
    All methods are async because SQLAlchemy AsyncSession
    uses async database calls. This ensures proper connection handling
    under concurrent load.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.user_repo = UserRepository(db)
        self.student_repo = StudentRepository(db)
        self.teacher_repo = TeacherRepository(db)

    async def get_profile(self, user_id: UUID) -> dict:
        """
        Get user profile by UUID from user_profiles table.
        
        Args:
            user_id: User's UUID
        
        Returns:
            dict: User profile data
        """
        try:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return self._profile_to_dict(user)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_profile_with_role(self, user_id: UUID) -> dict:
        """
        Get user profile with role information using relational select.
        
        Args:
            user_id: User's UUID
        
        Returns:
            dict: User profile with role data
        """
        try:
            user = await self.user_repo.get_with_role(user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return self._profile_to_dict_with_role(user)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_full_user_context(self, user_id: UUID) -> dict:
        """
        Get complete user context including profile, role, and student/teacher details
        in optimized queries to avoid N+1 patterns.
        
        Returns a dict with profile, role, and optional student/teacher details.
        """
        try:
            user = await self.user_repo.get_full_context(user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

            profile = self._profile_to_dict_with_role(user)
            student_details = self._student_to_dict(user.student) if user.student else None
            teacher_details = self._teacher_to_dict(user.teacher) if user.teacher else None

            return {
                "profile": profile,
                "student_details": student_details,
                "teacher_details": teacher_details
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_student_details(self, user_id: UUID) -> Optional[dict]:
        """
        Get student details by user_id with related information.
        
        Args:
            user_id: User's UUID
        
        Returns:
            dict: Student details or None
        """
        try:
            student = await self.student_repo.get_by_user_id_with_relations(user_id)
            if student:
                return self._student_to_dict(student)
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_details(self, user_id: UUID) -> Optional[dict]:
        """
        Get teacher details by user_id.
        
        Args:
            user_id: User's UUID
        
        Returns:
            dict: Teacher details or None
        """
        try:
            teacher = await self.teacher_repo.get_by_user_id(user_id)
            if teacher:
                return self._teacher_to_dict(teacher)
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def build_user_response(
        self,
        user: Any,
        profile: Optional[dict] = None,
        student_details: Optional[dict] = None,
        teacher_details: Optional[dict] = None,
    ) -> UserResponse:
        """
        Normalize user + profile context into a UserResponse model.
        
        Works with both AuthenticatedUser (custom auth) and legacy user objects.
        """
        role_name = None
        role_id: Optional[int] = None

        if profile:
            roles_data = profile.get("roles") if isinstance(profile, dict) else None
            if isinstance(roles_data, dict):
                role_name = roles_data.get("role_name")
            profile_role_id = profile.get("role_id") if isinstance(profile, dict) else None
            if profile_role_id is not None:
                try:
                    role_id = int(profile_role_id)
                except (ValueError, TypeError):
                    role_id = None

        # Check for role_id on user object (AuthenticatedUser has role_id directly)
        if role_id is None:
            user_role_id = getattr(user, "role_id", None)
            if user_role_id is not None:
                try:
                    role_id = int(user_role_id)
                except (ValueError, TypeError):
                    role_id = None
        
        # Fallback to user_metadata (legacy Supabase user)
        if role_id is None:
            meta_role_id = getattr(user, "user_metadata", {}).get("role_id") if hasattr(user, "user_metadata") else None
            if meta_role_id is not None:
                try:
                    role_id = int(meta_role_id)
                except (ValueError, TypeError):
                    role_id = None

        # Get role_name from user object if not found in profile
        if role_name is None:
            role_name = getattr(user, "role_name", None)

        full_name = None
        if profile and isinstance(profile, dict):
            full_name = profile.get("full_name")
        if full_name is None:
            # Try AuthenticatedUser's full_name attribute
            full_name = getattr(user, "full_name", None)
        if full_name is None and hasattr(user, "user_metadata"):
            full_name = user.user_metadata.get("full_name") if user.user_metadata else None

        # Get created_at - handle both datetime and string
        created_at = getattr(user, "created_at", None)
        if profile and isinstance(profile, dict) and created_at is None:
            created_at = profile.get("created_at")

        return UserResponse(
            id=str(getattr(user, "id")),
            email=getattr(user, "email"),
            full_name=str(full_name) if full_name is not None else None,
            role_id=role_id,
            role_name=str(role_name) if role_name is not None else None,
            student_details=dict(student_details) if student_details and isinstance(student_details, dict) else None,
            teacher_details=dict(teacher_details) if teacher_details and isinstance(teacher_details, dict) else None,
            created_at=created_at,
        )

    async def get_profile_by_email(self, email: str) -> Optional[dict]:
        """
        Get user profile by email from user_profiles table.
        
        Args:
            email: User's email address
        
        Returns:
            dict: User profile or None
        """
        try:
            user = await self.user_repo.get_by_email(email)
            if not user:
                return None
            return self._profile_to_dict(user)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def _shape_user_list_item(self, user: UserProfile) -> dict:
        """
        Normalize user to match UserListItemResponse format.
        
        Args:
            user: UserProfile SQLAlchemy model instance
        
        Returns:
            dict: Shaped user list item
        """
        role_name = user.role.role_name if user.role else None

        password = None
        student_id = None
        school_name = None
        major_name = None
        
        if role_name == RoleName.STUDENT.value and user.student:
            student = user.student
            password = student.stored_password
            student_id = student.student_id
            
            if student.school:
                school_name = student.school.school_name
            
            if student.major:
                major_name = student.major.major_name

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": role_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "student_id": student_id if role_name == RoleName.STUDENT.value else None,
            "password": password if role_name == RoleName.STUDENT.value else None,
            "school_name": school_name if role_name == RoleName.STUDENT.value else None,
            "major_name": major_name if role_name == RoleName.STUDENT.value else None,
        }

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        role: Optional[str] = None,
        search: Optional[str] = None,
        viewer_role: str = RoleName.ADMIN.value,
        viewer_user_id: Optional[UUID] = None,
    ) -> Tuple[List[dict], int]:
        """
        List users with role-aware filtering and pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role: Filter by role name
            search: Search term for full_name or email
            viewer_role: Role of the user making the request
            viewer_user_id: UUID of the user making the request
        
        Returns:
            Tuple of (list of shaped users, total count)
        """
        try:
            role_filter_id: Optional[int] = None
            if role:
                role_normalized = role.lower()
                role_map = {
                    RoleName.ADMIN.value: RoleType.ADMIN.value,
                    RoleName.TEACHER.value: RoleType.TEACHER.value,
                    RoleName.STUDENT.value: RoleType.STUDENT.value,
                }
                if role_normalized not in role_map:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid role filter",
                    )
                role_filter_id = role_map[role_normalized]

            viewer_school_id: Optional[int] = None
            viewer_role_normalized = viewer_role.lower() if viewer_role else None
            
            if viewer_role_normalized == RoleName.TEACHER.value:
                if viewer_user_id is None:
                    return [], 0

                teacher = await self.teacher_repo.get_by_user_id(viewer_user_id)
                if teacher:
                    viewer_school_id = teacher.school_id

                if not viewer_school_id:
                    return [], 0

                role_filter_id = RoleType.STUDENT.value

            # Build query with eager loading
            query = (
                select(UserProfile)
                .options(
                    joinedload(UserProfile.role),
                    selectinload(UserProfile.student).options(
                        joinedload(Student.school),
                        joinedload(Student.major),
                    ),
                )
            )
            
            # Apply filters
            if role_filter_id is not None:
                query = query.where(UserProfile.role_id == role_filter_id)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        UserProfile.full_name.ilike(search_pattern),
                        UserProfile.email.ilike(search_pattern)
                    )
                )
            
            # Teacher-specific school filter (inner join on students)
            if viewer_role_normalized == RoleName.TEACHER.value and viewer_school_id is not None:
                query = query.join(Student, UserProfile.id == Student.user_id)
                query = query.where(Student.school_id == viewer_school_id)
            
            query = query.order_by(UserProfile.created_at.desc())
            
            # Execute with pagination
            # Note: Using unique() because of joined relationships
            count_stmt = select(func.count()).select_from(query.subquery())
            total = (await self.db.execute(count_stmt)).scalar() or 0
            
            paginated_query = query.offset(skip).limit(limit)
            result = await self.db.execute(paginated_query)
            users = result.unique().scalars().all()
            
            shaped_items = [self._shape_user_list_item(user) for user in users]
            return shaped_items, total
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # =========================================================================
    # Helper methods for model-to-dict conversion
    # =========================================================================

    def _profile_to_dict(self, user: UserProfile) -> dict:
        """Convert UserProfile model to basic dict."""
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role_id": user.role_id,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    def _profile_to_dict_with_role(self, user: UserProfile) -> dict:
        """Convert UserProfile model to dict with role info."""
        result = self._profile_to_dict(user)
        if user.role:
            result["roles"] = {
                "id": user.role.id,
                "role_name": user.role.role_name,
            }
        else:
            result["roles"] = None
        return result

    def _student_to_dict(self, student: Student) -> dict:
        """Convert Student model to dict with relations."""
        result = {
            "id": student.id,
            "user_id": str(student.user_id),
            "school_id": student.school_id,
            "major_id": student.major_id,
            "current_class_id": student.current_class_id,
            "interview_session_quota": student.interview_session_quota,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None,
        }
        
        if student.school:
            result["schools"] = {
                "id": student.school.id,
                "school_name": student.school.school_name,
            }
        
        if student.major:
            result["majors"] = {
                "id": student.major.id,
                "major_name": student.major.major_name,
            }
        
        if student.current_class:
            result["classes"] = {
                "id": student.current_class.id,
                "class_name": student.current_class.class_name,
                "grade_level": student.current_class.grade_level,
            }
        
        return result

    def _teacher_to_dict(self, teacher: Teacher) -> dict:
        """Convert Teacher model to dict with relations."""
        result = {
            "id": teacher.id,
            "user_id": str(teacher.user_id),
            "created_at": teacher.created_at.isoformat() if teacher.created_at else None,
            "updated_at": teacher.updated_at.isoformat() if teacher.updated_at else None,
        }
        
        if teacher.school:
            result["schools"] = {
                "id": teacher.school.id,
                "school_name": teacher.school.school_name,
            }
        
        return result

    @staticmethod
    def _first_relationship_record(relationship: Any) -> Optional[dict]:
        """
        Return the first related record regardless of response shape.
        
        Kept for backward compatibility with dict-based responses.
        """
        if not relationship:
            return None
        if isinstance(relationship, list):
            return relationship[0] if relationship else None
        return relationship
