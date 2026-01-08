"""
FastAPI dependencies for the API using SQLAlchemy and custom auth.

All dependency functions that interact with the database are async because
SQLAlchemy async sessions use async database calls. This ensures proper
connection handling under concurrent load.
"""
from dataclasses import dataclass
from typing import Annotated, Union, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.auth_user import AuthenticatedUser
from app.repositories.user_repository import UserRepository


@dataclass
class RoleContext:
    """Auth context enriched with role information."""
    user: AuthenticatedUser
    profile: Optional[dict]
    role_id: Optional[int]
    role_name: Optional[str]


def require_role(role_names: Union[str, List[str]]):
    """
    Dependency to check if user has required role(s).
    
    Args:
        role_names: A single role name (str) or list of allowed role names (List[str])
    
    Usage: 
        # Single role
        current_user = Depends(require_role("teacher"))
        
        # Multiple allowed roles
        current_user = Depends(require_role(["teacher", "admin"]))
    
    Raises:
        HTTPException 403: If user doesn't have the required role
        HTTPException 404: If user profile not found
    """
    # Normalize role_names to always be a list
    allowed_roles = [role_names] if isinstance(role_names, str) else role_names
    
    async def role_checker(
        db: Annotated[AsyncSession, Depends(get_db)],
        current_user: AuthenticatedUser = Depends(get_current_user)
    ) -> RoleContext:
        try:
            # Get user profile with role information using SQLAlchemy repository
            user_repo = UserRepository(db)
            user_profile = await user_repo.get_with_role(current_user.id)
            
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            # Extract role metadata from SQLAlchemy model
            user_role_name: Optional[str] = None
            user_role_id: Optional[int] = None
            
            if user_profile.role:
                user_role_name = user_profile.role.role_name
                user_role_id = user_profile.role.id
            else:
                user_role_id = user_profile.role_id
            
            # Check if user's role is in the list of allowed roles
            if not user_role_name or user_role_name not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Required role(s): {', '.join(allowed_roles)}"
                )
            
            # Convert SQLAlchemy model to dict for backward compatibility
            profile_dict = {
                "id": str(user_profile.id),
                "email": user_profile.email,
                "full_name": user_profile.full_name,
                "role_id": user_profile.role_id,
                "created_at": user_profile.created_at.isoformat() if user_profile.created_at else None,
                "updated_at": user_profile.updated_at.isoformat() if user_profile.updated_at else None,
                "roles": {
                    "id": user_profile.role.id,
                    "role_name": user_profile.role.role_name,
                } if user_profile.role else None,
            }
            
            return RoleContext(
                user=current_user,
                profile=profile_dict,
                role_id=user_role_id,
                role_name=user_role_name
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error checking user role: {str(e)}"
            )
    
    return role_checker
