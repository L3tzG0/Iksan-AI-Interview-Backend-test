from pydantic import BaseModel
from uuid import UUID
from app.schemas.user import UserProfileResponse

class TeacherBase(BaseModel):
    user_id: UUID

class TeacherCreate(TeacherBase):
    pass

class TeacherResponse(TeacherBase):
    id: int

    class Config:
        from_attributes = True

class TeacherWithUser(TeacherResponse):
    user_profile: UserProfileResponse
