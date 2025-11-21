from pydantic import BaseModel
from app.schemas.user import UserResponse

class TeacherBase(BaseModel):
    user_id: int

class TeacherCreate(TeacherBase):
    pass

class TeacherResponse(TeacherBase):
    pass

    class Config:
        from_attributes = True

class TeacherWithUser(TeacherResponse):
    user: UserResponse
