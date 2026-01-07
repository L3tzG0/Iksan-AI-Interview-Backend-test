"""
Security utilities for custom JWT-based authentication.

This module provides FastAPI integration helpers for our custom auth system
that uses locally-managed JWTs and the user_profiles table for user data.

All functions are async to maintain consistency with the rest of the application
and to support async database queries when enriching user data.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import AsyncClient

from app.core.database import get_supabase
from app.core.jwt import get_jwt_manager, JWTExpiredError, JWTInvalidError, TokenType
from app.core.auth_user import AuthenticatedUser
from uuid import UUID

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: AsyncClient = Depends(get_supabase)
) -> AuthenticatedUser:
    """
    Validate JWT token and get current user.
    
    This validates our custom JWT tokens and returns an AuthenticatedUser
    object with user information from the token claims.
    
    For enriched data (full profile, etc.), the user_profiles table is queried.
    """
    try:
        jwt_manager = get_jwt_manager()
        
        # Verify the access token
        payload = jwt_manager.verify_access_token(credentials.credentials)
        
        # Optionally fetch full profile from database for up-to-date role info
        # This ensures role changes take effect immediately
        response = await supabase.table('user_profiles').select(
            'id, email, full_name, role_id, created_at, updated_at, roles(id, role_name)'
        ).eq('id', payload.sub).execute()
        
        if response.data:
            profile = response.data[0]
            role_data = profile.get('roles', {}) or {}
            
            return AuthenticatedUser(
                id=UUID(profile['id']),
                email=profile.get('email', payload.email),
                full_name=profile.get('full_name'),
                role_id=profile.get('role_id'),
                role_name=role_data.get('role_name') if isinstance(role_data, dict) else None,
                email_verified=True,
                created_at=profile.get('created_at'),
                updated_at=profile.get('updated_at')
            )
        
        # Fallback to token claims if profile not found
        # This can happen if DB is temporarily unavailable
        return AuthenticatedUser(
            id=UUID(payload.sub),
            email=payload.email,
            role_id=payload.role_id,
            role_name=payload.role_name,
            email_verified=True
        )
        
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_from_token_only(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """
    Validate JWT token and get user from token claims only (no DB lookup).
    
    Use this for endpoints that don't need the latest profile data
    and want to minimize database calls.
    """
    try:
        jwt_manager = get_jwt_manager()
        payload = jwt_manager.verify_access_token(credentials.credentials)
        
        return AuthenticatedUser(
            id=UUID(payload.sub),
            email=payload.email,
            role_id=payload.role_id,
            role_name=payload.role_name,
            email_verified=True
        )
        
    except JWTExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

