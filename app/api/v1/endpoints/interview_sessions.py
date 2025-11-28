from typing import List, Annotated, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status, Query, Request
from supabase import Client
from app.core.database import get_supabase
from app.core.config import settings
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.schemas.interview_session import (
    InterviewSessionResponse, 
    InterviewSessionCreate,
    SessionInitiateResponse,
    SessionHistoryItem,
    SessionHistoryResponse,
    SessionSubmitRequest,
    SessionFeedbackResponse,
    SessionDetailResponse,
    FeedbackDetail,
    GeneratedQuestion
)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService
from app.services.feedback_service import FeedbackService
from app.services.student_service import StudentService
from app.services.user_service import UserProfileService
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/", response_model=SessionHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_my_sessions(
    request: Request,
    supabase: Annotated[Client, Depends(get_supabase)],
    current_user = Depends(get_current_user),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status (completed, in_progress, failed)")
):
    """
    Get current student's interview session history based on token-derived ID.
    
    This endpoint is for students to view their own session history.
    Requires: Authentication (JWT token)
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **status_filter**: Filter by session status
    
    Returns: Paginated list of session history
    """
    # Get student_id from current_user
    user_service = UserProfileService(supabase)
    student_details = user_service.get_student_details(current_user.id)
    
    if not student_details:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not a student"
        )
    
    student_id = student_details.get("id")
    
    # Fetch real session data with pagination
    session_service = InterviewSessionService(supabase)
    sessions, total = session_service.get_sessions_by_student(
        student_id=student_id,
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )
    
    # Transform to SessionHistoryItem format
    session_items = [
        SessionHistoryItem(
            id=s["id"],
            status=s["status"],
            total_score=s.get("total_score"),
            completed_at=s.get("completed_at"),
            created_at=s["created_at"]
        )
        for s in sessions
    ]
    
    return SessionHistoryResponse(
        sessions=session_items,
        total_count=total
    )


