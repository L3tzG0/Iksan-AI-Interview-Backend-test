
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from app.schemas.user import UserProfileResponse
from app.schemas.school import SchoolResponse
from app.schemas.major import MajorResponse
from app.schemas.class_schema import ClassResponse


class StudentBase(BaseModel):
    user_id: UUID


class StudentCreate(StudentBase):
    school_id: int
    major_id: int
    current_class_id: int


class StudentUpdate(BaseModel):
    school_id: Optional[int] = None
    major_id: Optional[int] = None
    current_class_id: Optional[int] = None


class StudentResponse(StudentBase):
    id: int
    school_id: Optional[int] = None
    major_id: Optional[int] = None
    current_class_id: Optional[int] = None

    class Config:
        from_attributes = True

class StudentWithDetails(StudentResponse):
    user_profile: UserProfileResponse
    school: SchoolResponse
    major: MajorResponse
    current_class: ClassResponse
