from typing import Optional
from pydantic import BaseModel

class InterviewDetailedFeedbackBase(BaseModel):
    session_id: int
    question_order: Optional[int] = None
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    evaluation_text: Optional[str] = None
    is_correct: bool = False
    content_relevance_score: Optional[float] = None
    structure_score: Optional[float] = None
    fluency_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None

class InterviewDetailedFeedbackCreate(BaseModel):
    """Simplified for initial creation - only requires session_id"""
    session_id: int

class InterviewDetailedFeedbackUpdate(BaseModel):
    question_order: Optional[int] = None
    question_text: Optional[str] = None
    answer_text: Optional[str] = None
    evaluation_text: Optional[str] = None
    is_correct: Optional[bool] = None
    content_relevance_score: Optional[float] = None
    structure_score: Optional[float] = None
    fluency_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None

class InterviewDetailedFeedbackResponse(InterviewDetailedFeedbackBase):
    id: int

    class Config:
        from_attributes = True
