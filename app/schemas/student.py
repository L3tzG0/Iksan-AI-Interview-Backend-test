
from typing import Optional
from pydantic import BaseModel, model_validator
from uuid import UUID

from app.schemas.types import GradeLevel


class StudentBase(BaseModel):
    user_id: UUID
    student_id: str  # Student ID number (e.g., school-issued ID)

class StudentAccountCreate(BaseModel):
    full_name: str
    school_id: Optional[int] = None
    school_name: Optional[str] = None
    major_id: Optional[int] = None
    major_name: Optional[str] = None
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    grade_level: Optional[GradeLevel] = None

    @model_validator(mode='after')
    def validate_required_fields(self):
        """Validate that required field combinations exist"""
        # Validate school: either school_id or school_name must be provided
        if self.school_id is None and self.school_name is None:
            raise ValueError('Either school_id or school_name must be provided')
        if self.school_id is not None and self.school_name is not None:
            raise ValueError('Provide either school_id or school_name, not both')
        
        # Validate major: either major_id or major_name must be provided
        if self.major_id is None and self.major_name is None:
            raise ValueError('Either major_id or major_name must be provided')
        if self.major_id is not None and self.major_name is not None:
            raise ValueError('Provide either major_id or major_name, not both')
        
        # Validate class: either class_id OR (class_name + grade_level) must be provided
        has_class_id = self.class_id is not None
        has_class_name_and_grade = self.class_name is not None and self.grade_level is not None
        
        if not has_class_id and not has_class_name_and_grade:
            raise ValueError('Either class_id or both class_name and grade_level must be provided')
        if has_class_id and (self.class_name is not None or self.grade_level is not None):
            raise ValueError('Provide either class_id or class_name with grade_level, not both')
        
        return self

class StudentAccountResponse(BaseModel):
    id: int
    user_id: UUID
    full_name: str
    student_id: str
    current_class_id: int
    password: str

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    id: int
    user_id: UUID
    student_id: str
    school_id: int
    major_id: int
    current_class_id: int

    class Config:
        from_attributes = True
