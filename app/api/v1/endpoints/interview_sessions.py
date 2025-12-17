from typing import Annotated, Optional
from datetime import datetime
import logging
import json
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status, Query, Request, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from supabase import AsyncClient
from app.core.database import get_supabase
from app.core.config import settings
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.api.dependencies import require_role, RoleContext
from app.services.storage_service import StorageService

#redis import
import redis 
from app.core.redis_client import get_redis_connection
from app.services.queue_service import QueueService 

# New service imports (replacing LLMService)
from app.services.question_generator import generate_interview_questions
from app.services.evaluation_generator import generate_session_evaluation
from app.services.university_question_generator import generate_university_prep_questions

from app.services.rag_service import retrieve_questions_from_rag

from app.schemas.interview_session import (
    InterviewSessionResponse, 
    SessionInitiateResponse,
    SessionQueueResponse,
    SessionHistoryItem,
    SessionHistoryResponse,
    SessionListForAdminsResponse,
    SessionSubmitRequest,
    SessionWithStudentInfo,
    SessionFeedbackResponse,
    SessionDetailResponse,
    FeedbackDetail,
    GeneratedQuestion,
    QuestionAnswerPair,
    SessionStatusResponse
)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService
from app.services.feedback_service import FeedbackService
from app.services.user_service import UserProfileService
from app.services.text_sanitizer import sanitize_qa_pairs, sanitize_json_string
from app.schemas.summary import InterviewSummaryCreate
from app.schemas.next_step import InterviewNextStepCreate
from app.services.datetime_utils import pad_microseconds 


router = APIRouter()


@router.get("/", response_model=SessionHistoryResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_my_sessions(
    request: Request,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
    student_details = await user_service.get_student_details(current_user.id)
    
    if not student_details:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Current user is not a student"
        )
    
    student_id = student_details.get("id")
    
    # Fetch real session data with pagination
    session_service = InterviewSessionService(supabase)
    sessions, total = await session_service.get_sessions_by_student(
        student_id=student_id,
        skip=skip,
        limit=limit,
        status_filter=status_filter
    )
    
    # Transform to SessionHistoryItem format
    session_payloads = session_service.build_history_payloads(sessions)
    session_items = [
        SessionHistoryItem.model_construct(**payload)
        for payload in session_payloads
    ]
    
    response = SessionHistoryResponse(
        sessions=session_items,
        total_count=total
    )
    return JSONResponse(content=jsonable_encoder(response.dict()))


@router.get("/all", response_model=SessionListForAdminsResponse, summary="Retrieve student interview session history")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_sessions_with_students(
    request: Request,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    role_context: RoleContext = Depends(require_role(["teacher", "admin"])),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status (completed, in_progress, failed)")
):
    """
    Retrieve student interview session history

    - Admins: All students across the system.
    - Teachers: Only students within their school.
    """
    session_service = InterviewSessionService(supabase)

    school_id: Optional[int] = None
    if role_context.role_name == "teacher":
        teacher_response = await supabase.table("teachers").select("school_id").eq("user_id", str(role_context.user.id)).single().execute()
        school_id = teacher_response.data.get("school_id") if teacher_response and teacher_response.data else None
        if not school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not associated with a school"
            )

    sessions, total = await session_service.get_sessions_with_student_info(
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        school_id=school_id
    )

    shaped_sessions = [
        SessionWithStudentInfo.model_construct(
            **session_service.shape_session_with_student_info(
                session,
                include_school=(role_context.role_name == "admin")
            )
        )
        for session in sessions
    ]

    response = SessionListForAdminsResponse(
        sessions=shaped_sessions,
        total_count=total
    )
    return JSONResponse(content=jsonable_encoder(response.dict()))

