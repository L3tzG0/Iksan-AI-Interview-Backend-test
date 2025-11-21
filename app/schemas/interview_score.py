from typing import Optional
from pydantic import BaseModel

class InterviewScoreBase(BaseModel):
    session_id: int
    content_relevance_score: float
    structure_score: float
    fluency_score: float
    confidence_score: float
    overall_score: float

class InterviewScoreCreate(InterviewScoreBase):
    pass

class InterviewScoreUpdate(BaseModel):
    content_relevance_score: Optional[float] = None
    structure_score: Optional[float] = None
    fluency_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None

class InterviewScoreResponse(InterviewScoreBase):
    id: int

    class Config:
        from_attributes = True
