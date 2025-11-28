"""
Security utilities for Supabase Auth integration.
Supabase handles authentication, token generation, and password hashing.
This module provides FastAPI integration helpers.

All functions are synchronous (def) because the Supabase Python client
uses synchronous HTTP calls internally. FastAPI will automatically
run sync dependencies in a thread pool.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.core.database import get_supabase

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase)
):
    """
    Validate JWT token and get current user from Supabase Auth.
    This replaces the custom JWT validation logic.
    
    Note: This is a sync function because supabase.auth.get_user() is synchronous.
    FastAPI handles running sync dependencies in a thread pool automatically.
    """
    try:
        # Get user from Supabase using the access token
        user_response = supabase.auth.get_user(credentials.credentials)
        
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_response.user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
