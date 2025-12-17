from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.student import StudentResponse
from app.schemas.types import FlexibleDateTime

class InterviewSessionBase(BaseModel):
    student_id: int
    status: str
    total_score: Optional[float] = None

class InterviewSessionCreate(InterviewSessionBase):
    pass

class InterviewSessionUpdate(BaseModel):
    status: Optional[str] = None
    completed_at: Optional[FlexibleDateTime] = None
    total_score: Optional[float] = None

class InterviewSessionResponse(InterviewSessionBase):
    id: int
    completed_at: Optional[FlexibleDateTime] = None
    created_at: FlexibleDateTime

    class Config:
        from_attributes = True

class InterviewSessionWithDetails(InterviewSessionResponse):
    student: StudentResponse


class GeneratedQuestion(BaseModel):
    """Schema for a generated interview question"""
    question_order: int
    question_text: str

    class Config:
        from_attributes = True


class SessionInitiateResponse(BaseModel):
    """Response schema for session initiation - includes generated questions"""
    success: bool
    message: str
    session_id: int
    questions: List[GeneratedQuestion]

    class Config:
        from_attributes = True

class SessionQueueResponse(BaseModel):
    """Response schema for session submission queue confirmation."""
    success: bool
    message: str
    session_id: int
    
    class Config:
        from_attributes = True

class SessionHistoryItem(BaseModel):
    """Single session history item for listing"""
    id: int
    status: str
    interview_type: Optional[str] = None
    total_score: Optional[float] = None
    completed_at: Optional[FlexibleDateTime] = None
    created_at: FlexibleDateTime

    class Config:
        from_attributes = True


class SessionHistoryResponse(BaseModel):
    """Response schema for session history list"""
    sessions: List["SessionHistoryItem"]
    total_count: int

    class Config:
        from_attributes = True


class SessionWithStudentInfo(BaseModel):
    """Admin/teacher view of sessions with student context."""
    session_id: int
    interview_type: Optional[str] = None
    student_name: Optional[str]
    student_identifier: Optional[str]
    school_name: Optional[str] = None
    major_name: Optional[str] = None
    class_name: Optional[str] = None
    grade_level: Optional[int] = None
    total_score: Optional[float] = None
    status: str
    completed_at: Optional[FlexibleDateTime] = None
    created_at: FlexibleDateTime

    class Config:
        from_attributes = True


class SessionListForAdminsResponse(BaseModel):
    sessions: List[SessionWithStudentInfo]
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
    question_order: Optional[int] = None
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

class SessionStatusResponse(BaseModel):
    """Response schema for LLM-generated feedback"""
    session_id: int
    status: str
    is_ready: bool

    class Config:
        from_attributes = True

class SessionDetailResponse(BaseModel):
    """Detailed view of a specific session with all feedback"""
    session_id: int
    student_id: int
    status: str
    interview_type: Optional[str] = None
    total_score: Optional[float] = None
    created_at: FlexibleDateTime
    completed_at: Optional[FlexibleDateTime] = None
    overall_score: Optional[float] = None
    avg_cr: float = Field(default=0.0, description="Average Content Relevance score.")
    avg_st: float = Field(default=0.0, description="Average Structure score.")
    avg_fl: float = Field(default=0.0, description="Average Fluency score (Odd Qs only).")
    avg_cp: float = Field(default=0.0, description="Average Confidence Proxy score (Odd Qs only).")
    strength_summary: Optional[str] = None
    areas_for_growth: Optional[str] = None
    detailed_feedback: Optional[List[FeedbackDetail]] = None
    next_steps: Optional[List[str]] = None

    class Config:
        from_attributes = True


# --- A. Question Generation Request (Used by POST /initiate) ---

class QuestionGenerationRequest(BaseModel):
    """
    The data needed by the LLM Service to generate personalized questions.
    NOTE: The POST /initiate route uses Form data, not this Pydantic body,
    but the LLM Service function will use this model internally.
    """
    cv_text: str = Field(..., description="The candidate's CV/Resume text.")
    field: str = Field(..., description="The target industry/field.")
    role: str = Field(..., description="The specific job role being interviewed for.")

# --- B. Evaluation Input - QnA Pair (Used by POST /submit) ---

