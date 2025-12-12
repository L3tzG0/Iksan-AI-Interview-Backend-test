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
from app.services.student_registration_service import StudentRegistrationService
from app.schemas.auth import Token, LoginRequest, RegisterRequest, UserResponse, StudentLoginRequest, StudentLoginResponse

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
        user_response = profile_service.build_user_response(
            user=user,
            profile=profile,
            student_details=student_details,
            teacher_details=teacher_details,
        )
    except HTTPException:
        # Fallback to user_metadata if profile not found
        user_response = profile_service.build_user_response(user=user)
    
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
        user_response = profile_service.build_user_response(
            user=current_user,
            profile=profile,
            student_details=student_details,
            teacher_details=teacher_details,
        )

        return JSONResponse(content=jsonable_encoder(user_response.dict(exclude_none=True)))
    except HTTPException:
        # Fallback to user_metadata if profile not found
        user_response = profile_service.build_user_response(user=current_user)

        return JSONResponse(content=jsonable_encoder(user_response.dict(exclude_none=True)))


@router.post("/student-login", response_model=StudentLoginResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH, key_func=get_ip_address)
async def student_login(
    request: Request,
    login_data: StudentLoginRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Login with student ID and password (username-based login for students).
    
    Students use their auto-generated student ID (12 digits) and password
    instead of email-based login.
    
    This uses a fake email pattern internally to work with Supabase Auth:
    {student_id}@students.internal
    
    Parameters:
    - student_id: The 12-digit student ID
    - password: The student's password
    
    Returns: Access token, refresh token, and student user information
    
    Rate limited: 5 requests per minute per IP address.
    """
    registration_service = StudentRegistrationService(supabase)
    
    try:
        result = await registration_service.authenticate_student(
            login_data.student_id,
            login_data.password
        )
        
        # Get student details from the database via service helper
        student = await registration_service.get_student_context_by_student_id(login_data.student_id)
        user_profile = student.get("user_profiles") if student else None
        school_info = student.get("schools") if student else None
        major_info = student.get("majors") if student else None
        class_info = student.get("classes") if student else None
        
        student_login_response = StudentLoginResponse(
            access_token=result["access_token"],
            token_type="bearer",
            refresh_token=result["refresh_token"],
            user_id=result["user"].id,
            student_id=login_data.student_id,
            full_name=user_profile.get("full_name") if user_profile else None,
            school_name=school_info.get("school_name") if school_info else None,
            major_name=major_info.get("major_name") if major_info else None,
            class_name=class_info.get("class_name") if class_info else None,
            grade_level=class_info.get("grade_level") if class_info else None
        )
        
        return JSONResponse(content=jsonable_encoder(student_login_response.dict(exclude_none=True)))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )
