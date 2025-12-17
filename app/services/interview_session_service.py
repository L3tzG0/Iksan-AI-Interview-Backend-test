from datetime import datetime
from typing import Optional, Tuple, List
from operator import itemgetter
from supabase import AsyncClient
from fastapi import HTTPException, status
from app.utils.pagination import paginate_query

# Explicit columns to select for sessions (avoiding SELECT *)
SESSION_COLUMNS = "id, student_id, status, type, total_score, completed_at, created_at"
SESSION_COLUMNS_WITH_DETAILS = """
    id, student_id, status, type, total_score, completed_at, created_at,
    students(id, user_id, school_id, major_id,
        user_profiles(id, full_name, email),
        schools(id, school_name),
        majors(id, major_name)
    )
"""
SESSION_COLUMNS_WITH_STUDENT_INFO = """
    id, status, type, total_score, completed_at, created_at,
    students!inner(
        id, student_id, school_id,
        user_profiles(full_name),
        schools(id, school_name),
        majors(id, major_name),
        classes(id, class_name, grade_level)
    )
"""
SESSION_WITH_FEEDBACKS = """
    id, student_id, status, type, total_score, completed_at, created_at,
    detailed_feedbacks(
        id, question_order, question_text, answer_text, evaluation_text,
        is_correct, content_relevance_score, structure_score, 
        fluency_score, confidence_score, overall_score
    ),
    summaries(id, strength_text, areas_for_growth_text),
    next_steps(id, next_step_order, title, description_text)
"""

ALLOWED_SESSION_TYPES = {"job", "university"}


