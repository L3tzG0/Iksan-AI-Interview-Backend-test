from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import Token, LoginRequest, RegisterRequest, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_in: RegisterRequest,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Register a new user with Supabase Auth.
    """
    auth_service = AuthService(supabase)
    result = await auth_service.register_user(user_in)
    
    return UserResponse(
        id=result["user"].id,
        email=result["user"].email,
        full_name=result["user"].user_metadata.get("full_name"),
        role_id=result["user"].user_metadata.get("role_id"),
        created_at=result["user"].created_at
    )

@router.post("/login", response_model=Token)
async def login_for_access_token(
    login_data: LoginRequest,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Login with email and password to get access token.
    Uses Supabase Auth for authentication.
    """
    auth_service = AuthService(supabase)
    result = await auth_service.authenticate_user(login_data)
    
    return Token(
        access_token=result["access_token"],
        token_type="bearer",
        refresh_token=result["refresh_token"]
    )

@router.post("/logout")
async def logout(
    supabase: Annotated[Client, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Sign out the current user.
    """
    auth_service = AuthService(supabase)
    return await auth_service.sign_out()

@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user = Depends(get_current_user)
):
    """
    Get current authenticated user information.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.user_metadata.get("full_name"),
        role_id=current_user.user_metadata.get("role_id"),
        created_at=current_user.created_at
    )
