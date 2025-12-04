from typing import Optional
from pydantic import BaseModel
from app.schemas.teacher import TeacherResponse

class ClassBase(BaseModel):
    class_year: int
    homeroom_teacher_id: Optional[int] = None

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    class_year: Optional[int] = None
    homeroom_teacher_id: Optional[int] = None

class ClassResponse(ClassBase):
    id: int

    class Config:
        from_attributes = True

class ClassWithTeacher(ClassResponse):
    homeroom_teacher: Optional[TeacherResponse] = None
