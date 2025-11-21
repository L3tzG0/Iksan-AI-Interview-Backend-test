"""
FastAPI dependencies for the API.
Now using Supabase client and auth instead of SQLAlchemy sessions.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.security import get_current_user

def require_role(role_name: str):
    """
    Dependency to check if user has required role.
    Usage: current_user = Depends(require_role("teacher"))
    """
    def role_checker(current_user = Depends(get_current_user)):
        user_role = current_user.user_metadata.get("role_id")
        # You'll need to map role_id to role names or store role_name in metadata
        # For now, this is a placeholder implementation
        if user_role != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return role_checker
