"""
Student Registration Service

Handles student account creation with:
- Auto-generated student IDs (school_number + major_number + student_number)
- Secure password generation
- Custom JWT-based authentication
- Class resolution/creation

Uses SQLAlchemy AsyncSession for database operations.
"""

import hashlib
import logging
import uuid as uuid_module
from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.student import StudentAccountCreate, StudentAccountResponse
from app.core.config import settings
from app.utils.string_utils import sanitize_name
from app.utils.password_generator import PasswordGenerator
from app.core.password import hash_password as bcrypt_hash_password, verify_password
from app.core.jwt import get_jwt_manager
from app.core.auth_user import AuthenticatedUser

# Repository imports
from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.major_repository import MajorRepository
from app.repositories.class_repository import ClassRepository

# Model imports
from app.models.user_profile import UserProfile
from app.models.student import Student

# Setup logging
logger = logging.getLogger(__name__)

# Student role ID (from seed data)
STUDENT_ROLE_ID = 3

# Internal email domain for student accounts (used as workaround for username login)
STUDENT_EMAIL_DOMAIN = "students.internal"


class StudentRegistrationService:
    """
    Service for student account registration and management.
    
    Handles the complete flow of creating student accounts including:
    - School/major number assignment
    - Student ID generation
    - Password generation
    - User profile creation with hashed password
    - Class resolution
    
    Updated to use SQLAlchemy AsyncSession and repositories.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with SQLAlchemy AsyncSession.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.password_generator = PasswordGenerator()
        self.jwt_manager = get_jwt_manager()
        
        # Initialize repositories
        self.user_repo = UserRepository(db)
        self.student_repo = StudentRepository(db)
        self.teacher_repo = TeacherRepository(db)
        self.school_repo = SchoolRepository(db)
        self.major_repo = MajorRepository(db)
        self.class_repo = ClassRepository(db)
        
        # Optional caches to reduce repeated lookups during bulk creation.
        # Keys are normalized (lowercased) sanitized names.
        self._school_cache: Optional[dict] = None  # key -> (school_id, school_number)
        self._major_cache: Optional[dict] = None   # key -> (major_id, major_number)
        self._class_cache: Optional[dict] = None   # (key, grade_level) -> class_id

    # =========================================================================
    # UTILITY METHODS
    # =========================================================================

    def _generate_secure_password(self, pattern: str) -> str:
        """Generate a secure random password using a position-based pattern."""
        return self.password_generator.generate(pattern)

    def _hash_password(self, password: str) -> str:
        """
        Hash password for storage (for display purposes, not auth).
        Uses SHA-256 with salt for basic obfuscation.
        Note: Actual auth uses bcrypt.
        """
        return hashlib.sha256(f"{settings.STUDENT_PASSWORD_SALT}{password}".encode()).hexdigest()

    def _generate_student_email(self, student_id: str) -> str:
        """
        Generate a fake email for auth.
        Format: {student_id}@students.internal
        """
        return f"{student_id}@{STUDENT_EMAIL_DOMAIN}"

    # =========================================================================
    # SCHOOL METHODS
    # =========================================================================

    async def _resolve_or_create_school(self, school_name: str) -> Tuple[int, str]:
        """
        Find existing school by name or create new one.
        Returns tuple of (school_id, school_number).
        """
        logger.debug(f"[_resolve_or_create_school] Resolving school: {school_name}")
        sanitized_name = sanitize_name(school_name)
        if not sanitized_name:
            logger.error(f"[_resolve_or_create_school] School name is empty after sanitization")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="School name cannot be empty."
            )
        
        logger.debug(f"[_resolve_or_create_school] Sanitized name: {sanitized_name}")

        cache_key = sanitized_name.lower()
        if self._school_cache is not None and cache_key in self._school_cache:
            return self._school_cache[cache_key]

        # Use repository method which calls the RPC function
        school_id, school_number = await self.school_repo.resolve_or_create(sanitized_name)
        
        if school_number is None:
            # Assign number if not yet assigned
            school_number = await self._assign_school_number(school_id)
        
        result = (school_id, school_number)
        if self._school_cache is not None:
            self._school_cache[cache_key] = result
        
        logger.info(f"[_resolve_or_create_school] School resolved: id={school_id}, number={school_number}")
        return result

    async def _assign_school_number(self, school_id: int) -> str:
        """
        Assign the next available school number to a school.
        Uses database function for atomicity.
        """
        result = await self.school_repo.assign_number(school_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign school number."
            )
        return result

    # =========================================================================
    # MAJOR METHODS
    # =========================================================================

    async def _resolve_or_create_major(self, major_name: str) -> Tuple[int, str]:
        """
        Find existing major by name or create new one.
        Returns tuple of (major_id, major_number).
        """
        logger.debug(f"[_resolve_or_create_major] Resolving major: {major_name}")
        sanitized_name = sanitize_name(major_name)
        if not sanitized_name:
            logger.error(f"[_resolve_or_create_major] Major name is empty after sanitization")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Major name cannot be empty."
            )
        
        logger.debug(f"[_resolve_or_create_major] Sanitized name: {sanitized_name}")

        cache_key = sanitized_name.lower()
        if self._major_cache is not None and cache_key in self._major_cache:
            return self._major_cache[cache_key]

        # Use repository method which calls the RPC function
        major_id, major_number = await self.major_repo.resolve_or_create(sanitized_name)
        
        if major_number is None:
            # Assign number if not yet assigned
            major_number = await self._assign_major_number(major_id)
        
        result = (major_id, major_number)
        if self._major_cache is not None:
            self._major_cache[cache_key] = result
        
        logger.info(f"[_resolve_or_create_major] Major resolved: id={major_id}, number={major_number}")
        return result

    async def _assign_major_number(self, major_id: int) -> str:
        """
        Assign the next available major number to a major.
        Uses database function for atomicity.
        """
        result = await self.major_repo.assign_number(major_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to assign major number."
            )
        return result

    # =========================================================================
    # CLASS METHODS
    # =========================================================================

    async def _resolve_or_create_class(
        self,
        class_id: Optional[int],
        class_name: Optional[str],
        grade_level: Optional[int]
    ) -> int:
        """
        Resolve class by ID or find/create by name and grade level.
        Returns class_id.
        """
        logger.debug(f"[_resolve_or_create_class] Resolving class: class_id={class_id}, class_name={class_name}, grade_level={grade_level}")
        
        if class_id is not None:
            logger.debug(f"[_resolve_or_create_class] Validating class by id: {class_id}")
            # Validate class exists
            existing_class = await self.class_repo.get_by_id(class_id)
            
            if not existing_class:
                logger.error(f"[_resolve_or_create_class] Class not found: {class_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Class with id {class_id} does not exist."
                )
            logger.info(f"[_resolve_or_create_class] Class found by id: {class_id}")
            return class_id
        
        # Must have class_name and grade_level
        if not class_name or grade_level is None:
            logger.error(f"[_resolve_or_create_class] Missing required parameters: class_name={class_name}, grade_level={grade_level}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either class_id or both class_name and grade_level must be provided."
            )
        
        sanitized_name = sanitize_name(class_name)
        if not sanitized_name:
            logger.error(f"[_resolve_or_create_class] Class name is empty after sanitization")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class name cannot be empty."
            )
        
        logger.debug(f"[_resolve_or_create_class] Searching for existing class: name={sanitized_name}, grade={grade_level}")

        cache_key = (sanitized_name.lower(), grade_level)
        if self._class_cache is not None and cache_key in self._class_cache:
            return self._class_cache[cache_key]

        # Use repository method which calls the RPC function
        resolved_id, _, _ = await self.class_repo.resolve_or_create(sanitized_name, grade_level)
        
        if self._class_cache is not None:
            self._class_cache[cache_key] = resolved_id
        
        logger.info(f"[_resolve_or_create_class] Class resolved: id={resolved_id}")
        return resolved_id

    # =========================================================================
    # STUDENT ID GENERATION
    # =========================================================================

    async def _get_next_student_number(self, school_id: int, major_id: int) -> str:
        """
        Get the next sequential student number for a school+major combination.
        Uses database function for atomic increment.
        Returns 5-digit padded string.
        """
        result = await self.db.execute(
            text("SELECT public.get_next_student_number(:p_school_id, :p_major_id)"),
            {"p_school_id": school_id, "p_major_id": major_id}
        )
        row = result.scalar()
        
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate student number."
            )
        
        # Pad to 5 digits
        return str(row).zfill(5)

    async def _generate_student_id(
        self,
        school_id: int,
        school_number: str,
        major_id: int,
        major_number: str
    ) -> str:
        """
        Generate a unique student ID.
        Format: {school_number(3)}{major_number(4)}{student_number(5)} = 12 digits
        Example: 001000100001
        """
        student_number = await self._get_next_student_number(school_id, major_id)
        return f"{school_number}{major_number}{student_number}"

    # =========================================================================
    # USER PROFILE CREATION (Custom Auth)
    # =========================================================================

    async def _create_auth_user(
        self,
        student_id: str,
        password: str,
        full_name: str
    ) -> UUID:
        """
        Create a user profile for the student.
        
        Creates the user_profile record directly with the hashed password
        using custom JWT-based authentication.
        
        Returns the user UUID.
        """
        fake_email = self._generate_student_email(student_id)
        logger.debug(f"[_create_auth_user] Creating user profile with email={fake_email}, student_id={student_id}")
        
        try:
            # Generate a new UUID for the user
            user_id = uuid_module.uuid4()
            
            # Hash the password for storage
            hashed_pwd = bcrypt_hash_password(password)
            
            # Create user profile using repository
            user_profile = await self.user_repo.create_user(
                id=user_id,
                email=fake_email,
                full_name=full_name,
                hashed_password=hashed_pwd,
                role_id=STUDENT_ROLE_ID,
            )
            
            logger.info(f"[_create_auth_user] User profile created successfully: user_id={user_id}")
            return user_id
            
        except HTTPException:
            logger.error(f"[_create_auth_user] HTTPException raised")
            raise
        except Exception as e:
            error_message = str(e)
            logger.error(f"[_create_auth_user] Exception occurred: {error_message}", exc_info=True)
            if "duplicate" in error_message.lower() or "already exists" in error_message.lower():
                logger.warning(f"[_create_auth_user] Student already exists: {student_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A student with ID {student_id} already exists."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {error_message}"
            )

    async def _create_student_record(
        self,
        user_id: UUID,
        student_id: str,
        school_id: int,
        major_id: int,
        class_id: int,
        hashed_password: str
    ) -> int:
        """
        Create student record in students table.
        Returns the student record ID.
        """
        student = await self.student_repo.create(
            user_id=user_id,
            student_id=student_id,
            school_id=school_id,
            major_id=major_id,
            current_class_id=class_id,
            stored_password=hashed_password,
        )
        
        return student.id

    # =========================================================================
    # MAIN REGISTRATION METHODS
    # =========================================================================

    async def create_student_account(
        self,
        data: StudentAccountCreate,
        creator_school_id: Optional[int] = None
    ) -> StudentAccountResponse:
        """
        Create a single student account.
        
        Args:
            data: Student account creation data
            creator_school_id: School ID from teacher's profile (used if school_name not provided)
        
        Returns:
            StudentAccountResponse with generated credentials
        """
        logger.info(f"[create_student_account] Starting account creation for: {data.full_name}")
        logger.debug(f"[create_student_account] Request data: school_name={data.school_name}, major_name={data.major_name}, class_id={data.class_id}, class_name={data.class_name}")
        
        # Resolve school
        if data.school_name:
            logger.debug(f"[create_student_account] Resolving school by name: {data.school_name}")
            school_id, school_number = await self._resolve_or_create_school(data.school_name)
            logger.info(f"[create_student_account] School resolved: id={school_id}, number={school_number}")
        elif creator_school_id:
            logger.debug(f"[create_student_account] Using creator's school: {creator_school_id}")
            # Get school info from creator's school
            school = await self.school_repo.get_by_id(creator_school_id)
            
            if not school:
                logger.error(f"[create_student_account] Creator's school not found: {creator_school_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Creator's school not found."
                )
            
            school_id = school.id
            school_number = school.school_number
            logger.info(f"[create_student_account] Creator's school retrieved: id={school_id}, number={school_number}")
            
            if not school_number:
                logger.debug(f"[create_student_account] Assigning school number for: {school_id}")
                school_number = await self._assign_school_number(school_id)
                logger.info(f"[create_student_account] School number assigned: {school_number}")
        else:
            logger.error("[create_student_account] School name is required but not provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="School name is required."
            )
        
        # Resolve major
        logger.debug(f"[create_student_account] Resolving major: {data.major_name}")
        major_id, major_number = await self._resolve_or_create_major(data.major_name)
        logger.info(f"[create_student_account] Major resolved: id={major_id}, number={major_number}")
        
        # Resolve class
        grade_level_value = data.grade_level.value if data.grade_level else None
        logger.debug(f"[create_student_account] Resolving class: class_id={data.class_id}, class_name={data.class_name}, grade_level={grade_level_value}")
        class_id = await self._resolve_or_create_class(
            data.class_id,
            data.class_name,
            grade_level_value
        )
        logger.info(f"[create_student_account] Class resolved: id={class_id}")
        
        # Generate student ID
        logger.debug(f"[create_student_account] Generating student ID with school_id={school_id}, major_id={major_id}")
        student_id = await self._generate_student_id(
            school_id, school_number,
            major_id, major_number
        )
        logger.info(f"[create_student_account] Student ID generated: {student_id}")
        
        # Generate password
        logger.debug("[create_student_account] Generating secure password")
        password = self._generate_secure_password(pattern="UUUUUNNN")

        # Hashed password is disabled for MVP display purposes
        # hashed_password = self._hash_password(password)
        hashed_password = password
        logger.debug("[create_student_account] Password generated and hashed")
        
        # Create auth user (trigger automatically creates user_profile)
        logger.debug(f"[create_student_account] Creating user profile for student_id={student_id}")
        user_id = await self._create_auth_user(
            student_id, password, data.full_name
        )
        logger.info(f"[create_student_account] User profile created successfully: user_id={user_id}")
        
        try:
            # Create student record
            logger.debug(f"[create_student_account] Creating student record with user_id={user_id}, student_id={student_id}")
            record_id = await self._create_student_record(
                user_id, student_id, school_id, major_id, class_id, hashed_password
            )
            logger.info(f"[create_student_account] Student record created successfully: record_id={record_id}")
            
            logger.info(f"[create_student_account] Successfully completed account creation for {data.full_name}")
            return StudentAccountResponse(
                id=record_id,
                user_id=user_id,
                full_name=data.full_name,
                student_id=student_id,
                current_class_id=class_id,
                password=password  # Return plaintext for display
            )
            
        except Exception as e:
            logger.error(f"[create_student_account] Error during student record creation: {str(e)}", exc_info=False)
            # Cleanup: delete user profile if subsequent steps fail
            try:
                logger.debug(f"[create_student_account] Cleaning up user profile: {user_id}")
                await self.user_repo.delete(user_id)
                logger.info(f"[create_student_account] User profile deleted during cleanup")
            except Exception as cleanup_error:
                logger.warning(f"[create_student_account] Failed to cleanup user profile: {str(cleanup_error)}")
            raise

    async def bulk_create_student_accounts(
        self,
        data_list: List[StudentAccountCreate],
        creator_school_id: Optional[int] = None
    ) -> List[StudentAccountResponse]:
        """
        Create multiple student accounts in a single transaction.
        All-or-nothing: if any fails, all are rolled back.
        
        Args:
            data_list: List of student account creation data
            creator_school_id: School ID from teacher's profile
        
        Returns:
            List of StudentAccountResponse with generated credentials
        """
        if not data_list:
            return []

        # Enable per-call caches to reduce repeated resolve/create work.
        # These caches only live for the duration of this bulk request.
        self._school_cache = {}
        self._major_cache = {}
        self._class_cache = {}

        results: List[StudentAccountResponse] = []
        created_user_ids: List[UUID] = []
        
        try:
            for data in data_list:
                result = await self.create_student_account(data, creator_school_id)
                results.append(result)
                created_user_ids.append(result.user_id)
            
            return results
            
        except Exception as e:
            # Rollback: delete all created user profiles
            for user_id in created_user_ids:
                try:
                    await self.user_repo.delete(user_id)
                except:
                    pass  # Best effort cleanup
            
            # Re-raise the original exception
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk creation failed: {str(e)}. All changes have been rolled back."
            )
        finally:
            self._school_cache = None
            self._major_cache = None
            self._class_cache = None

    # =========================================================================
    # STUDENT LOGIN SUPPORT
    # =========================================================================

    async def authenticate_student(
        self,
        student_id: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Authenticate a student using their student ID and password.
        Uses custom JWT authentication.
        
        Returns:
            Dict with user, session, access_token, refresh_token
        """
        fake_email = self._generate_student_email(student_id)
        
        try:
            # Get user profile with role info
            user_profile = await self.user_repo.get_by_email_with_role(fake_email)
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect student ID or password"
                )
            
            hashed_password = user_profile.hashed_password
            
            if not hashed_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect student ID or password"
                )
            
            # Verify password
            if not verify_password(password, hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect student ID or password"
                )
            
            role_name = user_profile.role.role_name if user_profile.role else None
            
            # Generate tokens
            token_pair = self.jwt_manager.create_token_pair(
                user_id=str(user_profile.id),
                email=user_profile.email,
                role_id=user_profile.role_id,
                role_name=role_name
            )
            
            # Build authenticated user object
            user = AuthenticatedUser(
                id=user_profile.id,
                email=user_profile.email,
                full_name=user_profile.full_name,
                role_id=user_profile.role_id,
                role_name=role_name,
                created_at=user_profile.created_at.isoformat() if user_profile.created_at else None,
                updated_at=user_profile.updated_at.isoformat() if user_profile.updated_at else None
            )
            
            return {
                "user": user,
                "session": {
                    "access_token": token_pair.access_token,
                    "refresh_token": token_pair.refresh_token,
                    "token_type": token_pair.token_type,
                    "expires_in": token_pair.expires_in
                },
                "access_token": token_pair.access_token,
                "refresh_token": token_pair.refresh_token
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect student ID or password"
            )

    async def get_teacher_school_id(self, user_id: UUID) -> Optional[int]:
        """
        Get the school_id associated with a teacher.
        Returns None if user is not a teacher or has no school assigned.
        """
        teacher = await self.teacher_repo.get_by_user_id(user_id)
        
        if teacher:
            return teacher.school_id
        
        return None

    async def get_student_context_by_student_id(self, student_id: str) -> dict:
        """
        Fetch student details along with related profile, school, major, and class data.
        """
        try:
            student = await self.student_repo.get_by_student_id(student_id)
            
            if not student:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student record not found for ID {student_id}."
                )
            
            # Get student with relations for full context
            student_with_relations = await self.student_repo.get_with_relations(student.id)
            
            if not student_with_relations:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Student record not found for ID {student_id}."
                )
            
            # Format the response to match expected API structure
            result = {
                "id": student_with_relations.id,
                "user_id": str(student_with_relations.user_id),
                "student_id": student_with_relations.student_id,
                "interview_session_quota": student_with_relations.interview_session_quota,
                "user_profiles": {
                    "full_name": student_with_relations.user.full_name if student_with_relations.user else None,
                    "role_id": student_with_relations.user.role_id if student_with_relations.user else None,
                    "roles": {
                        "role_name": student_with_relations.user.role.role_name if student_with_relations.user and student_with_relations.user.role else None
                    }
                },
                "schools": {
                    "id": student_with_relations.school.id if student_with_relations.school else None,
                    "school_name": student_with_relations.school.school_name if student_with_relations.school else None
                } if student_with_relations.school else None,
                "majors": {
                    "id": student_with_relations.major.id if student_with_relations.major else None,
                    "major_name": student_with_relations.major.major_name if student_with_relations.major else None
                } if student_with_relations.major else None,
                "classes": {
                    "id": student_with_relations.current_class.id if student_with_relations.current_class else None,
                    "class_name": student_with_relations.current_class.class_name if student_with_relations.current_class else None,
                    "grade_level": student_with_relations.current_class.grade_level if student_with_relations.current_class else None
                } if student_with_relations.current_class else None
            }
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
