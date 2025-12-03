import asyncio # Import needed for async calls
from typing import List, Annotated, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from supabase import AsyncClient
from app.core.database import get_supabase
from app.core.config import settings
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.api.dependencies import require_role

# New service imports (replacing LLMService)
from app.services.question_generator import generate_interview_questions
from app.services.evaluation_generator import generate_session_evaluation

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
    GeneratedQuestion,
    QuestionAnswerPair # Needed for safely referencing the data structure
)
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.storage_service import StorageService
from app.services.document_service import DocumentService
from app.services.interview_session_service import InterviewSessionService
from app.services.text_extraction_service import TextExtractionService
from app.services.feedback_service import FeedbackService
from app.services.user_service import UserProfileService
# from app.services.llm_service import LLMService # REMOVED
from app.schemas.summary import InterviewSummaryCreate # Explicitly import the schema
from app.schemas.next_step import InterviewNextStepCreate


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


@router.post("/submit", response_model=SessionFeedbackResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def submit_session_answers(
    request: Request,
    submit_request: SessionSubmitRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Submit answers and get complete feedback from LLM.
    
    FE submits the complete QnA history, and this endpoint will:
    1. Validate and fetch existing session (must be in_progress)
    2. Call LLM with the whole QnA history and get feedback
    3. Update the database with scores, summaries, next steps, and detailed feedback
    4. Update session status to "completed" or "failed"
    5. Return the complete feedback response
    """
    session_service = InterviewSessionService(supabase)
    feedback_service = FeedbackService(supabase)
    user_service = UserProfileService(supabase)
    
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
         await session_service.update_session_status(session_id, status="completed", total_score=0.0)
         raise HTTPException(
            status_code=400, 
            detail="No question and answer pairs provided for evaluation."
        )

    try:
        # 2. Call LLM Evaluation Service
        # submit_request.qa_pairs is List[QuestionAnswerPair], which the service expects
        evaluation_result = await generate_session_evaluation(submit_request.qa_pairs)

        # 3. Update Database with results
        
        # A. Update main session table with overall score (scaling from 0-10 to 0-100)
        overall_score_10 = round(evaluation_result.overall_scores.overall_score, 1)

        await session_service.update_session_status(
            session_id=session_id, 
            status="completed",
            total_score=overall_score_10,
            completed_at=datetime.now()
        )
        
        # B. Save summaries
        summary_data = InterviewSummaryCreate(
            session_id=session_id,
            strength_text=evaluation_result.session_summary.strength_text,
            areas_for_growth_text=evaluation_result.session_summary.areas_for_growth_text
        )
        
        # Now pass the single Pydantic object to the service method
        await feedback_service.create_session_summary(summary=summary_data)

        # C. Save next steps
        next_step_creates = [
            InterviewNextStepCreate(
                session_id=session_id,
                next_step_order=idx + 1, # Use index here for order
                title=ns.title,
                description_text=ns.description_text
            )
            for idx, ns in enumerate(evaluation_result.next_steps)
        ]

        await feedback_service.create_next_steps_batch(
            next_steps=next_step_creates # Pass the mapped list of objects
        )

         # D. Update detailed feedbacks (Q&A and scores)
        # 1. Create a map of question_order to answer_text from the request
        qa_map = {p.question_order: p.answer_text for p in submit_request.qa_pairs}
        
        # 2. Merge answer_text into the LLM's per-question feedback structure
        combined_feedback_updates = []
        for fb_item in evaluation_result.per_question_feedback:
            # Convert the Pydantic object to a mutable dictionary
            # We use model_dump() here to include all the LLM-generated fields (scores/evaluation_text)
            update_data = fb_item.model_dump(exclude_none=True, exclude_unset=True)
            
            # Look up the corresponding answer text using the question order
            answer_text_for_q = qa_map.get(fb_item.question_order)
            
            # Add the answer_text to the update payload
            if answer_text_for_q is not None:
                update_data["answer_text"] = answer_text_for_q
            
            combined_feedback_updates.append(update_data)

        # 3. Send the updated list of dictionaries (which now includes answer_text) to the service
        await feedback_service.update_detailed_feedbacks_batch(
            session_id=session_id,
            # We pass a list of dicts/Any, which is handled in the service
            feedback_updates=combined_feedback_updates 
        )
        # 4. Construct final response model
        
        # Helper map to link feedback (which lacks Q&A text) back to the input request
        qa_map = {p.question_order: (p.question_text, p.answer_text) for p in submit_request.qa_pairs}
        detailed_feedback_list = []

        for fb in evaluation_result.per_question_feedback:
            # Skip placeholder feedback items from the LLM (unanswered questions)
            if fb.evaluation_text == "Question not answered by the candidate.":
                 continue
            
            # Get the original Q&A text from the request body
            q_text, a_text = qa_map.get(
                fb.question_order, 
                (f"Question {fb.question_order} (Unanswered)", "N/A")
            )
            
            detailed_feedback_list.append(
                FeedbackDetail(
                    question=q_text,
                    answer=a_text,
                    evaluation=fb.evaluation_text,
                    content_relevance_score=fb.content_relevance_score,
                    structure_score=fb.structure_score,
                    fluency_score=fb.fluency_score,
                    confidence_score=fb.confidence_score,
                    overall_score=fb.overall_score,
                    is_correct=fb.is_correct
                )
            )
        
        response_payload = SessionFeedbackResponse(
            session_id=session_id,
            overall_score=overall_score_10,
            strength_summary=evaluation_result.session_summary.strength_text,
            areas_for_growth=evaluation_result.session_summary.areas_for_growth_text,
            detailed_feedback=detailed_feedback_list,
            next_steps=[ns.title or ns.description_text for ns in evaluation_result.next_steps]
        )
        
        # 5. Return success response
        return JSONResponse(content=jsonable_encoder(response_payload.dict()))

    except Exception as e:
        # 6. Handle errors and rollback status
        error_detail = str(e)
        # Ensure the session is marked as failed on error
        await session_service.update_session_status(session_id, status="failed")
        print(f"Error during session evaluation (ID: {session_id}): {e}")
        
        raise HTTPException(
            status_code=500,
            detail=f"AI Session Evaluation or Database Update failed. Error: {error_detail}"
        )


@router.get("/{session_id}", response_model=SessionDetailResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_session_detail(
    request: Request,
    session_id: int,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
    session = await session_service.get_session_with_feedbacks(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify current user owns this session (get student details)
    student_details = await user_service.get_student_details(current_user.id)
    if student_details and student_details.get("id") != session.get("student_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own sessions"
        )
    
    # Transform detailed_feedbacks from database format
    sorted_feedbacks = session_service.normalize_ordered_records(
        session.get("detailed_feedbacks"),
        "question_order"
    )
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
        for fb in sorted_feedbacks
        if fb.get("overall_score") is not None and fb.get("overall_score") > 0.0 # Only show evaluated items
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


@router.post("/initiate", response_model=SessionInitiateResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def initiate_interview_session(
    request: Request,
    file: Optional[UploadFile] = File(None, description="Document file (PDF, DOCX, TXT, MD)"),
    raw_text: Optional[str] = Form(None, description="Raw text content"),
    # ADDED: Required for targeted question generation
    field: str = Form(..., description="Target industry/field for the interview."),
    role: str = Form(..., description="Target job role for the interview."),
    current_user = Depends(require_role("student")),
    supabase: AsyncClient = Depends(get_supabase)
):
    """
    Initiate new interview session by processing document text or raw text.
    
    Requires: Authentication (JWT token) - Student role only
    Rate limited: 10 requests per minute per user.
    """
    # Initialize services
    storage_service = StorageService(supabase) # Used for validation only
    session_service = InterviewSessionService(supabase)
    document_service = DocumentService(supabase)
    extraction_service = TextExtractionService()
    feedback_service = FeedbackService(supabase)
    # llm_service removed
    user_service = UserProfileService(supabase)
    
    session_id: int | None = None
    
    try:
        # Step 0: Validate that at least one of file or raw_text is provided
        if not file and not raw_text:
            raise HTTPException(
                status_code=400,
                detail="Either 'file' or 'raw_text' must be provided"
            )
        
        # Validate field and role are not empty
        if not field or not role:
            raise HTTPException(
                status_code=400,
                detail="Target 'field' and 'role' must be provided for question generation."
            )

        # Step 1: Get student_id from token-derived current_user
        student_details = await user_service.get_student_details(current_user.id)
        
        if not student_details:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Current user is not associated with a student record"
            )
        
        student_id = student_details.get("id")
        
        # Step 2: Create session
        session = await session_service.create_session(student_id=student_id, status="in_progress")
        session_id = session['id']
        
        # Ensure session_id is set (type narrowing)
        assert session_id is not None, "Session ID must be set after creation"
        
        # Step 3: Process file or use raw_text
        cleaned_text_extracted: str
        
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
        
        # Step 5: Generate interview questions using LLM (using the new service)
        # Service returns List[GeneratedQuestion]
        generated_questions_list = await generate_interview_questions(
            cv_text=cleaned_text_extracted,
            field=field,
            role=role
        )
        
        # Step 6: Create detailed_feedbacks records (10 rows with questions)
        # This step uses the list of Pydantic models (correct).
        await feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        # Step 7: Build response with all generated questions
        # The redundant loop from before has been removed. We use the list directly.
        response = SessionInitiateResponse(
            success=True,
            message="Interview session initiated successfully with 10 questions",
            session_id=session['id'],
            # Directly use the list of GeneratedQuestion objects from the service
            questions=generated_questions_list
        )
        
        # FastAPI's jsonable_encoder correctly converts the List[GeneratedQuestion] 
        # objects into List[dict] for the JSON response body.
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
            detail=f"Failed to initiate interview session: {str(e)}"
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