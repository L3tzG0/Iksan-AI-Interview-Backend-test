from supabase import Client
from fastapi import HTTPException, status
from app.schemas.auth import LoginRequest, RegisterRequest

class AuthService:
    """
    Authentication service using Supabase Auth.
    Handles user registration, login, and session management.
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def register_user(self, register_data: RegisterRequest):
        """
        Register a new user with Supabase Auth.
        Validates that the role_id exists before registration.
        """
        try:
            # Validate that role exists
            role_response = self.supabase.table("roles").select("id").eq("id", register_data.role_id).execute()
            
            if not role_response.data or len(role_response.data) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Role with id {register_data.role_id} does not exist. Please ensure roles are seeded in the database."
                )
            
            # Sign up user with Supabase Auth
            response = self.supabase.auth.sign_up({
                "email": register_data.email,
                "password": register_data.password,
                "options": {
                    "data": {
                        "full_name": register_data.full_name,
                        "role_id": register_data.role_id
                    }
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
                    detail=f"Invalid role_id. Please ensure roles are seeded in the database."
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
            response = self.supabase.auth.sign_in_with_password({
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
            self.supabase.auth.sign_out()
            return {"message": "Successfully signed out"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sign out failed: {str(e)}"
            )
