from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from supabase import AsyncClient
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter, get_ip_address
from app.services.auth_service import AuthService
from app.services.user_service import UserProfileService
from app.schemas.auth import Token, LoginRequest, RegisterRequest, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH, key_func=get_ip_address)
async def register_user(
    request: Request,
    user_in: RegisterRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Register a new user with Supabase Auth.
    A user profile will be automatically created via database trigger.
    
    Note: Student registration is not allowed through this endpoint.
    Only teachers (role_id: 2) and admins (role_id: 1) can register.
    
    Rate limited: 5 requests per minute per IP address.
    """
    auth_service = AuthService(supabase)
    result = await auth_service.register_user(user_in)
    
    user_response = UserResponse(
        id=result["user"].id,
        email=result["user"].email,
        full_name=result["user"].user_metadata.get("full_name"),
        role_id=result["user"].user_metadata.get("role_id"),
        created_at=result["user"].created_at
    )

    return JSONResponse(content=jsonable_encoder(user_response.dict(exclude_none=True)))

@router.post("/login", response_model=Token)
@limiter.limit(settings.RATE_LIMIT_AUTH, key_func=get_ip_address)
async def login_for_access_token(
    request: Request,
    login_data: LoginRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Login with email and password to get access token.
    Uses Supabase Auth for authentication.
    Returns token along with user profile data (same as /auth/me).
    
    Rate limited: 5 requests per minute per IP address.
    """
    auth_service = AuthService(supabase)
    result = await auth_service.authenticate_user(login_data)
    
    # Get user context (same as /auth/me)
    profile_service = UserProfileService(supabase)
    user = result["user"]
    
    try:
        user_context = await profile_service.get_full_user_context(user.id)
        profile = user_context["profile"]
        student_details = user_context["student_details"]
        teacher_details = user_context["teacher_details"]
        
        # Extract role information
        role_name = None
        roles_data = profile.get("roles") if isinstance(profile, dict) else None
        if roles_data and isinstance(roles_data, dict):
            role_name = roles_data.get("role_name")
        
        full_name = profile.get("full_name") if isinstance(profile, dict) else None
        full_name_str = str(full_name) if full_name is not None else None
        
        role_id = profile.get("role_id") if isinstance(profile, dict) else None
        role_id_int = int(role_id) if role_id is not None and isinstance(role_id, (int, float, str)) else None
        role_name_str = str(role_name) if role_name is not None else None
        
        student_dict = dict(student_details) if student_details and isinstance(student_details, dict) else None
        teacher_dict = dict(teacher_details) if teacher_details and isinstance(teacher_details, dict) else None
        
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=full_name_str,
            role_id=role_id_int,
            role_name=role_name_str,
            student_details=student_dict,
            teacher_details=teacher_dict,
            created_at=user.created_at
        )
    except HTTPException:
        # Fallback to user_metadata if profile not found
        user_response = UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.user_metadata.get("full_name"),
            role_id=user.user_metadata.get("role_id"),
            created_at=user.created_at
        )
    
    token_response = Token(
        access_token=result["access_token"],
        token_type="bearer",
        refresh_token=result["refresh_token"],
        user=user_response
    )

    return JSONResponse(content=jsonable_encoder(token_response.dict(exclude_none=True)))

@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def logout(
    request: Request,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Sign out the current user.
    """
    auth_service = AuthService(supabase)
    sign_out_payload = await auth_service.sign_out()
    return JSONResponse(content=sign_out_payload)

@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def read_users_me(
    request: Request,
    current_user = Depends(get_current_user),
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Get current authenticated user information.
    Returns combined data from auth.users, public.user_profiles, and role information.
    If user is a student, includes student details (school, major, class).
    If user is a teacher, includes teacher details.
    
    Optimized to minimize database queries using relational selects.
    """
    profile_service = UserProfileService(supabase)
    
    try:
        # Get complete user context in optimized queries (avoids N+1)
        user_context = await profile_service.get_full_user_context(current_user.id)
        
        profile = user_context["profile"]
        student_details = user_context["student_details"]
        teacher_details = user_context["teacher_details"]
        
        # Extract role information from the relational query result
        role_name = None
        roles_data = profile.get("roles") if isinstance(profile, dict) else None
        if roles_data and isinstance(roles_data, dict):
            role_name = roles_data.get("role_name")
        
        # Extract and cast values properly
        full_name = profile.get("full_name") if isinstance(profile, dict) else None
        full_name_str = str(full_name) if full_name is not None else None
        
        role_id = profile.get("role_id") if isinstance(profile, dict) else None
        role_id_int = int(role_id) if role_id is not None and isinstance(role_id, (int, float, str)) else None
        role_name_str = str(role_name) if role_name is not None else None
        
        # Cast details to dict if they exist
        student_dict = dict(student_details) if student_details and isinstance(student_details, dict) else None
        teacher_dict = dict(teacher_details) if teacher_details and isinstance(teacher_details, dict) else None
        
        user_response = UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=full_name_str,
            role_id=role_id_int,
            role_name=role_name_str,
            student_details=student_dict,
            teacher_details=teacher_dict,
            created_at=current_user.created_at
        )

        return JSONResponse(content=jsonable_encoder(user_response.dict(exclude_none=True)))
    except HTTPException:
        # Fallback to user_metadata if profile not found
        user_response = UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.user_metadata.get("full_name"),
            role_id=current_user.user_metadata.get("role_id"),
            created_at=current_user.created_at
        )

        return JSONResponse(content=jsonable_encoder(user_response.dict(exclude_none=True)))
