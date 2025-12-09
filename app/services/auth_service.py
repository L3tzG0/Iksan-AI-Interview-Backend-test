import re
from typing import Optional
from supabase import AsyncClient
from fastapi import HTTPException, status
from app.schemas.auth import LoginRequest, RegisterRequest, TeacherRegistrationData


class AuthService:
    """
    Authentication service using Supabase Auth.
    Handles user registration, login, and session management.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    def _sanitize_name(self, name: str) -> str:
        """
        Sanitize user-typed names:
        - Strip leading/trailing whitespace
        - Normalize multiple spaces to single space
        - Remove null bytes and control characters
        """
        if not name:
            return name
        # Remove null bytes and control characters
        name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
        # Normalize whitespace
        name = ' '.join(name.split())
        return name.strip()

    async def _resolve_or_create_school(self, school_id: Optional[int], school_name: Optional[str]) -> Optional[int]:
        """
        Returns school_id - either the provided one or creates/finds school from name.
        Uses case-insensitive matching to avoid duplicates.
        """
        if school_id is not None:
            # Validate school exists
            response = await self.supabase.table("schools").select("id").eq("id", school_id).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"School with id {school_id} does not exist."
                )
            return school_id
        
        if school_name is not None:
            sanitized_name = self._sanitize_name(school_name)
            if not sanitized_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="School name cannot be empty."
                )
            
            # Try to find existing school (case-insensitive)
            response = await self.supabase.table("schools").select("id, school_name").ilike("school_name", sanitized_name).execute()
            if response.data:
                return response.data[0]["id"]
            
            # Create new school
            response = await self.supabase.table("schools").insert({"school_name": sanitized_name}).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create school."
                )
            return response.data[0]["id"]
        
        return None

    async def _resolve_or_create_major(self, major_id: Optional[int], major_name: Optional[str]) -> Optional[int]:
        """
        Returns major_id - either the provided one or creates/finds major from name.
        Uses case-insensitive matching to avoid duplicates.
        """
        if major_id is not None:
            # Validate major exists
            response = await self.supabase.table("majors").select("id").eq("id", major_id).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Major with id {major_id} does not exist."
                )
            return major_id
        
        if major_name is not None:
            sanitized_name = self._sanitize_name(major_name)
            if not sanitized_name:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Major name cannot be empty."
                )
            
            # Try to find existing major (case-insensitive)
            response = await self.supabase.table("majors").select("id, major_name").ilike("major_name", sanitized_name).execute()
            if response.data:
                return response.data[0]["id"]
            
            # Create new major
            response = await self.supabase.table("majors").insert({"major_name": sanitized_name}).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to create major."
                )
            return response.data[0]["id"]
        
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

    async def register_user(self, register_data: RegisterRequest):
        """
        Register a new user with Supabase Auth.
        Handles role-specific registration:
        - Students: registration disabled
        - Teachers: optional school assignment
        - Admins: no additional data
        """
        try:
            # Validate that role exists and get role_name
            role_response = await self.supabase.table("roles").select("id, role_name").eq("id", register_data.role_id).execute()
            
            if not role_response.data or len(role_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with id {register_data.role_id} does not exist. Please ensure roles are seeded in the database."
                )
            
            role_name = role_response.data[0].get("role_name")
            
            # Block student registration
            if role_name == "student":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student registration is not allowed through this endpoint."
                )
            
            # Build base metadata for Supabase Auth
            user_metadata = {
                "full_name": register_data.full_name,
                "role_id": register_data.role_id
            }
            
            # Handle role-specific registration
            if role_name == "teacher":
                teacher_metadata = await self._prepare_teacher_metadata(register_data.teacher_data)
                user_metadata.update(teacher_metadata)
            
            # Admin role doesn't need additional metadata
            
            # Sign up user with Supabase Auth
            response = await self.supabase.auth.sign_up({
                "email": register_data.email,
                "password": register_data.password,
                "options": {
                    "data": user_metadata
                }
            })
            
            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User registration failed"
                )
            
            return {
                "user": response.user,
                "session": response.session
            }
        except HTTPException:
            raise
        except Exception as e:
            error_message = str(e)
            # Check for common database errors
            if "does not exist" in error_message.lower() and "role" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role_id. Please ensure roles are seeded in the database."
                )
            if "duplicate" in error_message.lower() and "student_id" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A student with this student_id already exists."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Registration error: {error_message}"
            )

    async def authenticate_user(self, login_data: LoginRequest):
        """
        Authenticate user with email and password using Supabase Auth.
        """
        try:
            response = await self.supabase.auth.sign_in_with_password({
                "email": login_data.email,
                "password": login_data.password
            })
            
            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password"
                )
            
            return {
                "user": response.user,
                "session": response.session,
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}"
            )
    
    async def sign_out(self):
        """
        Sign out the current user.
        """
        try:
            await self.supabase.auth.sign_out()
            return {"message": "Successfully signed out"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign out failed: {str(e)}"
            )
