from typing import Optional
from pydantic import BaseModel

class InterviewNextStepBase(BaseModel):
    session_id: int
    title: str
    description_text: str

class InterviewNextStepCreate(InterviewNextStepBase):
    pass

class InterviewNextStepUpdate(BaseModel):
    title: Optional[str] = None
    description_text: Optional[str] = None

class InterviewNextStepResponse(InterviewNextStepBase):
    id: int

    class Config:
        from_attributes = True
