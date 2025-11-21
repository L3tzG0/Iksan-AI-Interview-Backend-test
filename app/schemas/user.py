from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.schemas.role import RoleResponse

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role_id: int

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserWithRole(UserResponse):
    role: RoleResponse
