from typing import Optional
from pydantic import BaseModel

class InterviewDetailedFeedbackBase(BaseModel):
    session_id: int
    question_order: Optional[int] = None
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    evaluation_text: Optional[str] = None
    is_correct: bool = False
    score: Optional[float] = None
    transcript: Optional[str] = None

class InterviewDetailedFeedbackCreate(BaseModel):
    """Simplified for initial creation - only requires session_id"""
    session_id: int

class InterviewDetailedFeedbackUpdate(BaseModel):
    evaluation_text: Optional[str] = None
    score: Optional[float] = None

class InterviewDetailedFeedbackResponse(InterviewDetailedFeedbackBase):
    id: int

    class Config:
        from_attributes = True
