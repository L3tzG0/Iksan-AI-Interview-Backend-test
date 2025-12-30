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


class NextStepItem(BaseModel):
    """Maps to the next_steps table."""
    title: str = Field(..., description="권장되는 연습 활동에 대한 간결한 제목입니다")
    description_text: str = Field(..., description="학생이 취해야 할 조치에 대한 1~2문장 분량의 설명입니다.")

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
    next_steps: Optional[List[NextStepItem]] = None

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
    question_order: int = Field(..., description="질문의 순번입니다.")
    question_text: str = Field(..., description="진행된 질문의 텍스트입니다.")
    answer_text: Optional[str] = Field(None, description="학생의 전사된 전체 답변(입력값)입니다.")
    
    # OPTIONAL INPUT 1: Measured duration from the client's recording timer
    audio_duration_seconds: Optional[float] = Field(
        None, 
        description="이 답변에 대해 녹음된 오디오의 총 시간(초 단위)입니다.",
        ge=0.0
    )
    
    # OPTIONAL INPUT 2: Explicit word count (essential for languages like Korean)
    word_count: Optional[int] = Field(
        None, 
        description="전사된 답변 내의 토큰 또는 단어의 정확한 개수입니다.",
        ge=0
    )

    total_pause_count: Optional[int] = Field(
        None,
        description="답변에서 감지된 총 일시 정지(멈춤) 횟수입니다.",
        ge=0
    )

    total_pause_duration_seconds: Optional[float] = Field(
        None,
        description="감지된 모든 일시 정지(멈춤)의 누적 시간(초 단위)입니다.",
        ge=0.0
    )

class SessionSubmitRequest(BaseModel):
    """
    Request schema for submitting answers to get feedback.
    Updated to use the detailed QuestionAnswerPair model.
    """
    session_id: int
    qa_pairs: Optional[List[QuestionAnswerPair]] = Field(None, description="The list of all 10 questions and their corresponding answers/transcripts. Optional: can be null or undefined.")


# =========================================================
# III. LLM API STRUCTURED OUTPUT SCHEMAS (MIGRATED FROM OLD)
# =========================================================

class OverallScores(BaseModel):
    """Maps to the overall interview_score table/summary fields."""
    content_relevance_score: float = Field(..., description="모든 답변에 대한 내용 관련성의 평균 점수 (0-10).")
    structure_score: float = Field(..., description="모든 답변에 대한 답변 구조(STAR)의 평균 점수 (0-10).")
    fluency_score: float = Field(..., description="유창성 및 흐름(낮은 불필요한 추임새 비율, 적절한 속도)에 대한 평균 점수 (0-10).")
    confidence_proxy_score: float = Field(..., description="자신감 프록시(발화 속도의 안정성 및 일관성 시뮬레이션)에 대한 평균 점수 (0-10).")
    overall_score: float = Field(..., description="최종 종합 집계 점수 (0-10).")

class SessionSummary(BaseModel):
    """Maps to the summaries table."""
    strength_text: str = Field(..., description="학생의 주요 강점을 요약하는 2~3문장 분량의 단락입니다.")
    areas_for_growth_text: str = Field(..., description="가장 중요한 2~3가지 개선 필요 사항을 요약하는 2~3문장 분량의 단락입니다.")

class DetailedEvaluationItem(BaseModel):
    """Detailed per-question feedback. Maps to the detailed_feedbacks update."""
    question_order: int = Field(..., description="질문의 순번입니다 (1-10).")
    
    # Individual Scores (0-10)
    content_relevance_score: float = Field(..., alias="cr_score", description="내용 관련성 점수 (0-10).")
    structure_score: float = Field(..., alias="st_score", description="구조(STAR) 점수 (0-10).")
    fluency_score: float = Field(..., alias="fl_score", description="유창성 점수 (0-10).")
    confidence_score: float = Field(..., alias="cp_score", description="자신감 프록시 점수 (0-10).")
    overall_score: float = Field(..., description="해당 질문에 대한 종합 점수 (0-10).")

    evaluation_text: str = Field(..., description="해당 단일 질문/답변에 대한 통합 피드백을 제공하는 짧고 간결한 단락입니다.")
    is_correct: bool = Field(..., description="핵심 사실이나 내용이 정확하고 질문과 관련이 있는 경우 True로 표시됩니다.")

    class Config:
        # Allows accessing fields using both snake_case (Python) and alias (LLM output)
        populate_by_name = True 

class EvaluationBatchResponse(BaseModel):
    """The single, comprehensive JSON object returned by the LLM evaluation call."""
    per_question_feedback: List[DetailedEvaluationItem] = Field(..., description="A list containing exactly 10 detailed feedback objects.")
    overall_scores: OverallScores
    session_summary: SessionSummary
    next_steps: List[NextStepItem] = Field(..., description="Exactly 3 actionable next step recommendations.")