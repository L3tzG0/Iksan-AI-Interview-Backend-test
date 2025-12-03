from typing import List, Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from supabase import AsyncClient
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.schemas.student import StudentResponse, StudentCreate, StudentUpdate
from app.schemas.interview_session import SessionHistoryItem, SessionHistoryResponse, SessionDetailResponse, FeedbackDetail
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.student_service import StudentService
from app.services.interview_session_service import InterviewSessionService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[StudentResponse])
async def read_students(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    student_id: Optional[str] = Query(default=None, description="Filter by student ID number (partial match)"),
    school_id: Optional[int] = Query(default=None, description="Filter by school ID"),
    major_id: Optional[int] = Query(default=None, description="Filter by major ID"),
    class_id: Optional[int] = Query(default=None, description="Filter by class ID"),
    with_details: bool = Query(default=False, description="Include school/major/class details")
):
    """
    Get all students with pagination and optional filtering.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **student_id**: Filter by student ID number (partial match)
    - **school_id**: Filter by school
    - **major_id**: Filter by major
    - **class_id**: Filter by class
    - **with_details**: Include related school/major/class info
    """
    service = StudentService(supabase)
    students, total = await service.get_all_students(
        skip=skip,
        limit=limit,
        student_id_filter=student_id,
        school_id=school_id,
        major_id=major_id,
        class_id=class_id,
        with_details=with_details
    )
    return create_paginated_response(items=students, total=total, skip=skip, limit=limit)


@router.get("/by-student-id/{student_id_number}", response_model=StudentResponse)
async def get_student_by_student_id(
    student_id_number: str,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Get a student by their student ID number (not the primary key).
    
    - **student_id_number**: The student's ID number (e.g., school-issued ID)
    """
    service = StudentService(supabase)
    return await service.get_student_by_student_id(student_id_number)


@router.post("/", response_model=StudentResponse)
async def create_student(
    student_in: StudentCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Create a new student record.
    
    Note: Students are typically created via the registration endpoint.
    This endpoint is for administrative purposes.
    """
    service = StudentService(supabase)
    return await service.create_student(student_in)


@router.patch("/{id}", response_model=StudentResponse)
async def update_student(
    id: int,
    student_in: StudentUpdate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """
    Update a student's information.
    
    - **id**: The primary key ID of the student record
    """
    service = StudentService(supabase)
    return await service.update_student(id, student_in)


@router.get("/{student_id}/sessions", response_model=SessionHistoryResponse)
async def get_student_sessions(
    student_id: int,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status (completed, in_progress, failed)")
):
    """
    Get a specific student's interview session history.
    
    This endpoint is for teachers/admins to view a student's session history.
    Requires: Authentication (JWT token) - should be teacher or admin role
    
    Parameters:
    - student_id: The ID of the student whose sessions to retrieve
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **status_filter**: Filter by session status
    
    Returns: Paginated list of session history
    """
    # TODO: Verify current_user is teacher or admin
    
    # Verify student exists
    student_service = StudentService(supabase)
    await student_service.get_student(student_id)  # Raises 404 if not found
    
    # Fetch actual session data with pagination
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
    
    return SessionHistoryResponse(
        sessions=session_items,
        total_count=total
    )


@router.get("/{student_id}/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    student_id: int,
    session_id: int,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Get detailed view of a specific student's session.
    
    This endpoint returns the complete session details including feedback.
    Uses relational select to fetch all data in single query.
    Requires: Authentication (JWT token) - should be teacher or admin role
    
    Parameters:
    - student_id: The ID of the student
    - session_id: The ID of the specific session
    
    Returns: Detailed session information with feedback
    """
    # TODO: Verify current_user is teacher or admin
    
    session_service = InterviewSessionService(supabase)
    
    # Get the session with all related data in single query
    session = await session_service.get_session_with_feedbacks(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify session belongs to the specified student
    if session.get("student_id") != student_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found for this student"
        )
    
    # Transform detailed_feedbacks from database format
    sorted_feedbacks = session_service.normalize_ordered_records(
        session.get("detailed_feedbacks"),
        "question_order"
    )
    feedback_list = [
        FeedbackDetail(
            question=fb.get("question_text", ""),
            answer=fb.get("answer_text", ""),
            evaluation=fb.get("evaluation_text", ""),
            content_relevance_score=fb.get("content_relevance_score"),
            structure_score=fb.get("structure_score"),
            fluency_score=fb.get("fluency_score"),
            confidence_score=fb.get("confidence_score"),
            overall_score=fb.get("overall_score"),
            is_correct=fb.get("is_correct", False)
        )
        for fb in sorted_feedbacks
    ]
    
    # Get summary data
    summaries = session.get("summaries")
    strength_summary = None
    areas_for_growth = None
    if summaries:
        if isinstance(summaries, list) and len(summaries) > 0:
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
        ns.get("title", "") or ns.get("description_text", "")
        for ns in sorted_next_steps
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
