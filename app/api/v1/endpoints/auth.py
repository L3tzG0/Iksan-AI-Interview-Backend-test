from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.services.auth_service import AuthService
from app.services.user_service import UserProfileService
from app.schemas.auth import Token, LoginRequest, RegisterRequest, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register_user(
    user_in: RegisterRequest,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Register a new user with Supabase Auth.
    A user profile will be automatically created via database trigger.
    """
    auth_service = AuthService(supabase)
    result = auth_service.register_user(user_in)
    
    return UserResponse(
        id=result["user"].id,
        email=result["user"].email,
        full_name=result["user"].user_metadata.get("full_name"),
        role_id=result["user"].user_metadata.get("role_id"),
        created_at=result["user"].created_at
    )

@router.post("/login", response_model=Token)
def login_for_access_token(
    login_data: LoginRequest,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Login with email and password to get access token.
    Uses Supabase Auth for authentication.
    """
    auth_service = AuthService(supabase)
    result = auth_service.authenticate_user(login_data)
    
    return Token(
        access_token=result["access_token"],
        token_type="bearer",
        refresh_token=result["refresh_token"]
    )

@router.post("/logout")
def logout(
    supabase: Annotated[Client, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Sign out the current user.
    """
    auth_service = AuthService(supabase)
    return auth_service.sign_out()

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Get current authenticated user information.
    Returns combined data from auth.users, public.user_profiles, and role information.
    If user is a student, includes student details (school, major, class).
    If user is a teacher, includes teacher details.
    """
    profile_service = UserProfileService(supabase)
    
    try:
        # Get profile with role information
        profile = profile_service.get_profile_with_role(current_user.id)
        
        # Extract role information
        role_name = None
        roles_data = profile.get("roles") if isinstance(profile, dict) else None
        if roles_data and isinstance(roles_data, dict):
            role_name = roles_data.get("role_name")
        
        # Get student or teacher details based on role_id
        student_details = None
        teacher_details = None
        
        role_id = profile.get("role_id") if isinstance(profile, dict) else None
        
        # Fetch student/teacher details for all users (will return None if not applicable)
        if role_id:
            student_details = profile_service.get_student_details(current_user.id)
            teacher_details = profile_service.get_teacher_details(current_user.id)
        
        # Extract and cast values properly
        full_name = profile.get("full_name") if isinstance(profile, dict) else None
        full_name_str = str(full_name) if full_name is not None else None
        
        role_id_int = int(role_id) if role_id is not None and isinstance(role_id, (int, float, str)) else None
        role_name_str = str(role_name) if role_name is not None else None
        
        # Cast details to dict if they exist
        student_dict = dict(student_details) if student_details and isinstance(student_details, dict) else None
        teacher_dict = dict(teacher_details) if teacher_details and isinstance(teacher_details, dict) else None
        
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=full_name_str,
            role_id=role_id_int,
            role_name=role_name_str,
            student_details=student_dict,
            teacher_details=teacher_dict,
            created_at=current_user.created_at
        )
    except HTTPException:
        # Fallback to user_metadata if profile not found
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.user_metadata.get("full_name"),
            role_id=current_user.user_metadata.get("role_id"),
            created_at=current_user.created_at
        )
