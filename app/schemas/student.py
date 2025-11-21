from typing import Optional
from pydantic import BaseModel
from app.schemas.user import UserResponse
from app.schemas.school import SchoolResponse
from app.schemas.major import MajorResponse
from app.schemas.class_schema import ClassResponse

class StudentBase(BaseModel):
    user_id: int
    school_id: int
    major_id: int
    current_class_id: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    school_id: Optional[int] = None
    major_id: Optional[int] = None
    current_class_id: Optional[int] = None

class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True

class StudentWithDetails(StudentResponse):
    user: UserResponse
    school: SchoolResponse
    major: MajorResponse
    current_class: ClassResponse
