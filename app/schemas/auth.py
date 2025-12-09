from typing import Optional, Any, Dict, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.schemas.types import FlexibleDateTime


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    student_details: Optional[Dict[str, Any]] = None
    teacher_details: Optional[Dict[str, Any]] = None
    created_at: FlexibleDateTime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    user: Optional[UserResponse] = None

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TeacherRegistrationData(BaseModel):
    """Registration data specific to teachers"""
    # School: either ID or name (optional for teachers)
    school_id: Optional[int] = None
    school_name: Optional[str] = None

    @model_validator(mode='after')
    def validate_school_input(self):
        """If school is provided, ensure only one method is used"""
        if self.school_id is not None and self.school_name is not None:
            raise ValueError('Provide either school_id or school_name, not both')
        return self


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role_id: int
    # Role-specific nested data
    teacher_data: Optional[TeacherRegistrationData] = None