class InterviewSessionService:
    """Service for handling interview session database operations"""
    
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    @staticmethod
    def _normalize_interview_type(interview_type: Optional[str]) -> Optional[str]:
        """Lowercase and validate provided interview type."""
        if interview_type is None:
            return None

        normalized = interview_type.lower()
        if normalized not in ALLOWED_SESSION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interview_type '{interview_type}'. Must be one of: {', '.join(sorted(ALLOWED_SESSION_TYPES))}."
            )
        return normalized
    
    async def create_session(self, student_id: int, status: str = "in_progress", session_type: str = "job") -> dict:
        """
        Create new interview session
        
        Args:
            student_id: ID of the student
            status: Initial status (default: "in_progress")
            session_type: Session type (job or university)
        
        Returns:
            dict: Created session record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            allowed_types = {"job", "university"}
            if session_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid session type '{session_type}'. Must be one of: {', '.join(sorted(allowed_types))}."
                )

            session_data = {
                "student_id": student_id,
                "status": status,
                "type": session_type
            }
            
            response = await self.supabase.table('sessions').insert(session_data).execute()
            
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
    
    async def update_session_status(
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
            
            response = await self.supabase.table('sessions').update(update_data).eq('id', session_id).execute()
            
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
    
    async def delete_session(self, session_id: int) -> bool:
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
            response = await self.supabase.table('sessions').delete().eq('id', session_id).execute()
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}"
            )
    
    async def get_session(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID with explicit column selection
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session record if found
        """
        try:
            response = await self.supabase.table('sessions').select(SESSION_COLUMNS).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session: {str(e)}"
            )

    async def get_session_with_details(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID with student and related info (single query).
        Uses relational select to avoid N+1 queries.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested student details
        """
        try:
            response = await self.supabase.table('sessions').select(
                SESSION_COLUMNS_WITH_DETAILS
            ).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session with details: {str(e)}"
            )

    async def get_session_with_feedbacks(self, session_id: int) -> Optional[dict]:
        """
        Get session with all feedbacks, summary, and next steps in single query.
        Uses relational select to avoid N+1 queries.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested feedback data
        """
        try:
            response = await self.supabase.table('sessions').select(
                SESSION_WITH_FEEDBACKS
            ).eq('id', session_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session with feedbacks: {str(e)}"
            )

    async def get_sessions_by_student(
        self,
        student_id: int,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
        interview_type: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get all sessions for a student with pagination.
        
        Args:
            student_id: Student ID
            skip: Number of records to skip
            limit: Maximum records to return
            status_filter: Filter by status (completed, in_progress, failed)
            interview_type: Filter by interview type (job, university)
        
        Returns:
            Tuple of (list of sessions, total count)
        """
        try:
            normalized_type = self._normalize_interview_type(interview_type)

            def build_query():
                base_query = self.supabase.table('sessions').select(
                    SESSION_COLUMNS, count='exact'
                ).eq('student_id', student_id)
                if status_filter:
                    base_query = base_query.eq('status', status_filter)
                if normalized_type:
                    base_query = base_query.eq('type', normalized_type)
                return base_query.order('created_at', desc=True)

            return await paginate_query(build_query, skip, limit)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch student sessions: {str(e)}"
            )

    async def get_all_sessions(
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

            def build_query():
                base_query = self.supabase.table('sessions').select(columns, count='exact')
                if student_id is not None:
                    base_query = base_query.eq('student_id', student_id)
                if status_filter:
                    base_query = base_query.eq('status', status_filter)
                return base_query.order('created_at', desc=True)

            return await paginate_query(build_query, skip, limit)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch sessions: {str(e)}"
            )

    async def get_sessions_with_student_info(
        self,
        skip: int = 0,
        limit: int = 20,
        status_filter: Optional[str] = None,
        school_id: Optional[int] = None,
        interview_type: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get sessions with student context for admin/teacher views.

        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            status_filter: Optional session status filter
            school_id: Optional school scoping (teachers)
            interview_type: Optional interview type filter

        Returns:
            Tuple of (list of sessions, total count)
        """
        try:
            normalized_type = self._normalize_interview_type(interview_type)

            def build_query():
                base_query = self.supabase.table('sessions').select(
                    SESSION_COLUMNS_WITH_STUDENT_INFO,
                    count='exact'
                )
                if status_filter:
                    base_query = base_query.eq('status', status_filter)
                if school_id is not None:
                    base_query = base_query.eq('students.school_id', school_id)
                if normalized_type:
                    base_query = base_query.eq('type', normalized_type)
                return base_query.order('created_at', desc=True)

            return await paginate_query(build_query, skip, limit)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch sessions with student info: {str(e)}"
            )

    @staticmethod
    def build_history_payloads(sessions: List[dict]) -> List[dict]:
        """Create lightweight session payloads for history responses without validation overhead."""
        return [
            {
                "id": session["id"],
                "status": session["status"],
                "interview_type": session.get("type"),
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

    @staticmethod
    def shape_session_with_student_info(session: dict, include_school: bool = False) -> dict:
        """Map raw session record to admin/teacher response shape."""
        student = session.get("students") if isinstance(session, dict) else None
        if isinstance(student, list):
            student = student[0] if student else None

        profile = None
        school = None
        major = None
        class_info = None
        if isinstance(student, dict):
            profile = student.get("user_profiles")
            school = student.get("schools")
            major = student.get("majors")
            class_info = student.get("classes")

        if isinstance(profile, list):
            profile = profile[0] if profile else None
        if isinstance(school, list):
            school = school[0] if school else None
        if isinstance(major, list):
            major = major[0] if major else None
        if isinstance(class_info, list):
            class_info = class_info[0] if class_info else None

        return {
            "session_id": session.get("id"),
            "interview_type": session.get("type"),
            "student_name": profile.get("full_name") if isinstance(profile, dict) else None,
            "student_identifier": student.get("student_id") if isinstance(student, dict) else None,
            "school_name": school.get("school_name") if include_school and isinstance(school, dict) else None,
            "major_name": major.get("major_name") if isinstance(major, dict) else None,
            "class_name": class_info.get("class_name") if isinstance(class_info, dict) else None,
            "grade_level": class_info.get("grade_level") if isinstance(class_info, dict) else None,
            "total_score": session.get("total_score"),
            "status": session.get("status"),
            "completed_at": session.get("completed_at"),
            "created_at": session.get("created_at"),
        }
