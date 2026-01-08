from typing import Optional
from pydantic import BaseModel

class InterviewSummaryBase(BaseModel):
    session_id: int
    strength_text: str
    areas_for_growth_text: str

class InterviewSummaryCreate(InterviewSummaryBase):
    pass

class InterviewSummaryUpdate(BaseModel):
    strength_text: Optional[str] = None
    areas_for_growth_text: Optional[str] = None

class InterviewSummaryResponse(InterviewSummaryBase):
    id: int

    class Config:
        from_attributes = True
