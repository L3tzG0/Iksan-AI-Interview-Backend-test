from datetime import datetime
from typing import Optional, Tuple, List, NamedTuple, Dict, Any
from operator import itemgetter
from supabase import AsyncClient
from fastapi import HTTPException, status
from app.utils.pagination import paginate_query

class CalculatedAverages(NamedTuple):
    """The four calculated dimension averages for a session."""
    avg_cr: float
    avg_st: float
    avg_fl: float
    avg_cp: float

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

    async def get_latest_sessions_per_student(
        self,
        skip: int = 0,
        limit: int = 20,
        school_id: Optional[int] = None,
        interview_type: Optional[str] = None
    ) -> Tuple[List[dict], int]:
        """
        Get the latest non-failed session for each student.
        
        Args:
            skip: Number of records to skip (applied after grouping)
            limit: Maximum records to return
            school_id: Optional school scoping (for teachers)
            interview_type: Optional interview type filter (job, university)
        
        Returns:
            Tuple of (list of latest sessions per student, total count)
        """
        try:
            normalized_type = self._normalize_interview_type(interview_type)
            
            # Build base query
            base_query = self.supabase.table('sessions').select(
                SESSION_COLUMNS_WITH_STUDENT_INFO,
                count='exact'
            ).neq('status', 'failed').order('created_at', desc=True)
            
            # Apply school filter if provided
            if school_id is not None:
                base_query = base_query.eq('students.school_id', school_id)
            
            # Apply interview type filter if provided
            if normalized_type:
                base_query = base_query.eq('type', normalized_type)
            
            # Fetch all sessions (we'll filter to latest per student in Python)
            response = await base_query.execute()
            
            if not response.data:
                return [], 0
            
            # Group by student_id and keep only the latest session for each
            student_latest_sessions: Dict[int, dict] = {}
            for session in response.data:
                student_data = session.get('students')
                if not student_data:
                    continue
                    
                student_id = student_data.get('id')
                if student_id is None:
                    continue
                
                # Keep the first occurrence (already sorted by created_at desc)
                if student_id not in student_latest_sessions:
                    student_latest_sessions[student_id] = session
            
            # Convert to list and sort by created_at descending
            all_latest_sessions = sorted(
                student_latest_sessions.values(),
                key=lambda s: s.get('created_at', ''),
                reverse=True
            )
            
            total_count = len(all_latest_sessions)
            
            # Apply pagination
            paginated_sessions = all_latest_sessions[skip:skip + limit]
            
            return paginated_sessions, total_count
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch latest sessions per student: {str(e)}"
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

    @staticmethod
    def _safe_average(scores: List[float], num_total_graded_items: int) -> float:
        """Safely calculates the average, returning 0.0 if the denominator is zero."""
        if num_total_graded_items == 0:
            return 0.0
        return round(sum(scores) / num_total_graded_items, 1)


    @staticmethod
    def calculate_session_dimension_averages(feedbacks: List[Dict[str, Any]]) -> CalculatedAverages:
        """
        Calculates the four individual dimension averages based on the 'answer_text' presence rule.
        
        CR/ST are averaged over ALL answered questions.
        FL/CP are averaged over ODD answered questions.
        A question is answered if 'answer_text' is not empty.
        
        Args:
            feedbacks: List of detailed feedback dictionaries from the database.
            
        Returns:
            CalculatedAverages: A named tuple containing the four averaged scores.
        """
        cr_scores: List[float] = []
        st_scores: List[float] = []
        fl_scores_odd: List[float] = []
        cp_scores_odd: List[float] = []
        answered_questions_count = 0
        answered_odd_questions_count = 0

        for fb in feedbacks:
            q_order = fb.get("question_order", 0)
            answer_text = fb.get("answer_text")

            # Check if the question was answered (non-empty answer_text)
            is_answered = bool(answer_text and str(answer_text).strip())

            if is_answered:
                answered_questions_count += 1
                
                # CR and ST metrics are included for all answered questions
                # Defaulting to 0.0 if score is missing/None
                cr_scores.append(fb.get("content_relevance_score") or 0.0)
                st_scores.append(fb.get("structure_score") or 0.0)
                
                # Check for odd question for FL and CP
                if q_order % 2 != 0:
                    answered_odd_questions_count += 1
                    fl_scores_odd.append(fb.get("fluency_score") or 0.0)
                    cp_scores_odd.append(fb.get("confidence_score") or 0.0)

        # --- Calculate Averages ---
        
        # CR and ST Averages (Denominator: answered_questions_count)
        avg_cr = InterviewSessionService._safe_average(cr_scores, answered_questions_count)
        avg_st = InterviewSessionService._safe_average(st_scores, answered_questions_count)
        
        # FL and CP Averages (Denominator: answered_odd_questions_count)
        avg_fl = InterviewSessionService._safe_average(fl_scores_odd, answered_odd_questions_count)
        avg_cp = InterviewSessionService._safe_average(cp_scores_odd, answered_odd_questions_count)

        return CalculatedAverages(avg_cr, avg_st, avg_fl, avg_cp)
