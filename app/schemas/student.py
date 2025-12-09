
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.types import GradeLevel
from app.schemas.user import UserProfileResponse
from app.schemas.school import SchoolResponse
from app.schemas.major import MajorResponse
from app.schemas.class_schema import ClassResponse


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

class StudentAccountResponse(BaseModel):
    id: int
    user_id: UUID
    full_name: str
    student_id: str
    current_class_id: int
    password: str

    class Config:
        from_attributes = True


class StudentUpdate(BaseModel):
    student_id: Optional[str] = None
    school_id: Optional[int] = None
    major_id: Optional[int] = None
    current_class_id: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    user_id: UUID
    student_id: str
    school_id: int
    major_id: int
    current_class_id: int

    class Config:
        from_attributes = True


class StudentWithDetails(StudentResponse):
    user_profile: Optional[UserProfileResponse] = None
    school: Optional[SchoolResponse] = None
    major: Optional[MajorResponse] = None
    current_class: Optional[ClassResponse] = None
