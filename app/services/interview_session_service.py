from datetime import datetime
from typing import Optional, Tuple, List
from operator import itemgetter
from supabase import Client
from fastapi import HTTPException, status

# Explicit columns to select for sessions (avoiding SELECT *)
SESSION_COLUMNS = "id, student_id, status, total_score, completed_at, created_at"
SESSION_COLUMNS_WITH_DETAILS = """
    id, student_id, status, total_score, completed_at, created_at,
    students(id, user_id, school_id, major_id,
        user_profiles(id, full_name, email),
        schools(id, school_name),
        majors(id, major_name)
    )
"""
SESSION_WITH_FEEDBACKS = """
    id, student_id, status, total_score, completed_at, created_at,
    detailed_feedbacks(
        id, question_order, question_text, answer_text, evaluation_text,
        is_correct, content_relevance_score, structure_score, 
        fluency_score, confidence_score, overall_score
    ),
    summaries(id, strength_text, areas_for_growth_text),
    next_steps(id, next_step_order, title, description_text)
"""


class InterviewSessionService:
    """Service for handling interview session database operations"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def create_session(self, student_id: int, status: str = "in_progress") -> dict:
        """
        Create new interview session
        
        Args:
            student_id: ID of the student
            status: Initial status (default: "in_progress")
        
        Returns:
            dict: Created session record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            session_data = {
                "student_id": student_id,
                "status": status
            }
            
            response = self.supabase.table('sessions').insert(session_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create session record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating session: {str(e)}"
            )
    
    def update_session_status(
        self, 
        session_id: int, 
        status: str,
        completed_at: Optional[datetime] = None,
        total_score: Optional[float] = None
    ) -> dict:
        """
        Update session status and related fields
        
        Args:
            session_id: Session ID
            status: New status value
            completed_at: Completion timestamp (optional)
            total_score: Total score (optional)
        
        Returns:
            dict: Updated session record
        
        Raises:
            HTTPException: If update fails
        """
        try:
            update_data = {"status": status}
            
            if completed_at:
                update_data["completed_at"] = completed_at.isoformat()
            if total_score is not None:
                update_data["total_score"] = total_score
            
            response = self.supabase.table('sessions').update(update_data).eq('id', session_id).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session with id {session_id} not found"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update session: {str(e)}"
            )
    
    def delete_session(self, session_id: int) -> bool:
        """
        Delete session (hard delete for rollback)
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            bool: True if successful
        
        Raises:
            HTTPException: If deletion fails
        """
        try:
            response = self.supabase.table('sessions').delete().eq('id', session_id).execute()
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}"
            )
    
    def get_session(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID with explicit column selection
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session record if found
        """
        try:
            response = self.supabase.table('sessions').select(SESSION_COLUMNS).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session: {str(e)}"
            )

    def get_session_by_id(self, session_id: int, student_id: int) -> Optional[dict]:
        """
        NEW: Get session by ID AND student_id (for authorization checks).
        
        Args:
            session_id: The ID of the session.
            student_id: The ID of the student (user) who owns the session.
            
        Returns:
            dict or None: The session record if found and owned by the student.
        """
        try:
            response = self.supabase.table('sessions').select(SESSION_COLUMNS)\
                .eq('id', session_id)\
                .eq('student_id', student_id)\
                .limit(1)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session for status check: {str(e)}"
            )
        
    def get_session_with_details(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID with student and related info (single query).
        Uses relational select to avoid N+1 queries.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested student details
        """
        try:
            response = self.supabase.table('sessions').select(
                SESSION_COLUMNS_WITH_DETAILS
            ).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session with details: {str(e)}"
            )

    def get_session_with_feedbacks(self, session_id: int) -> Optional[dict]:
        """
        Get session with all feedbacks, summary, and next steps in single query.
        Uses relational select to avoid N+1 queries.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested feedback data
        """
        try:
            response = self.supabase.table('sessions').select(
                SESSION_WITH_FEEDBACKS
            ).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session with feedbacks: {str(e)}"
            )

    def get_sessions_by_student(
        self,
        student_id: int,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get all sessions for a student with pagination.
        
        Args:
            student_id: Student ID
            skip: Number of records to skip
            limit: Maximum records to return
            status_filter: Filter by status (completed, in_progress, failed)
        
        Returns:
            Tuple of (list of sessions, total count)
        """
        try:
            query = self.supabase.table('sessions').select(
                SESSION_COLUMNS, count='exact'
            ).eq('student_id', student_id)
            
            if status_filter:
                query = query.eq('status', status_filter)
            
            # Order by most recent first
            query = query.order('created_at', desc=True)
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch student sessions: {str(e)}"
            )

    def get_all_sessions(
        self,
        skip: int = 0,
        limit: int = 20,
        student_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        with_student: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all sessions with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            student_id: Filter by student ID
            status_filter: Filter by status
            with_student: Include student details
        
        Returns:
            Tuple of (list of sessions, total count)
        """
        try:
            columns = SESSION_COLUMNS_WITH_DETAILS if with_student else SESSION_COLUMNS
            
            query = self.supabase.table('sessions').select(columns, count='exact')
            
            if student_id is not None:
                query = query.eq('student_id', student_id)
            if status_filter:
                query = query.eq('status', status_filter)
            
            query = query.order('created_at', desc=True)
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch sessions: {str(e)}"
            )

    @staticmethod
    def build_history_payloads(sessions: List[dict]) -> List[dict]:
        """Create lightweight session payloads for history responses without validation overhead."""
        return [
            {
                "id": session["id"],
                "status": session["status"],
                "total_score": session.get("total_score"),
                "completed_at": session.get("completed_at"),
                "created_at": session["created_at"]
            }
            for session in sessions
        ]

    @staticmethod
    def normalize_ordered_records(records: Optional[List[dict]], key: str) -> List[dict]:
        """Return records sorted by key while defaulting missing order values to zero."""
        if not records:
            return []

        normalized: List[dict] = []
        for record in records:
            order_value = record.get(key)
            if order_value is None:
                normalized.append({**record, key: 0})
            else:
                normalized.append(record)

        return sorted(normalized, key=itemgetter(key))
