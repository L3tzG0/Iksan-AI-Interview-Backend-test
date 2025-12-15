from typing import Optional, Tuple, List, Any
from supabase import AsyncClient
from fastapi import HTTPException, status
from uuid import UUID
from app.schemas.auth import UserResponse
from app.utils.pagination import paginate_query
from app.schemas.types import RoleType, RoleName

# Explicit columns to select for user profiles (avoiding SELECT *)
USER_PROFILE_COLUMNS = "id, email, full_name, role_id, created_at, updated_at"
USER_PROFILE_COLUMNS_WITH_ROLE = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name)
"""
USER_LIST_COLUMNS = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(role_name),
    students(student_id, stored_password, school_id)
"""

# For fetching complete user with all details in a single query
USER_FULL_DETAILS_QUERY = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name)
"""

USER_FULL_CONTEXT_QUERY = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name),
    students!user_id(
        id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
        schools(id, school_name),
        majors(id, major_name),
        classes(id, class_name, grade_level)
    ),
    teachers!user_id(
        id, user_id, created_at, updated_at,
        schools(id, school_name)
    )
"""


class UserProfileService:
    """
    Service for managing user profiles in public.user_profiles table.
    Note: User profiles are auto-created via database trigger when users register.
    This service is mainly for querying and updating existing profiles.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def get_profile(self, user_id: UUID):
        """Get user profile by UUID from user_profiles table with explicit columns"""
        try:
            response = await self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_profile_with_role(self, user_id: UUID):
        """Get user profile with role information using relational select"""
        try:
            response = await self.supabase.table('user_profiles').select(
                USER_PROFILE_COLUMNS_WITH_ROLE
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_full_user_context(self, user_id: UUID):
        """
        Get complete user context including profile, role, and student/teacher details
        in optimized queries to avoid N+1 patterns.
        
        Returns a dict with profile, role, and optional student/teacher details.
        """
        try:
            response = await self.supabase.table('user_profiles').select(
                USER_FULL_CONTEXT_QUERY
            ).eq('id', str(user_id)).execute()

            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

            payload = response.data[0]
            profile = {
                key: value
                for key, value in payload.items()
                if key not in ("students", "teachers")
            }

            student_details = self._first_relationship_record(payload.get("students"))
            teacher_details = self._first_relationship_record(payload.get("teachers"))

            return {
                "profile": profile,
                "student_details": student_details,
                "teacher_details": teacher_details
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_student_details(self, user_id: UUID):
        """Get student details by user_id with related information in single query"""
        try:
            response = await self.supabase.table('students').select(
                """id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
                   schools(id, school_name),
                   majors(id, major_name),
                   classes(id, class_name, grade_level)"""
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_details(self, user_id: UUID):
        """Get teacher details by user_id with explicit columns"""
        try:
            response = await self.supabase.table('teachers').select(
                "id, user_id, created_at, updated_at"
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
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
        """Normalize user + profile context into a UserResponse model."""
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

        if role_id is None:
            meta_role_id = getattr(user, "user_metadata", {}).get("role_id") if hasattr(user, "user_metadata") else None
            if meta_role_id is not None:
                try:
                    role_id = int(meta_role_id)
                except (ValueError, TypeError):
                    role_id = None

        full_name = None
        if profile and isinstance(profile, dict):
            full_name = profile.get("full_name")
        if full_name is None and hasattr(user, "user_metadata"):
            full_name = user.user_metadata.get("full_name") if user.user_metadata else None

        return UserResponse(
            id=str(getattr(user, "id")),
            email=getattr(user, "email"),
            full_name=str(full_name) if full_name is not None else None,
            role_id=role_id,
            role_name=str(role_name) if role_name is not None else None,
            student_details=dict(student_details) if student_details and isinstance(student_details, dict) else None,
            teacher_details=dict(teacher_details) if teacher_details and isinstance(teacher_details, dict) else None,
            created_at=getattr(user, "created_at"),
        )

    async def get_profile_by_email(self, email: str):
        """Get user profile by email from user_profiles table with explicit columns"""
        try:
            response = await self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('email', email).execute()
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    def _first_relationship_record(relationship: Any) -> Optional[dict]:
        """Return the first related record regardless of Supabase response shape."""
        if not relationship:
            return None
        if isinstance(relationship, list):
            return relationship[0] if relationship else None
        return relationship

    def _shape_user_list_item(self, payload: dict) -> dict:
        """Normalize list payload to match UserListItemResponse."""
        roles_data = payload.get("roles") if isinstance(payload, dict) else None
        role_name = roles_data.get("role_name") if isinstance(roles_data, dict) else None

        student_data = self._first_relationship_record(payload.get("students")) if isinstance(payload, dict) else None
        password = None
        student_id = None
        if role_name == RoleName.STUDENT.value and isinstance(student_data, dict):
            password = student_data.get("stored_password")
            student_id = student_data.get("student_id")

        return {
            "id": payload.get("id"),
            "email": payload.get("email"),
            "full_name": payload.get("full_name"),
            "role": role_name,
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "student_id": student_id if role_name == RoleName.STUDENT.value else None,
            "password": password if role_name == RoleName.STUDENT.value else None,
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
        """List users with role-aware filtering and pagination."""
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

                teacher_response = await self.supabase.table("teachers").select("school_id").eq("user_id", str(viewer_user_id)).execute()
                teacher_rows = teacher_response.data if teacher_response else None
                if teacher_rows and isinstance(teacher_rows, list) and teacher_rows[0]:
                    viewer_school_id = teacher_rows[0].get("school_id")

                if not viewer_school_id:
                    return [], 0

                role_filter_id = RoleType.STUDENT.value

            def build_query():
                base_query = self.supabase.table("user_profiles").select(USER_LIST_COLUMNS, count="exact")
                if role_filter_id is not None:
                    base_query = base_query.eq("role_id", role_filter_id)
                if search:
                    base_query = base_query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
                if viewer_role_normalized == RoleName.TEACHER.value and viewer_school_id is not None:
                    base_query = base_query.eq("students.school_id", viewer_school_id)
                return base_query

            items, total = await paginate_query(build_query, skip, limit)
            shaped_items = [self._shape_user_list_item(item) for item in items]
            return shaped_items, total
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
