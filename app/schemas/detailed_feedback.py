from typing import Optional
from pydantic import BaseModel

class DetailedFeedbackBase(BaseModel):
    session_id: int
    question_order: int
    question_text: str
    answer_text: str
    evaluation_text: str
    is_correct: bool
    score: float
    transcript: str
    audio_path: str

class DetailedFeedbackCreate(DetailedFeedbackBase):
    pass

class DetailedFeedbackUpdate(BaseModel):
    evaluation_text: Optional[str] = None
    score: Optional[float] = None

class DetailedFeedbackResponse(DetailedFeedbackBase):
    id: int

    class Config:
        from_attributes = True
