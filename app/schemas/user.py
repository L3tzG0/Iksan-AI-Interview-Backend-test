from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.schemas.role import RoleResponse
from app.schemas.types import FlexibleDateTime

class UserProfileBase(BaseModel):
    email: EmailStr
    full_name: str
    role_id: int

class UserProfileCreate(UserProfileBase):
    """
    Schema for creating user profile.
    Note: Password is NOT included here as it's handled by Supabase Auth.
    The profile is auto-created via database trigger.
    """
    pass

class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role_id: Optional[int] = None

class UserProfileResponse(UserProfileBase):
    id: UUID
    created_at: FlexibleDateTime
    updated_at: FlexibleDateTime

    class Config:
        from_attributes = True

class UserProfileWithRole(UserProfileResponse):
    role: RoleResponse
