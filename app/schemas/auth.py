from typing import Optional, Any, Dict, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
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
    """Login request for email-based authentication (teachers/admins)"""
    email: EmailStr
    password: str


class StudentLoginRequest(BaseModel):
    """
    Login request for student authentication.
    Students use their generated student_id instead of email.
    """
    student_id: str = Field(..., min_length=12, max_length=12, description="12-digit student ID")
    password: str = Field(..., min_length=1)

    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v: str) -> str:
        """Validate student ID is 12 digits"""
        if not v.isdigit():
            raise ValueError('Student ID must contain only digits')
        return v


class StudentLoginResponse(BaseModel):
    """Response for successful student login"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user_id: str
    student_id: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    school_name: Optional[str] = None
    major_name: Optional[str] = None
    class_name: Optional[str] = None
    interview_session_quota: Optional[int] = None
    grade_level: Optional[int] = None


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

class RefreshRequest(BaseModel):
    refresh_token: str