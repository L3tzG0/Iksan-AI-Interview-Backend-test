from typing import Optional, Any, Dict, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from app.schemas.types import FlexibleDateTime
import re


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


class StudentRegistrationData(BaseModel):
    """Registration data specific to students"""
    student_id: str  # Required - the student's ID number
    # School: either ID or name (mutually exclusive)
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    # Major: either ID or name
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    # Class: either ID or (name + grade_level)
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    grade_level: Optional[str] = None

    @model_validator(mode='after')
    def validate_school_input(self):
        """Ensure either school_id or school_name is provided, not both"""
        if self.school_id is None and self.school_name is None:
            raise ValueError('Either school_id or school_name must be provided')
        if self.school_id is not None and self.school_name is not None:
            raise ValueError('Provide either school_id or school_name, not both')
        return self

    @model_validator(mode='after')
    def validate_major_input(self):
        """Ensure either major_id or major_name is provided, not both"""
        if self.major_id is None and self.major_name is None:
            raise ValueError('Either major_id or major_name must be provided')
        if self.major_id is not None and self.major_name is not None:
            raise ValueError('Provide either major_id or major_name, not both')
        return self

    @model_validator(mode='after')
    def validate_class_input(self):
        """Ensure either class_id or (class_name + grade_level) is provided"""
        has_class_id = self.class_id is not None
        has_class_name = self.class_name is not None
        has_grade_level = self.grade_level is not None
        
        if has_class_id and (has_class_name or has_grade_level):
            raise ValueError('Provide either class_id or (class_name + grade_level), not both')
        if not has_class_id and not has_class_name:
            raise ValueError('Either class_id or class_name must be provided')
        if has_class_name and not has_grade_level:
            raise ValueError('grade_level is required when providing class_name')
        return self


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
    student_data: Optional[StudentRegistrationData] = None
    teacher_data: Optional[TeacherRegistrationData] = None

