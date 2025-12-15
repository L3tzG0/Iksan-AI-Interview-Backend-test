from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.schemas.role import RoleResponse
from app.schemas.types import FlexibleDateTime, RoleName

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

class UserProfileResponse(UserProfileBase):
    id: UUID
    created_at: FlexibleDateTime
    updated_at: FlexibleDateTime

    class Config:
        from_attributes = True

class UserProfileWithRole(UserProfileResponse):
    role: RoleResponse


class UserListItemResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: RoleName
    created_at: FlexibleDateTime
    updated_at: FlexibleDateTime
    student_id: Optional[str] = None
    password: Optional[str] = None

    class Config:
        from_attributes = True