@router.post("/submit", response_model=SessionFeedbackResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
def submit_session_answers(
    request: Request,
    submit_request: SessionSubmitRequest,
    supabase: Annotated[Client, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Submit answers and get complete feedback from LLM.
    
    FE submits the complete QnA history, and this endpoint will:
    1. Call LLM with the whole QnA history
    2. Generate comprehensive feedback
    3. Return scores, summaries, and next steps
    
    Requires: Authentication (JWT token)
    
    Returns: Complete feedback response (dummy data for skeleton implementation)
    """
    # TODO: Implement actual LLM call with QnA history
    # For now, return dummy feedback data
    
    dummy_detailed_feedback = [
        FeedbackDetail(
            question="자기소개를 해주세요.",
            answer="안녕하세요, 저는 컴퓨터공학을 전공하고 있는 학생입니다.",
            evaluation="명확하고 간결한 자기소개입니다. 전공 분야를 잘 언급했습니다.",
            content_relevance_score=8.5,
            structure_score=8.0,
            fluency_score=9.0,
            confidence_score=8.5,
            overall_score=8.5,
            is_correct=True
        ),
        FeedbackDetail(
            question="왜 이 직무에 지원하셨나요?",
            answer="개발에 대한 열정이 있고, 실무 경험을 쌓고 싶습니다.",
            evaluation="동기는 좋으나 좀 더 구체적인 이유를 제시하면 좋겠습니다.",
            content_relevance_score=7.0,
            structure_score=6.5,
            fluency_score=7.5,
            confidence_score=7.0,
            overall_score=7.0,
            is_correct=True
        ),
        FeedbackDetail(
            question="팀 프로젝트 경험에 대해 말씀해주세요.",
            answer="학교에서 웹 개발 프로젝트를 진행한 경험이 있습니다.",
            evaluation="경험을 언급했으나 역할과 성과에 대한 구체적인 설명이 부족합니다.",
            content_relevance_score=6.5,
            structure_score=6.0,
            fluency_score=7.0,
            confidence_score=6.5,
            overall_score=6.5,
            is_correct=True
        ),
    ]
    
    return SessionFeedbackResponse(
        session_id=submit_request.session_id,
        overall_score=73.3,
        strength_summary="명확한 의사소통 능력과 기본적인 기술 지식을 보여주셨습니다. 자기소개가 간결하고 전공 분야를 잘 어필했습니다.",
        areas_for_growth="답변에 구체적인 예시와 수치를 포함하면 더 설득력이 있을 것입니다. 경험을 설명할 때 STAR 기법(상황-과제-행동-결과)을 활용해보세요.",
        detailed_feedback=dummy_detailed_feedback,
        next_steps=[
            "STAR 기법을 활용한 답변 연습하기",
            "프로젝트 경험에 대한 구체적인 수치와 성과 정리하기",
            "지원 직무와 관련된 기술 질문 대비하기",
            "모의 면접을 통해 실전 감각 익히기"
        ]
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_session_detail(
    request: Request,
    session_id: int,
    supabase: Annotated[Client, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Get detailed view of a student's specific session with feedbacks.
    
    This endpoint is for students to view their own session details and feedback.
    Uses relational select to fetch session with all feedbacks in a single query.
    Requires: Authentication (JWT token) - student accessing their own session
    
    Parameters:
    - session_id: The ID of the session to retrieve
    
    Returns: Detailed session information with feedback
    """
    session_service = InterviewSessionService(supabase)
    user_service = UserProfileService(supabase)
    
    # Get the session with all related data in single query
    session = session_service.get_session_with_feedbacks(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify current user owns this session (get student details)
    student_details = user_service.get_student_details(current_user.id)
    if student_details and student_details.get("id") != session.get("student_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sessions"
        )
    
    # Transform detailed_feedbacks from database format
    detailed_feedbacks = session.get("detailed_feedbacks", []) or []
    feedback_list = [
        FeedbackDetail(
            question=fb.get("question_text") or "",
            answer=fb.get("answer_text") or "",
            evaluation=fb.get("evaluation_text") or "",
            content_relevance_score=fb.get("content_relevance_score"),
            structure_score=fb.get("structure_score"),
            fluency_score=fb.get("fluency_score"),
            confidence_score=fb.get("confidence_score"),
            overall_score=fb.get("overall_score"),
            is_correct=fb.get("is_correct") or False
        )
        for fb in sorted(detailed_feedbacks, key=lambda x: x.get("question_order", 0))
    ]
    
    # Get summary data
    summaries = session.get("summaries")
    strength_summary = None
    areas_for_growth = None
    if summaries:
        # summaries could be a list or dict depending on DB structure
        if isinstance(summaries, list) and len(summaries) > 0:
            strength_summary = summaries[0].get("strength_text")
            areas_for_growth = summaries[0].get("areas_for_growth_text")
        elif isinstance(summaries, dict):
            strength_summary = summaries.get("strength_text")
            areas_for_growth = summaries.get("areas_for_growth_text")
    
    # Get next steps
    next_steps_data = session.get("next_steps", []) or []
    next_steps = [
        ns.get("title", "") or ns.get("description_text", "")
        for ns in sorted(next_steps_data, key=lambda x: x.get("next_step_order", 0))
    ]
    
    return SessionDetailResponse(
        session_id=session["id"],
        student_id=session["student_id"],
        status=session["status"],
        total_score=session.get("total_score"),
        created_at=session["created_at"],
        completed_at=session.get("completed_at"),
        overall_score=session.get("total_score"),
        strength_summary=strength_summary,
        areas_for_growth=areas_for_growth,
        detailed_feedback=feedback_list if feedback_list else None,
        next_steps=next_steps if next_steps else None
    )


@router.post("/initiate", response_model=SessionInitiateResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
def initiate_interview_session(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, TXT, MD)"),
    raw_text: Optional[str] = Form(None, description="Raw text content"),
    student_id: int = Form(..., description="Student ID"),
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate new interview session by processing document text or raw text.
    
    Requires: Authentication (any logged-in user)
    Rate limited: 10 requests per minute per user.
    
    Parameters:
    - file (optional): Document file to process (PDF, DOCX, TXT, MD)
    - raw_text (optional): Raw text content
    - student_id (required): Student ID
    
    Note: At least one of 'file' or 'raw_text' must be provided.
    If both are provided, the file will be processed and raw_text will be ignored.
    
    Security measures:
    - Authentication required (JWT token)
    - Student existence validation
    - File type validation (MIME type) - when file is provided
    - File signature verification (magic numbers) - when file is provided
    - Filename sanitization - when file is provided
    - File size limits - when file is provided
    
    Simplified flow (no storage):
    1. Validates authentication
    2. Validates at least one of file or raw_text is provided
    3. Validates student exists
    4. If file provided: validates file type, signature, and size, extracts text
    5. If only raw_text provided: uses raw_text directly
    6. Creates session with status "in_progress"
    7. Saves raw_text to documents table
    8. Creates initial detailed_feedbacks record
    9. Returns success response
    
    If any step fails, the session is marked as failed.
    """
    # Initialize services
    storage_service = StorageService(supabase)  # Used for validation only
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    feedback_service = FeedbackService(supabase)
    student_service = StudentService(supabase)
    llm_service = LLMService()
    
    session_id: int | None = None
    
    try:
        # Step 0: Validate that at least one of file or raw_text is provided
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided"
            )
        
        # Step 1: Validate student exists
        student = student_service.get_student(student_id)
        
        # Step 2: Create session
        session = session_service.create_session(student_id=student_id, status="in_progress")
        session_id = session['id']
        
        # Ensure session_id is set (type narrowing)
        assert session_id is not None, "Session ID must be set after creation"
        
        # Step 3: Process file or use raw_text
        cleaned_text_extracted: str
        
        if file:
            # File provided - process it (ignore raw_text if also provided)
            # Step 3a: Validate file type and filename
            storage_service.validate_file(file)
            
            # Step 3b: Read file bytes (sync read from SpooledTemporaryFile)
            # Note: file.file is the underlying SpooledTemporaryFile which supports sync read
            file_bytes = file.file.read()
            
            # Validate file size
            if len(file_bytes) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
                )
            
            # Verify file signature (magic numbers)
            content_type = file.content_type or "application/octet-stream"
            storage_service.verify_file_signature(file_bytes, content_type)
            
            # Step 3c: Extract and clean text from document
            cleaned_text_extracted = extraction_service.extract_text_from_file(
                file_bytes=file_bytes,
                content_type=content_type
            )
        else:
            # Only raw_text provided - use it directly as cleaned text
            # At this point raw_text is guaranteed to be str due to validation above
            if raw_text is None:
                raise HTTPException(status_code=400, detail="raw_text cannot be None")
            cleaned_text_extracted = raw_text
        
        # Step 4: Save cleaned text to documents table
        document = document_service.create_document(
            session_id=session_id,
            cleaned_text=cleaned_text_extracted
        )
        
        # Step 5: Generate interview questions using LLM
        question_texts = llm_service.generate_interview_questions(cleaned_text_extracted)
        
        # Step 6: Create detailed_feedbacks records (10 rows with questions)
        feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=question_texts
        )
        
        # Step 7: Build response with all generated questions
        generated_questions = [
            GeneratedQuestion(
                question_order=idx + 1,
                question_text=q_text
            )
            for idx, q_text in enumerate(question_texts)
        ]
        
        return SessionInitiateResponse(
            success=True,
            message="Interview session initiated successfully with 10 questions",
            session_id=session['id'],
            questions=generated_questions
        )
        
    except HTTPException:
        # HTTPExceptions already have proper status codes and messages
        # Perform rollback before re-raising
        _rollback_session_creation(session_service, session_id)
        raise
        
    except Exception as e:
        # Unexpected errors - rollback and return 500
        _rollback_session_creation(session_service, session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate interview session: {str(e)}"
        )


def _rollback_session_creation(
    session_service: InterviewSessionService,
    session_id: int | None = None
):
    """
    Rollback changes if session initiation fails.
    
    Simplified: Only marks session as failed (no storage cleanup needed).
    We keep the session record for debugging purposes.
    """
    # Mark session as failed (keep for debugging, don't delete)
    if session_id:
        try:
            session_service.update_session_status(session_id, status="failed")
        except Exception as e:
            print(f"Warning: Failed to update session status during rollback: {str(e)}")