class QuestionAnswerPair(BaseModel):
    """
    Input structure for each question and answer, including required STT metrics.
    Replaces the simple QnAItem to capture objective fluency data.
    """
    question_order: int = Field(..., description="The sequence number of the question.")
    question_text: str = Field(..., description="The text of the question asked.")
    answer_text: str = Field(..., description="The student's full transcribed answer (input).")
    
    # REQUIRED INPUT 1: Measured duration from the client's recording timer
    audio_duration_seconds: float = Field(
        ..., 
        description="The total duration of the recorded audio for this answer, in seconds.",
        ge=0.0
    )
    
    # REQUIRED INPUT 2: Explicit word count (essential for languages like Korean)
    word_count: int = Field(
        ..., 
        description="The precise count of tokens/words in the transcribed answer.",
        ge=0
    )

    total_pause_count: int = Field(
        ...,
        description="Total number of detected pauses in the answer.",
        ge=0
    )

    total_pause_duration_seconds: float = Field(
        ...,
        description="Total cumulative duration of all detected pauses in seconds.",
        ge=0.0
    )

class SessionSubmitRequest(BaseModel):
    """
    Request schema for submitting answers to get feedback.
    Updated to use the detailed QuestionAnswerPair model.
    """
    session_id: int
    qa_pairs: List[QuestionAnswerPair] = Field(..., description="The list of all 10 questions and their corresponding answers/transcripts.")


# =========================================================
# III. LLM API STRUCTURED OUTPUT SCHEMAS (MIGRATED FROM OLD)
# =========================================================

class OverallScores(BaseModel):
    """Maps to the overall interview_score table/summary fields."""
    content_relevance_score: float = Field(..., description="Average score (0-10) for content relevance across all answers.")
    structure_score: float = Field(..., description="Average score (0-10) for answer structure (STAR) across all answers.")
    fluency_score: float = Field(..., description="Average score (0-10) for fluency and flow (low filler words, good pace).")
    confidence_proxy_score: float = Field(..., description="Average score (0-10) for confidence proxy (simulated speech rate stability/consistency).")
    overall_score: float = Field(..., description="The final aggregate score (0-100).")

class SessionSummary(BaseModel):
    """Maps to the summaries table."""
    strength_text: str = Field(..., description="A 2-3 sentence paragraph summarizing the student's key strengths.")
    areas_for_growth_text: str = Field(..., description="A 2-3 sentence paragraph summarizing the 2-3 most critical areas for growth.")

class NextStepItem(BaseModel):
    """Maps to the next_steps table."""
    title: str = Field(..., description="A concise title for the suggested practice activity.")
    description_text: str = Field(..., description="A 1-2 sentence description of the action the student should take.")

class DetailedEvaluationItem(BaseModel):
    """Detailed per-question feedback. Maps to the detailed_feedbacks update."""
    question_order: int = Field(..., description="The sequence number of the question (1-10).")
    
    # Individual Scores (0-10)
    content_relevance_score: float = Field(..., alias="cr_score", description="Content Relevance score (0-10).")
    structure_score: float = Field(..., alias="st_score", description="Structure (STAR) score (0-10).")
    fluency_score: float = Field(..., alias="fl_score", description="Fluency score (0-10).")
    confidence_score: float = Field(..., alias="cp_score", description="Confidence Proxy score (0-10).")
    overall_score: float = Field(..., description="Overall score for this specific question (0-10).")

    evaluation_text: str = Field(..., description="A short, concise paragraph providing holistic feedback for THIS single question/answer.")
    is_correct: bool = Field(..., description="True if the core facts/content were accurate and relevant.")

    class Config:
        # Allows accessing fields using both snake_case (Python) and alias (LLM output)
        populate_by_name = True 

class EvaluationBatchResponse(BaseModel):
    """The single, comprehensive JSON object returned by the LLM evaluation call."""
    per_question_feedback: List[DetailedEvaluationItem] = Field(..., description="A list containing exactly 10 detailed feedback objects.")
    overall_scores: OverallScores
    session_summary: SessionSummary
    next_steps: List[NextStepItem] = Field(..., description="Exactly 3 actionable next step recommendations.")