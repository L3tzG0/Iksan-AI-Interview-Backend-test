from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.schemas.student import StudentResponse
from app.schemas.document import DocumentUploadResponse

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
    updated_at: datetime

    class Config:
        from_attributes = True

class InterviewSessionWithDetails(InterviewSessionResponse):
    student: StudentResponse


class SessionInitiateResponse(BaseModel):
    """Response schema for session initiation with document upload"""
    session_id: int
    student_id: int
    status: str
    document: DocumentUploadResponse
    created_at: datetime

    class Config:
        from_attributes = True
