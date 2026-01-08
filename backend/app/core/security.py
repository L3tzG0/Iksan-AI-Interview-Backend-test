"""
Security utilities for custom JWT-based authentication.

This module provides FastAPI integration helpers for our custom auth system
that uses locally-managed JWTs and the user_profiles table for user data.

All functions are async to maintain consistency with the rest of the application
and to support async database queries when enriching user data.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.jwt import get_jwt_manager, JWTExpiredError, JWTInvalidError, TokenType
from app.core.auth_user import AuthenticatedUser
from app.models.user_profile import UserProfile
from app.models.role import Role
from uuid import UUID

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
    Validate JWT token and get current user.
    
    This validates our custom JWT tokens and returns an AuthenticatedUser
    object with user information from the token claims.
    
    For enriched data (full profile, etc.), the user_profiles table is queried
    using SQLAlchemy.
    """
    try:
        jwt_manager = get_jwt_manager()
        
        # Verify the access token
        payload = jwt_manager.verify_access_token(credentials.credentials)
        
        # Fetch full profile from database for up-to-date role info
        # This ensures role changes take effect immediately
        stmt = (
            select(UserProfile)
            .options(selectinload(UserProfile.role))
            .where(UserProfile.id == UUID(payload.sub))
        )
        result = await db.execute(stmt)
        profile = result.scalar_one_or_none()
        
        if profile:
            role_name = profile.role.role_name if profile.role else None
            
            return AuthenticatedUser(
                id=profile.id,
                email=profile.email,
                full_name=profile.full_name,
                role_id=profile.role_id,
                role_name=role_name,
                email_verified=True,
                created_at=profile.created_at.isoformat() if profile.created_at else None,
                updated_at=profile.updated_at.isoformat() if profile.updated_at else None
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