@router.post("/submit", 
    response_model=SessionQueueResponse, # Use the new queue response model
    status_code=status.HTTP_202_ACCEPTED # Returns 202 Accepted immediately
)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def submit_session_answers(
    request: Request,
    redis_conn: Annotated[redis.Redis, Depends(get_redis_connection)], # ADDED
    submit_request: SessionSubmitRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Submit answers and queue the LLM evaluation.
    
    This endpoint performs validation, updates session status to 'pending_evaluation',
    and immediately returns a 202 Accepted response. The heavy evaluation is done
    by a background worker.
    """
    session_service = InterviewSessionService(supabase)
    user_service = UserProfileService(supabase)
    queue_service = QueueService(redis_conn) # ADDED
    
    session_id = submit_request.session_id
    
    # 1. Fetch and validate session state & ownership
    session = await session_service.get_session(session_id)
    if not session or session.get("status") != "in_progress":
        raise HTTPException(
            status_code=400, 
            detail=f"Session {session_id} not found or not in 'in_progress' status."
        )
    
    student_details = await user_service.get_student_details(current_user.id)
    student_id = student_details.get("id")
    if session.get("student_id") != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="You are not authorized to submit to this session."
        )
        
    if not submit_request.qa_pairs:
        # Edge case: If no answers are provided, mark as completed immediately (no LLM required)
        await session_service.update_session_status(
            session_id, 
            status="completed", 
            total_score=0.0,
            completed_at=datetime.now()
        )
        
        # Return 200 OK since the final status is resolved and no further async action is needed
        response_payload = SessionQueueResponse(
            success=True,
            session_id=int(session_id), # Cast to int for the response model
            message="Session completed with score 0.0 (No Q&A pairs provided)."
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(response_payload.model_dump())
        )

    try:
        # clean answer
        sanitized_qa_pairs = sanitize_qa_pairs(submit_request.qa_pairs)
        # 2. Update session status to reflect that evaluation is pending
        await session_service.update_session_status(session_id, status="pending_evaluation")
        
        # 3. ENQUEUE THE JOB (Replaces all synchronous LLM/DB steps)
        job_payload = {
            "job_type": "evaluation", 
            "session_id": session_id,
            "qa_pairs": [p.model_dump() for p in sanitized_qa_pairs],
            "timestamp": datetime.now().isoformat()
        }
        
        queue_length = queue_service.enqueue_job(job_payload)

        # 4. Return 202 Accepted response
        response_payload = SessionQueueResponse(
            success=True,
            session_id=int(session_id), # Cast to int for the response model
            message=f"Session evaluation job accepted and queued. There are {queue_length - 1} pending jobs ahead of yours. Check session status for completion."
        )
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content=jsonable_encoder(response_payload.model_dump())
        )

    except Exception as e:
        # If queueing or initial status update fails, mark the session as failed
        error_detail = str(e)
        await session_service.update_session_status(
            session_id, 
            status="failed",
            completed_at=datetime.now()
        )
        logging.error(f"Critical error during session submission/queuing for ID {session_id}: {e}")
        
        # Re-raise as HTTPException which will return a 500 status code
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue session evaluation job. Session marked as failed. Error: {error_detail}"
        )

# --- ASYNCHRONOUS FLOW - STEP 2: STATUS CHECK (Polling) ---
@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: Annotated[int, Path(description="The ID of the interview session")],
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    role_context: RoleContext = Depends(require_role(["student", "teacher", "admin"]))
):
    """
    Allows the client to poll for the current status of a queued session.
    """
    user_service = UserProfileService(supabase)
    session_service = InterviewSessionService(supabase)
    
    # 1. Fetch session
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # 2. Role-aware authorization
    if role_context.role_name == "student":
        student_details = await user_service.get_student_details(role_context.user.id)
        if not student_details:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not associated with a student record"
            )
        if session.get("student_id") != student_details.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this session."
            )
    elif role_context.role_name == "teacher":
        teacher_response = await supabase.table("teachers").select("school_id").eq("user_id", str(role_context.user.id)).single().execute()
        teacher_school_id = teacher_response.data.get("school_id") if teacher_response and teacher_response.data else None
        if not teacher_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not associated with a school"
            )

        student_response = await supabase.table("students").select("school_id").eq("id", session.get("student_id")).single().execute()
        student_school_id = student_response.data.get("school_id") if student_response and student_response.data else None
        if not student_school_id or student_school_id != teacher_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this session."
            )
    else:
        # Admins are allowed to view any session
        pass
    
    status_message = session.get('status')
    
    return SessionStatusResponse(
        session_id=session_id,
        status=status_message,
        is_ready=(status_message == "in_progress")
    )

@router.get("/{session_id}", response_model=SessionDetailResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_session_detail(
    request: Request,
    session_id: int,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    role_context: RoleContext = Depends(require_role(["student", "teacher", "admin"]))
):
    """
    Get detailed view of a student's specific session with feedbacks.
    
    If the session is not 'completed', this returns a 409 Conflict.
    """
    session_service = InterviewSessionService(supabase)
    user_service = UserProfileService(supabase)
    
    # Get the session with all related data in single query
    session = await session_service.get_session_with_feedbacks(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if 'created_at' in session and session['created_at']:
        session['created_at'] = pad_microseconds(session['created_at'])
    if 'completed_at' in session and session['completed_at']:
        session['completed_at'] = pad_microseconds(session['completed_at'])
    
    # >>> NEW CHECK: If session is not completed, block retrieval and advise polling. <<<
    current_status = session.get("status")
    if current_status not in ["in_progress", "completed"]:
        # Raise 409 Conflict to signal that the request cannot be fulfilled yet.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session is still processing. Current status: {current_status}. Please continue polling the /status/{session_id} endpoint."
        )
    
    # Verify access based on role
    if role_context.role_name == "student":
        student_details = await user_service.get_student_details(role_context.user.id)
        if not student_details:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not associated with a student record"
            )
        if student_details.get("id") != session.get("student_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own sessions"
            )
    elif role_context.role_name == "teacher":
        teacher_response = await supabase.table("teachers").select("school_id").eq("user_id", str(role_context.user.id)).single().execute()
        teacher_school_id = teacher_response.data.get("school_id") if teacher_response and teacher_response.data else None
        if not teacher_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Teacher is not associated with a school"
            )
        student_response = await supabase.table("students").select("school_id").eq("id", session.get("student_id")).single().execute()
        student_school_id = student_response.data.get("school_id") if student_response and student_response.data else None
        if not student_school_id or student_school_id != teacher_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this session"
            )
    else:
        # Admins can view any session
        pass
    
    # Transform detailed_feedbacks from database format
    sorted_feedbacks = session_service.normalize_ordered_records(
        session.get("detailed_feedbacks"),
        "question_order"
    )
    feedback_list = [
        FeedbackDetail(
            question_order=fb.get("question_order"),
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
        for fb in sorted_feedbacks
        # if fb.get("overall_score") is not None and fb.get("overall_score") > 0.0 # Only show evaluated items
    ]
    
    # Get summary data
    summaries = session.get("summaries")
    strength_summary = None
    areas_for_growth = None
    if summaries:
        # summaries could be a list or dict depending on DB structure
        if isinstance(summaries, list) and len(summaries) > 0:
            # We assume the first (or only) summary record is the right one
            strength_summary = summaries[0].get("strength_text")
            areas_for_growth = summaries[0].get("areas_for_growth_text")
        elif isinstance(summaries, dict):
            strength_summary = summaries.get("strength_text")
            areas_for_growth = summaries.get("areas_for_growth_text")
    
    # Get next steps
    sorted_next_steps = session_service.normalize_ordered_records(
        session.get("next_steps"),
        "next_step_order"
    )
    next_steps = [
        ns.get("title") or ns.get("description_text") or ""
        for ns in sorted_next_steps
    ]
    
    # Total score in DB is 0-100, use it for overall_score in response
    response = SessionDetailResponse(
        session_id=session["id"],
        student_id=session["student_id"],
        status=session["status"],
        interview_type=session.get("type"),
        total_score=session.get("total_score"),
        created_at=session["created_at"],
        completed_at=session.get("completed_at"),
        overall_score=session.get("total_score"),
        strength_summary=strength_summary,
        areas_for_growth=areas_for_growth,
        detailed_feedback=feedback_list if feedback_list else None,
        next_steps=next_steps if next_steps else None
    )
    return JSONResponse(content=jsonable_encoder(response.dict()))



# Initiate route for job prep
# --- ASYNCHRONOUS FLOW - STEP 1: PRODUCER (Initiate & Queue) ---
@router.post("/initiate", 
    response_model=SessionInitiateResponse,
    status_code=status.HTTP_202_ACCEPTED # Returns 202 Accepted immediately
)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def initiate_interview_session(
    request: Request,
    redis_conn: Annotated[redis.Redis, Depends(get_redis_connection)],
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, & TXT)"),
    raw_text: Optional[str] = Form(None, description="Raw text content"),
    field: str = Form(..., description="Target industry/field for the interview."),
    role: str = Form(..., description="Target job role for the interview."),
    role_context: RoleContext = Depends(require_role("student")),
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Initiate new interview session. Saves input data, creates a session in 'pending' status, 
    and pushes the job to the Redis queue for asynchronous processing by the worker.
    Returns 202 Accepted immediately.
    """
    # Initialize services
    storage_service = StorageService(supabase)
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    user_service = UserProfileService(supabase)
    queue_service = QueueService(redis_conn)
    
    session_id: int | None = None
    
    try:
        # Step 0: Validation 
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided"
            )
        if not field or not role:
            raise HTTPException(
                status_code=400,
                detail="Target 'field' and 'role' must be provided for question generation."
            )

        # Step 1: Get student_id from token-derived current_user
        student_details = await user_service.get_student_details(role_context.user.id)
        
        if not student_details:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not associated with a student record"
            )
        student_id = student_details.get("id")
        
        # Step 2: Create session
        # NOTE: Status is set to "pending" instead of the synchronous "in_progress"
        session = await session_service.create_session(
            student_id=student_id,
            status="pending",
            session_type="job"
        )
        session_id = session['id']
        assert session_id is not None, "Session ID must be set after creation"
        
        # Step 3: Process file or use raw_text (Text Extraction)
        cleaned_text_extracted: str
        # --- START FILE PROCESSING LOGIC ---
        if file:
            storage_service.validate_file(file)
            max_size_message = (
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
            content_length_header = request.headers.get("content-length")
            if content_length_header:
                try:
                    content_length = int(content_length_header)
                except ValueError:
                    content_length = None
                else:
                    if content_length and content_length > settings.MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=max_size_message
                        )
            chunk_size = 1024 * 1024 # 1MB
            total_read = 0
            buffer = bytearray()
            while True:
                chunk = await file.read(chunk_size) 
                if not chunk:
                    break
                total_read += len(chunk)
                if total_read > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=max_size_message
                    )
                buffer.extend(chunk)
            file_bytes = bytes(buffer)
            content_type = file.content_type or "application/octet-stream"
            storage_service.verify_file_signature(file_bytes, content_type)
            cleaned_text_extracted = extraction_service.extract_text_from_file(
                file_bytes=file_bytes,
                content_type=content_type
            )
        else:
            if raw_text is None:
                raise HTTPException(status_code=400, detail="raw_text cannot be None")
            cleaned_text_extracted = raw_text
        # --- END FILE PROCESSING LOGIC ---
        
        # Step 4: Save cleaned text to documents table
        document_service.create_document(
            session_id=session_id,
            cleaned_text=cleaned_text_extracted
        )
        
        # Step 5: ENQUEUE THE JOB
        job_payload = {
            "job_type": "interview_generation", # Added job type for future expansion
            "session_id": session_id,
            "student_id": student_id,
            "cv_text": cleaned_text_extracted,
            "field": field,
            "role": role,
            "timestamp": datetime.now().isoformat()
        }
        
        queue_length = queue_service.enqueue_job(job_payload)
        
        # Step 6: Build 202 response
        response = SessionInitiateResponse(
            success=True,
            message=f"Request accepted and queued. Session ID: {session_id}. There are {queue_length - 1} pending jobs ahead of you.",
            session_id=session_id,
            questions=[] # Always empty in async mode
        )
        
        return JSONResponse(content=jsonable_encoder(response.dict()))
        
    except HTTPException:
        _rollback_session_creation(session_service, session_id)
        raise
        
    except Exception as e:
        _rollback_session_creation(session_service, session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue interview session: {str(e)}"
        )
 
