from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from app.schemas.user import UserProfileResponse
from app.schemas.school import SchoolResponse

class TeacherBase(BaseModel):
    user_id: UUID

class TeacherCreate(TeacherBase):
    school_id: Optional[int] = None

class TeacherUpdate(BaseModel):
    school_id: Optional[int] = None

class TeacherResponse(TeacherBase):
    id: int
    school_id: Optional[int] = None

    class Config:
        from_attributes = True

class TeacherWithUser(TeacherResponse):
    user_profile: UserProfileResponse

class TeacherWithDetails(TeacherResponse):
    user_profile: UserProfileResponse
    school: Optional[SchoolResponse] = None
