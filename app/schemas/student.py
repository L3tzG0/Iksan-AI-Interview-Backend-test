from typing import Optional, List
from pydantic import BaseModel, Field, model_validator
from uuid import UUID

from app.schemas.types import GradeLevel


class StudentBase(BaseModel):
    user_id: UUID
    student_id: str  # Student ID number (e.g., school-issued ID)


class StudentAccountCreate(BaseModel):
    """
    Schema for creating a single student account.
    
    Required fields:
    - full_name: Student's full name
    - major_name: Name of the major (will be created if not exists)
    
    School (one of):
    - school_name: Name of the school (required for admins, optional for teachers)
    
    Class (one of):
    - class_id: ID of existing class, OR
    - class_name + grade_level: Creates new class or finds existing match
    """
    full_name: str = Field(..., min_length=1, max_length=255)
    school_name: Optional[str] = Field(None, max_length=255)
    major_name: Optional[str] = Field(None, max_length=255)
    class_id: Optional[int] = None
    class_name: Optional[str] = Field(None, max_length=255)
    grade_level: Optional[GradeLevel] = None

    @model_validator(mode='after')
    def validate_required_fields(self):
        """Validate that required field combinations exist"""
        # Note: school_name validation is relaxed - teachers can omit it
        # and their school will be used automatically
        
        # Validate major: major_name must be provided
        if self.major_name is None:
            raise ValueError('major_name must be provided')
        
        # Validate class: either class_id OR (class_name + grade_level) must be provided
        has_class_id = self.class_id is not None
        has_class_name_and_grade = self.class_name is not None and self.grade_level is not None
        
        if not has_class_id and not has_class_name_and_grade:
            raise ValueError('Either class_id or both class_name and grade_level must be provided')
        if has_class_id and (self.class_name is not None or self.grade_level is not None):
            raise ValueError('Provide either class_id or class_name with grade_level, not both')
        
        return self


class StudentAccountResponse(BaseModel):
    """
    Response schema for a created student account.
    Includes the generated login credentials.
    """
    id: int
    user_id: UUID
    full_name: str
    student_id: str  # Generated login ID (12 digits)
    current_class_id: int
    password: str  # Generated password (shown once)

    class Config:
        from_attributes = True


class StudentBulkCreateRequest(BaseModel):
    """
    Request schema for bulk student account creation.
    """
    students: List[StudentAccountCreate] = Field(..., min_length=1, max_length=100)


class StudentBulkCreateResponse(BaseModel):
    """
    Response schema for bulk student account creation.
    """
    created_count: int
    students: List[StudentAccountResponse]


class StudentResponse(BaseModel):
    """
    Basic student response schema (without password).
    """
    id: int
    user_id: UUID
    student_id: str
    school_id: int
    major_id: int
    current_class_id: int

    class Config:
        from_attributes = True


class StudentDetailResponse(BaseModel):
    """
    Detailed student response with related data.
    """
    id: int
    user_id: UUID
    student_id: str
    full_name: str
    school_id: int
    school_name: Optional[str] = None
    major_id: int
    major_name: Optional[str] = None
    current_class_id: int
    class_name: Optional[str] = None
    grade_level: Optional[int] = None

    class Config:
        from_attributes = True