# Initiate route for university prep
# --- ASYNCHRONOUS FLOW - STEP 1: PRODUCER (Initiate & Queue) ---
@router.post("/initiate_university_prep", 
    response_model=SessionInitiateResponse,
    status_code=status.HTTP_202_ACCEPTED # Returns 202 Accepted immediately
)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def initiate_university_prep_session(
    request: Request,
    redis_conn: Annotated[redis.Redis, Depends(get_redis_connection)], # ADDED
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    file: Optional[UploadFile] = File(None, description="Student Record/Transcript file (PDF, DOCX, TXT, MD)"),
    raw_text: Optional[str] = Form(None, description="Raw student record text content"),
    universities: str = Form(..., description="Comma-separated list of preferred universities (e.g., 'Stanford, MIT')"),
    departments: str = Form(..., description="Comma-separated list of preferred academic departments (e.g., 'Computer Science, Electrical Engineering')"),
    role_context: RoleContext = Depends(require_role("student"))
):
    """
    Initiate new university preparation session. Saves input data, creates a session in 'pending' status, 
    and pushes the job to the Redis queue for asynchronous processing by the worker.
    Returns 202 Accepted immediately.
    """
    # Initialize services
    storage_service = StorageService(supabase)
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    user_service = UserProfileService(supabase)
    queue_service = QueueService(redis_conn) # ADDED
    
    session_id: int | None = None
    
    try:
        # Step 0: Validate input presence
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided (containing the student record)"
            )
        
        if not universities or not departments:
            raise HTTPException(
                status_code=400,
                detail="Preferred 'universities' and 'departments' must be provided for academic question generation."
            )

        # Step 1: User check
        student_details = await user_service.get_student_details(role_context.user.id)
        if not student_details:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not associated with a student record"
            )
        student_id = student_details.get("id")
        
        # Step 2: Create session with initial 'pending' status (CHANGED from "in_progress")
        session = await session_service.create_session(
            student_id=student_id,
            status="pending",
            session_type="university"
        )
        session_id = session['id']
        assert session_id is not None, "Session ID must be set after creation"
        
        # Step 3: Process file or use raw_text (Text Extraction)
        cleaned_text_extracted: str 
        
        # --- File/Raw Text Processing (Using existing logic) ---
        if file:
            # File provided - process it (ignore raw_text if also provided)
            # Step 3a: Validate file type and filename
            storage_service.validate_file(file)

            # Step 3b: Guard against oversized uploads before loading into memory
            max_size_message = (
                f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
            content_length_header = request.headers.get("content-length")
            if content_length_header:
                try:
                    content_length = int(content_length_header)
                except ValueError:
                    content_length = None
                else:
                    if content_length and content_length > settings.MAX_FILE_SIZE:
                        raise HTTPException(
                            status_code=400,
                            detail=max_size_message
                        )

            # Stream the file in manageable chunks to cap memory usage while reading
            chunk_size = 1024 * 1024 # 1MB
            total_read = 0
            buffer = bytearray()
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_read += len(chunk)
                if total_read > settings.MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=max_size_message
                    )
                buffer.extend(chunk)

            file_bytes = bytes(buffer)
            
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
            if raw_text is None:
                raise HTTPException(status_code=400, detail="raw_text cannot be None")
            cleaned_text_extracted = raw_text
        
        # Step 4: Save cleaned text to documents table
        document = await document_service.create_document(
            session_id=session_id,
            cleaned_text=cleaned_text_extracted
        )
        
        # Step 5: ENQUEUE THE JOB (Replaces all synchronous LLM/RAG/DB steps)
        job_payload = {
            "job_type": "university_generation", # NEW job type
            "session_id": session_id,
            "student_id": student_id,
            "student_record_text": cleaned_text_extracted,
            "universities": universities,
            "departments": departments,
            "timestamp": datetime.now().isoformat()
        }
        
        queue_length = queue_service.enqueue_job(job_payload)
        
        # Step 6: Build 202 response
        response = SessionInitiateResponse(
            success=True,
            # Message confirms the request is queued and gives queue length
            message=f"University Prep request accepted and queued. Session ID: {session_id}. There are {queue_length - 1} pending jobs ahead of you.",
            session_id=session_id,
            questions=[] # Always empty in async mode
        )
        
        return JSONResponse(content=jsonable_encoder(response.dict()))
        
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
            detail=f"Failed to queue university prep session: {str(e)}"
        )
    

async def _rollback_session_creation(
    session_service: InterviewSessionService,
    session_id: int | None = None
):
    """
    Rollback changes if session initiation fails.
    """
    # Mark session as failed (keep for debugging, don't delete)
    if session_id:
        try:
            await session_service.update_session_status(session_id, status="failed")
        except Exception as e:
            print(f"Warning: Failed to update session status during rollback: {str(e)}")