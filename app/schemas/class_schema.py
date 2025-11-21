from typing import Optional
from pydantic import BaseModel
from app.schemas.teacher import TeacherResponse

class ClassBase(BaseModel):
    class_name: str
    grade_level: str
    homeroom_teacher_id: int

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    grade_level: Optional[str] = None
    homeroom_teacher_id: Optional[int] = None

class ClassResponse(ClassBase):
    id: int

    class Config:
        from_attributes = True

class ClassWithTeacher(ClassResponse):
    homeroom_teacher: Optional[TeacherResponse] = None
