"""
Authentication Service

Handles user registration, login, and session management using custom JWT-based
authentication with passwords stored in the user_profiles table.

Uses SQLAlchemy AsyncSession for database operations.
"""
import uuid
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import LoginRequest, RegisterRequest, TeacherRegistrationData
from app.utils.string_utils import sanitize_name
from app.core.password import hash_password, verify_password
from app.core.jwt import get_jwt_manager, JWTExpiredError, JWTInvalidError
from app.core.auth_user import AuthenticatedUser

# Repository imports
from app.repositories.user_repository import UserRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.major_repository import MajorRepository
from app.repositories.teacher_repository import TeacherRepository

# Model imports
from app.models.role import Role


class AuthService:
    """
    Authentication service using custom JWT-based authentication.
    
    Handles user registration, login, and session management with:
    - Passwords stored in user_profiles.hashed_password
    - JWT tokens for session management
    - Role-based access control via roles table
    
    Updated to use SQLAlchemy AsyncSession and repositories.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with SQLAlchemy AsyncSession.
        
        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.jwt_manager = get_jwt_manager()
        
        # Initialize repositories
        self.user_repo = UserRepository(db)
        self.school_repo = SchoolRepository(db)
        self.major_repo = MajorRepository(db)
        self.teacher_repo = TeacherRepository(db)

    async def _resolve_or_create_school(self, school_id: Optional[int], school_name: Optional[str]) -> Optional[int]:
        """
        Returns school_id - either the provided one or creates/finds school from name.
        Uses case-insensitive matching to avoid duplicates.
        """
        if school_id is not None:
            # Validate school exists
            school = await self.school_repo.get_by_id(school_id)
            if not school:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"School with id {school_id} does not exist."
                )
            return school_id
        
        if school_name is not None:
            sanitized_name = sanitize_name(school_name)
            if not sanitized_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="School name cannot be empty."
                )
            
            # Use repository method which handles resolve_or_create
            result_id, _ = await self.school_repo.resolve_or_create(sanitized_name)
            return result_id
        
        return None

    async def _resolve_or_create_major(self, major_id: Optional[int], major_name: Optional[str]) -> Optional[int]:
        """
        Returns major_id - either the provided one or creates/finds major from name.
        Uses case-insensitive matching to avoid duplicates.
        """
        if major_id is not None:
            # Validate major exists
            major = await self.major_repo.get_by_id(major_id)
            if not major:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Major with id {major_id} does not exist."
                )
            return major_id
        
        if major_name is not None:
            sanitized_name = sanitize_name(major_name)
            if not sanitized_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Major name cannot be empty."
                )
            
            # Use repository method which handles resolve_or_create
            result_id, _ = await self.major_repo.resolve_or_create(sanitized_name)
            return result_id
        
        return None

    async def _prepare_teacher_metadata(self, teacher_data: Optional[TeacherRegistrationData]) -> dict:
        """
        Prepare metadata for teacher registration.
        Resolves or creates school if provided.
        """
        if teacher_data is None:
            return {}
        
        school_id = await self._resolve_or_create_school(teacher_data.school_id, teacher_data.school_name)
        
        if school_id is not None:
            return {"school_id": school_id}
        return {}

    async def _check_email_exists(self, email: str) -> bool:
        """Check if email already exists in user_profiles."""
        user = await self.user_repo.get_by_email(email)
        return user is not None

    async def _get_role_info(self, role_id: int) -> Dict[str, Any]:
        """Get role information by ID."""
        from sqlalchemy import select
        
        result = await self.db.execute(
            select(Role).where(Role.id == role_id)
        )
        role = result.scalar_one_or_none()
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with id {role_id} does not exist."
            )
        return {"id": role.id, "role_name": role.role_name}

    async def register_user(self, register_data: RegisterRequest) -> Dict[str, Any]:
        """
        Register a new user.
        
        Creates:
        - user_profiles record with hashed password
        - teachers record if role is teacher
        
        Note: Student registration is not allowed through this endpoint.
        """
        try:
            # Validate that role exists and get role_name
            role_info = await self._get_role_info(register_data.role_id)
            role_name = role_info.get("role_name")
            
            # Block student registration
            if role_name == "student":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student registration is not allowed through this endpoint."
                )
            
            # Check if email already exists
            if await self._check_email_exists(register_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists."
                )
            
            # Generate user ID
            user_id = uuid.uuid4()
            
            # Hash the password
            hashed_password = hash_password(register_data.password)
            
            # Create user profile using repository
            user_profile = await self.user_repo.create_user(
                id=user_id,
                email=register_data.email,
                full_name=register_data.full_name,
                hashed_password=hashed_password,
                role_id=register_data.role_id,
            )
            
            # Handle role-specific registration
            if role_name == "teacher":
                teacher_metadata = await self._prepare_teacher_metadata(register_data.teacher_data)
                school_id = teacher_metadata.get("school_id")
                
                await self.teacher_repo.create(
                    user_id=user_id,
                    school_id=school_id
                )
            
            # Generate tokens
            token_pair = self.jwt_manager.create_token_pair(
                user_id=str(user_id),
                email=register_data.email,
                role_id=register_data.role_id,
                role_name=role_name
            )
            
            # Build response mimicking the old format
            return {
                "user": AuthenticatedUser(
                    id=user_id,
                    email=register_data.email,
                    full_name=register_data.full_name,
                    role_id=register_data.role_id,
                    role_name=role_name,
                    created_at=user_profile.created_at.isoformat() if user_profile.created_at else None
                ),
                "session": {
                    "access_token": token_pair.access_token,
                    "refresh_token": token_pair.refresh_token,
                    "token_type": token_pair.token_type,
                    "expires_in": token_pair.expires_in
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            error_message = str(e)
            if "duplicate" in error_message.lower() and "email" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration error: {error_message}"
            )

    async def authenticate_user(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        Authenticate user with email and password.
        
        Returns tokens and user information on success.
        """
        try:
            # Get user profile with role info using repository
            user_profile = await self.user_repo.get_by_email_with_role(login_data.email)
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            hashed_password = user_profile.hashed_password
            
            if not hashed_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            # Verify password
            if not verify_password(login_data.password, hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
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
                detail=f"Authentication failed: {str(e)}"
            )
    
    async def sign_out(self) -> Dict[str, str]:
        """
        Sign out the current user.
        
        With JWT-based auth, sign out is handled client-side by discarding tokens.
        This endpoint can be used to invalidate tokens server-side if needed
        (requires token blacklist implementation).
        """
        # For now, sign out is a no-op on the server side
        # The client should discard their tokens
        # TODO: Implement token blacklist for true server-side invalidation
        return {"message": "Successfully signed out"}

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh the session using a refresh token.
        Returns a new access token and refresh token.
        """
        try:
            # Verify the refresh token
            payload = self.jwt_manager.verify_refresh_token(refresh_token)
            
            # Get current user profile to ensure user still exists and get latest role
            user_profile = await self.user_repo.get_with_role(UUID(payload.sub))
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            role_name = user_profile.role.role_name if user_profile.role else None
            
            # Generate new token pair
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
            
        except JWTExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except JWTInvalidError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not refresh session"
            )
