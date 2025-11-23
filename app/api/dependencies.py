"""
FastAPI dependencies for the API using Supabase client and auth.
"""
from typing import Annotated, Union, List, Any, Optional
from fastapi import Depends, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.security import get_current_user

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
        current_user = Depends(get_current_user),
        supabase: Annotated[Client, Depends(get_supabase)] = Depends(get_supabase)
    ):
        try:
            # Get user profile with role information from database
            response = supabase.table('user_profiles').select(
                '*, roles(id, role_name)'
            ).eq('id', str(current_user.id)).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            
            user_profile: Optional[Any] = response.data[0]
            role_data: Optional[Any] = user_profile.get('roles') if isinstance(user_profile, dict) else None
            
            # Extract role_name from nested roles object
            user_role_name: Optional[str] = None
            if isinstance(role_data, dict):
                user_role_name = role_data.get('role_name')
            
            # Check if user's role is in the list of allowed roles
            if not user_role_name or user_role_name not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Required role(s): {', '.join(allowed_roles)}"
                )
            
            return current_user
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error checking user role: {str(e)}"
            )
    
    return role_checker
