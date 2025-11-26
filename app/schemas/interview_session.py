from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.schemas.student import StudentResponse

class InterviewSessionBase(BaseModel):
    student_id: int
    status: str
    total_score: Optional[float] = None

class InterviewSessionCreate(InterviewSessionBase):
    pass

class InterviewSessionUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    total_score: Optional[float] = None

class InterviewSessionResponse(InterviewSessionBase):
    id: int
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

class InterviewSessionWithDetails(InterviewSessionResponse):
    student: StudentResponse


class SessionInitiateResponse(BaseModel):
    """Response schema for session initiation - simplified without storage"""
    success: bool
    message: str
    session_id: int

    class Config:
        from_attributes = True


# ========== New Session History & Feedback Schemas ==========

class SessionHistoryItem(BaseModel):
    """Single session history item for listing"""
    id: int
    status: str
    total_score: Optional[float] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SessionHistoryResponse(BaseModel):
    """Response schema for session history list"""
    sessions: List["SessionHistoryItem"]
    total_count: int

    class Config:
        from_attributes = True


class QnAItem(BaseModel):
    """Single Q&A item in the conversation history"""
    question: str
    answer: str


class SessionSubmitRequest(BaseModel):
    """Request schema for submitting answers to get feedback"""
    session_id: int
    qna_history: List[QnAItem]


class FeedbackDetail(BaseModel):
    """Detailed feedback for a single Q&A"""
    question: str
    answer: str
    evaluation: str
    content_relevance_score: Optional[float] = None
    structure_score: Optional[float] = None
    fluency_score: Optional[float] = None
    confidence_score: Optional[float] = None
    overall_score: Optional[float] = None
    is_correct: bool


class SessionFeedbackResponse(BaseModel):
    """Response schema for LLM-generated feedback"""
    session_id: int
    overall_score: float
    strength_summary: str
    areas_for_growth: str
    detailed_feedback: List[FeedbackDetail]
    next_steps: List[str]

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    """Detailed view of a specific session with all feedback"""
    session_id: int
    student_id: int
    status: str
    total_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    overall_score: Optional[float] = None
    strength_summary: Optional[str] = None
    areas_for_growth: Optional[str] = None
    detailed_feedback: Optional[List[FeedbackDetail]] = None
    next_steps: Optional[List[str]] = None

    class Config:
        from_attributes = True
