from typing import List, Annotated, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from supabase import Client
from app.core.database import get_supabase
from app.core.config import settings
from app.core.security import get_current_user
from app.schemas.interview_session import (
    InterviewSessionResponse, 
    InterviewSessionCreate,
    SessionInitiateResponse,
    SessionHistoryItem,
    SessionHistoryResponse,
    SessionSubmitRequest,
    SessionFeedbackResponse,
    SessionDetailResponse,
    FeedbackDetail
)
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService
from app.services.feedback_service import FeedbackService
from app.services.student_service import StudentService

router = APIRouter()

@router.get("/", response_model=SessionHistoryResponse)
async def get_my_sessions(
    current_user = Depends(get_current_user),
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    """
    Get current student's interview session history based on token-derived ID.
    
    This endpoint is for students to view their own session history.
    Requires: Authentication (JWT token)
    
    Returns: List of session history with dummy data (skeleton implementation)
    """
    # TODO: Get actual student_id from current_user and fetch real data
    # For now, return dummy data
    dummy_sessions = [
        SessionHistoryItem(
            id=1,
            status="completed",
            total_score=85.5,
            completed_at=datetime(2025, 11, 20, 14, 30, 0),
            created_at=datetime(2025, 11, 20, 14, 0, 0)
        ),
        SessionHistoryItem(
            id=2,
            status="in_progress",
            total_score=None,
            completed_at=None,
            created_at=datetime(2025, 11, 25, 10, 0, 0)
        ),
        SessionHistoryItem(
            id=3,
            status="completed",
            total_score=72.0,
            completed_at=datetime(2025, 11, 15, 16, 45, 0),
            created_at=datetime(2025, 11, 15, 16, 0, 0)
        ),
    ]
    
    return SessionHistoryResponse(
        sessions=dummy_sessions,
        total_count=len(dummy_sessions)
    )


@router.post("/submit", response_model=SessionFeedbackResponse)
async def submit_session_answers(
    request: SessionSubmitRequest,
    current_user = Depends(get_current_user),
    supabase: Annotated[Client, Depends(get_supabase)] = None
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
        session_id=request.session_id,
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
async def get_session_detail(
    session_id: int,
    current_user = Depends(get_current_user),
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    """
    Get detailed view of a student's specific session with feedbacks.
    
    This endpoint is for students to view their own session details and feedback.
    Requires: Authentication (JWT token) - student accessing their own session
    
    Parameters:
    - session_id: The ID of the session to retrieve
    
    Returns: Detailed session information with feedback (dummy data for skeleton)
    """
    # TODO: Verify current_user owns this session (student_id match)
    # TODO: Fetch actual session and feedback data from database
    # For now, return dummy data
    
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
    
    return SessionDetailResponse(
        session_id=session_id,
        student_id=1,  # TODO: Get actual student_id from current_user
        status="completed",
        total_score=85.5,
        created_at=datetime(2025, 11, 20, 14, 0, 0),
        completed_at=datetime(2025, 11, 20, 14, 30, 0),
        overall_score=85.5,
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


@router.post("/initiate", response_model=SessionInitiateResponse)
async def initiate_interview_session(
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, TXT, MD)"),
    raw_text: Optional[str] = Form(None, description="Raw text content"),
    student_id: int = Form(..., description="Student ID"),
    current_user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Initiate new interview session by processing document text or raw text.
    
    Requires: Authentication (any logged-in user)
    
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
    
    session_id: int | None = None
    
    try:
        # Step 0: Validate that at least one of file or raw_text is provided
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided"
            )
        
        # Step 1: Validate student exists
        student = await student_service.get_student(student_id)
        
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
            
            # Step 3b: Read file bytes
            file_bytes = await file.read()
            
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
        
        # Step 5: Create initial detailed_feedbacks record
        await feedback_service.create_detailed_feedback(session_id=session_id)
        
        # Step 6: Return simple success response
        return SessionInitiateResponse(
            success=True,
            message="Interview session initiated successfully",
            session_id=session['id']
        )
        
    except HTTPException:
        # HTTPExceptions already have proper status codes and messages
        # Perform rollback before re-raising
        await _rollback_session_creation(session_service, session_id)
        raise
        
    except Exception as e:
        # Unexpected errors - rollback and return 500
        await _rollback_session_creation(session_service, session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate interview session: {str(e)}"
        )


async def _rollback_session_creation(
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