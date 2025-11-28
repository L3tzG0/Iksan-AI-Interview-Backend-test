from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.core.security import get_current_user
from app.schemas.student import StudentResponse, StudentCreate
from app.schemas.interview_session import SessionHistoryItem, SessionHistoryResponse, SessionDetailResponse, FeedbackDetail

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
def read_students(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all students"""
    response = supabase.table('students').select('*').execute()
    return response.data

@router.post("/", response_model=StudentResponse)
def create_student(
    student_in: StudentCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass


@router.get("/{student_id}/sessions", response_model=SessionHistoryResponse)
def get_student_sessions(
    student_id: int,
    current_user = Depends(get_current_user),
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    """
    Get a specific student's interview session history.
    
    This endpoint is for teachers/admins to view a student's session history.
    Requires: Authentication (JWT token) - should be teacher or admin role
    
    Parameters:
    - student_id: The ID of the student whose sessions to retrieve
    
    Returns: List of session history with dummy data (skeleton implementation)
    """
    # TODO: Verify current_user is teacher or admin
    # TODO: Fetch actual session data for the specified student_id
    # For now, return dummy data
    
    dummy_sessions = [
        SessionHistoryItem(
            id=101,
            status="completed",
            total_score=88.0,
            completed_at=datetime(2025, 11, 22, 15, 30, 0),
            created_at=datetime(2025, 11, 22, 15, 0, 0)
        ),
        SessionHistoryItem(
            id=102,
            status="completed",
            total_score=76.5,
            completed_at=datetime(2025, 11, 18, 11, 45, 0),
            created_at=datetime(2025, 11, 18, 11, 0, 0)
        ),
        SessionHistoryItem(
            id=103,
            status="failed",
            total_score=None,
            completed_at=None,
            created_at=datetime(2025, 11, 10, 9, 30, 0)
        ),
        SessionHistoryItem(
            id=104,
            status="completed",
            total_score=91.2,
            completed_at=datetime(2025, 11, 5, 14, 20, 0),
            created_at=datetime(2025, 11, 5, 14, 0, 0)
        ),
    ]
    
    return SessionHistoryResponse(
        sessions=dummy_sessions,
        total_count=len(dummy_sessions)
    )


@router.get("/{student_id}/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session_detail(
    student_id: int,
    session_id: int,
    current_user = Depends(get_current_user),
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    """
    Get detailed view of a specific student's session.
    
    This endpoint returns the complete session details including feedback.
    Requires: Authentication (JWT token) - should be teacher or admin role
    
    Parameters:
    - student_id: The ID of the student
    - session_id: The ID of the specific session
    
    Returns: Detailed session information with feedback (dummy data for skeleton)
    """
    # TODO: Verify current_user is teacher or admin
    # TODO: Fetch actual session and feedback data
    # For now, return dummy data
    
    dummy_detailed_feedback = [
        FeedbackDetail(
            question="자기소개를 해주세요.",
            answer="안녕하세요, 저는 컴퓨터공학을 전공하고 있는 학생입니다.",
            evaluation="명확하고 간결한 자기소개입니다. 전공 분야를 잘 언급했습니다.",
            score=8.5,
            is_correct=True
        ),
        FeedbackDetail(
            question="왜 이 직무에 지원하셨나요?",
            answer="개발에 대한 열정이 있고, 실무 경험을 쌓고 싶습니다.",
            evaluation="동기는 좋으나 좀 더 구체적인 이유를 제시하면 좋겠습니다.",
            score=7.0,
            is_correct=True
        ),
    ]
    
    return SessionDetailResponse(
        session_id=session_id,
        student_id=student_id,
        status="completed",
        total_score=88.0,
        created_at=datetime(2025, 11, 22, 15, 0, 0),
        completed_at=datetime(2025, 11, 22, 15, 30, 0),
        overall_score=88.0,
        strength_summary="명확한 의사소통 능력과 기본적인 기술 지식을 보여주셨습니다.",
        areas_for_growth="답변에 구체적인 예시와 수치를 포함하면 더 설득력이 있을 것입니다.",
        detailed_feedback=dummy_detailed_feedback,
        next_steps=[
            "STAR 기법을 활용한 답변 연습하기",
            "프로젝트 경험에 대한 구체적인 수치와 성과 정리하기"
        ]
    )
