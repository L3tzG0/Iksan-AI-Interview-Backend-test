
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.user import UserProfileResponse
from app.schemas.school import SchoolResponse
from app.schemas.major import MajorResponse
from app.schemas.class_schema import ClassResponse


class StudentBase(BaseModel):
    user_id: UUID
    student_id: str  # Student ID number (e.g., school-issued ID)


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
