from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from supabase import AsyncClient
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.schemas.student import (
    StudentAccountCreate, 
    StudentAccountResponse,
    StudentBulkCreateRequest,
    StudentBulkCreateResponse,
    StudentDetailResponse
)
from app.schemas.interview_session import SessionHistoryItem, SessionHistoryResponse, SessionDetailResponse as InterviewSessionDetailResponse, FeedbackDetail
from app.services.student_service import StudentService
from app.services.student_registration_service import StudentRegistrationService
from app.services.interview_session_service import InterviewSessionService

router = APIRouter()


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


@router.get("/{student_id}/sessions/{session_id}", response_model=InterviewSessionDetailResponse)
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
    
    return InterviewSessionDetailResponse(
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



@router.post("/create", response_model=StudentAccountResponse)
async def create_student_account(
    student_account_in: StudentAccountCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Create a new student account with auto-generated student ID and password.
    
    Requires: Teacher or Admin role
    
    The student ID is auto-generated as a 12-digit number:
    - 3 digits: school_number
    - 4 digits: major_number  
    - 5 digits: sequential student_number
    
    Password is auto-generated with 8+ characters including uppercase, 
    lowercase, digit, and symbol.
    
    Parameters:
    - full_name: Student's full name (required)
    - school_name: School name (creates if not exists)
    - major_name: Major name (creates if not exists)
    - class_name: Class name (required with grade_level to assign class)
    - grade_level: Grade level for the class
    - class_id: Alternative - use existing class ID
    
    Returns: The created student account with credentials
    """
    # Get user's role from user_profiles table
    # The alternative of extending the dependency would add complexity and 
    # potentially a second query anyway (dependency would need to fetch the role), 
    # so this direct approach is cleaner.
    profile_response = await supabase.table("user_profiles").select("role_id").eq("id", str(current_user.id)).single().execute()
    
    if not profile_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile not found"
        )
    
    role_id = profile_response.data.get("role_id")
    # role_id 1 = admin, role_id 2 = teacher
    if role_id not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create student accounts"
        )
    
    # Get teacher's school_id if they are a teacher
    creator_school_id = None
    if role_id == 2:  # Teacher
        teacher_response = await supabase.table("teachers").select("school_id").eq("user_id", str(current_user.id)).single().execute()
        if teacher_response.data:
            creator_school_id = teacher_response.data.get("school_id")
    
    registration_service = StudentRegistrationService(supabase)
    
    try:
        result = await registration_service.create_student_account(
            student_account_in,
            creator_school_id=creator_school_id
        )
        
        # Service returns StudentAccountResponse directly
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student account: {str(e)}"
        )



@router.post("/bulk-create", response_model=StudentBulkCreateResponse)
async def bulk_create_student_accounts(
    request: StudentBulkCreateRequest,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    current_user = Depends(get_current_user)
):
    """
    Create multiple student accounts in a single transaction.
    
    Requires: Teacher or Admin role
    
    All-or-nothing: If any student creation fails, the entire batch is rolled back.
    
    Each student gets:
    - Auto-generated 12-digit student ID
    - Auto-generated secure password
    - Supabase auth account (using fake email pattern for username login)
    
    Parameters:
    - students: List of student account creation requests
    
    Returns: 
    - students: List of created student accounts with credentials
    - created_count: Number of successfully created accounts
    """
    
    # Get user's role from user_profiles table
    # The alternative of extending the dependency would add complexity and 
    # potentially a second query anyway (dependency would need to fetch the role), 
    # so this direct approach is cleaner.
    profile_response = await supabase.table("user_profiles").select("role_id").eq("id", str(current_user.id)).single().execute()
    
    if not profile_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User profile not found"
        )
    
    role_id = profile_response.data.get("role_id")
    # role_id 1 = admin, role_id 2 = teacher
    if role_id not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers and admins can create student accounts"
        )
    
    if not request.students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one student must be provided"
        )
    
    if len(request.students) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 students can be created at once"
        )
    
    registration_service = StudentRegistrationService(supabase)
    
    try:
        results = await registration_service.bulk_create_student_accounts(request.students)
        
        # results is already a list of StudentAccountResponse objects
        return StudentBulkCreateResponse(
            students=results,
            created_count=len(results)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student accounts: {str(e)}"
        )

