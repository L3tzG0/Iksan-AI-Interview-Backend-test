"""
Interview Session Service for session lifecycle management.

Uses SessionRepository for database operations with SQLAlchemy AsyncSession.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Tuple, List, NamedTuple, Dict, Any
from operator import itemgetter

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from fastapi import HTTPException, status

from app.models.session import Session
from app.models.student import Student
from app.models.user_profile import UserProfile
from app.models.school import School
from app.models.major import Major
from app.models.class_ import Class
from app.models.detailed_feedback import DetailedFeedback
from app.models.summary import Summary
from app.models.next_step import NextStep
from app.models.document import Document
from app.repositories.session_repository import SessionRepository
from app.utils.pagination import paginate_query


class CalculatedAverages(NamedTuple):
    """The four calculated dimension averages for a session."""
    avg_cr: float
    avg_st: float
    avg_fl: float
    avg_cp: float


ALLOWED_SESSION_TYPES = {"job", "university"}


class InterviewSessionService:
    """Service for handling interview session database operations."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.repo = SessionRepository(db)

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
    
    async def create_session(self, student_id: int, status_str: str = "in_progress", session_type: str = "job") -> dict:
        """
        Create new interview session.
        
        Args:
            student_id: ID of the student
            status_str: Initial status (default: "in_progress")
            session_type: Session type (job or university)
        
        Returns:
            dict: Created session record
        """
        try:
            allowed_types = {"job", "university"}
            if session_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid session type '{session_type}'. Must be one of: {', '.join(sorted(allowed_types))}."
                )

            session = Session(
                student_id=student_id,
                status=status_str,
                type=session_type
            )
            
            self.db.add(session)
            await self.db.flush()
            await self.db.refresh(session)
            
            return self._session_to_dict(session)
            
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
        status_str: str,
        completed_at: Optional[datetime] = None,
        total_score: Optional[float] = None
    ) -> dict:
        """
        Update session status and related fields.
        
        Args:
            session_id: Session ID
            status_str: New status value
            completed_at: Completion timestamp (optional)
            total_score: Total score (optional)
        
        Returns:
            dict: Updated session record
        """
        try:
            session = await self.repo.get_by_id(session_id)
            
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"Session with id {session_id} not found"
                )
            
            session.status = status_str
            
            if completed_at:
                session.completed_at = completed_at
            if total_score is not None:
                session.total_score = Decimal(str(total_score))
            
            await self.db.flush()
            await self.db.refresh(session)
            
            return self._session_to_dict(session)
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update session: {str(e)}"
            )
    
    async def delete_session(self, session_id: int) -> bool:
        """
        Delete session (hard delete for rollback).
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            bool: True if successful
        """
        try:
            await self.repo.delete_by_id(session_id)
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete session: {str(e)}"
            )
    
    async def get_session(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session record if found
        """
        try:
            session = await self.repo.get_by_id(session_id)
            return self._session_to_dict(session) if session else None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session: {str(e)}"
            )

    async def get_session_with_details(self, session_id: int) -> Optional[dict]:
        """
        Get session by ID with student and related info (single query).
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested student details
        """
        try:
            stmt = (
                select(Session)
                .options(
                    joinedload(Session.student).options(
                        joinedload(Student.user),
                        joinedload(Student.school),
                        joinedload(Student.major),
                    )
                )
                .where(Session.id == session_id)
            )
            result = await self.db.execute(stmt)
            session = result.unique().scalar_one_or_none()
            
            if not session:
                return None
            
            return self._session_to_dict_with_details(session)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch session with details: {str(e)}"
            )

    async def get_session_with_feedbacks(self, session_id: int) -> Optional[dict]:
        """
        Get session with all feedbacks, summary, and next steps in single query.
        
        Args:
            session_id: Session ID
        
        Returns:
            dict or None: Session with nested feedback data
        """
        try:
            session = await self.repo.get_with_feedbacks(session_id)
            
            if not session:
                return None
            
            return self._session_to_dict_with_feedbacks(session)
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

            sessions, total = await self.repo.get_by_student_paginated(
                student_id=student_id,
                skip=skip,
                limit=limit,
                status=status_filter,
                session_type=normalized_type,
            )
            
            return [self._session_to_dict(s) for s in sessions], total
        except HTTPException:
            raise
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
            # Build query
            if with_student:
                query = (
                    select(Session)
                    .options(
                        joinedload(Session.student).options(
                            joinedload(Student.user),
                            joinedload(Student.school),
                            joinedload(Student.major),
                        )
                    )
                )
            else:
                query = select(Session)
            
            conditions = []
            if student_id is not None:
                conditions.append(Session.student_id == student_id)
            if status_filter:
                conditions.append(Session.status == status_filter)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(Session.created_at.desc())
            
            # Count
            count_stmt = select(func.count()).select_from(query.subquery())
            total = (await self.db.execute(count_stmt)).scalar() or 0
            
            # Paginate
            paginated = query.offset(skip).limit(limit)
            result = await self.db.execute(paginated)
            sessions = result.unique().scalars().all()
            
            if with_student:
                return [self._session_to_dict_with_details(s) for s in sessions], total
            return [self._session_to_dict(s) for s in sessions], total
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

            query = (
                select(Session)
                .join(Student, Session.student_id == Student.id)
                .options(
                    joinedload(Session.student).options(
                        joinedload(Student.user),
                        joinedload(Student.school),
                        joinedload(Student.major),
                        joinedload(Student.current_class),
                    )
                )
            )
            
            conditions = []
            if status_filter:
                conditions.append(Session.status == status_filter)
            if school_id is not None:
                conditions.append(Student.school_id == school_id)
            if normalized_type:
                conditions.append(Session.type == normalized_type)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(Session.created_at.desc())
            
            # Count
            count_stmt = select(func.count()).select_from(query.subquery())
            total = (await self.db.execute(count_stmt)).scalar() or 0
            
            # Paginate
            paginated = query.offset(skip).limit(limit)
            result = await self.db.execute(paginated)
            sessions = result.unique().scalars().all()
            
            return [self._session_to_dict_with_student_info(s) for s in sessions], total
        except HTTPException:
            raise
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
            
            # Build query with joins
            query = (
                select(Session)
                .join(Student, Session.student_id == Student.id)
                .options(
                    joinedload(Session.student).options(
                        joinedload(Student.user),
                        joinedload(Student.school),
                        joinedload(Student.major),
                        joinedload(Student.current_class),
                    )
                )
                .where(Session.status != 'failed')
            )
            
            if school_id is not None:
                query = query.where(Student.school_id == school_id)
            if normalized_type:
                query = query.where(Session.type == normalized_type)
            
            query = query.order_by(Session.created_at.desc())
            
            # Execute and get all matching sessions
            result = await self.db.execute(query)
            all_sessions = result.unique().scalars().all()
            
            # Group by student_id and keep only the latest
            student_latest_sessions: Dict[int, Session] = {}
            for session in all_sessions:
                if session.student_id not in student_latest_sessions:
                    student_latest_sessions[session.student_id] = session
            
            # Convert to list and sort
            all_latest = sorted(
                student_latest_sessions.values(),
                key=lambda s: s.created_at or datetime.min,
                reverse=True
            )
            
            total_count = len(all_latest)
            paginated_sessions = all_latest[skip:skip + limit]
            
            return [self._session_to_dict_with_student_info(s) for s in paginated_sessions], total_count
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch latest sessions per student: {str(e)}"
            )

    # =========================================================================
    # Static utility methods
    # =========================================================================

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
        """
        Map raw session record to admin/teacher response shape.
        
        Note: This method is kept for backward compatibility with dict-based data.
        For SQLAlchemy models, use _session_to_dict_with_student_info instead.
        """
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

            is_answered = bool(answer_text and str(answer_text).strip())

            if is_answered:
                answered_questions_count += 1
                
                cr_scores.append(fb.get("content_relevance_score") or 0.0)
                st_scores.append(fb.get("structure_score") or 0.0)
                
                if q_order % 2 != 0:
                    answered_odd_questions_count += 1
                    fl_scores_odd.append(fb.get("fluency_score") or 0.0)
                    cp_scores_odd.append(fb.get("confidence_score") or 0.0)

        avg_cr = InterviewSessionService._safe_average(cr_scores, answered_questions_count)
        avg_st = InterviewSessionService._safe_average(st_scores, answered_questions_count)
        avg_fl = InterviewSessionService._safe_average(fl_scores_odd, answered_odd_questions_count)
        avg_cp = InterviewSessionService._safe_average(cp_scores_odd, answered_odd_questions_count)

        return CalculatedAverages(avg_cr, avg_st, avg_fl, avg_cp)

    # =========================================================================
    # Helper methods for model-to-dict conversion
    # =========================================================================

    def _session_to_dict(self, session: Session) -> dict:
        """Convert Session model to basic dict."""
        return {
            "id": session.id,
            "student_id": session.student_id,
            "status": session.status,
            "type": session.type,
            "total_score": float(session.total_score) if session.total_score else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }

    def _session_to_dict_with_details(self, session: Session) -> dict:
        """Convert Session model to dict with student details."""
        result = self._session_to_dict(session)
        
        if session.student:
            student = session.student
            result["students"] = {
                "id": student.id,
                "user_id": str(student.user_id),
                "school_id": student.school_id,
                "major_id": student.major_id,
                "user_profiles": {
                    "id": str(student.user.id),
                    "full_name": student.user.full_name,
                    "email": student.user.email,
                } if student.user else None,
                "schools": {
                    "id": student.school.id,
                    "school_name": student.school.school_name,
                } if student.school else None,
                "majors": {
                    "id": student.major.id,
                    "major_name": student.major.major_name,
                } if student.major else None,
            }
        
        return result

    def _session_to_dict_with_feedbacks(self, session: Session) -> dict:
        """Convert Session model to dict with all feedback data."""
        result = self._session_to_dict(session)
        
        result["detailed_feedbacks"] = [
            {
                "id": fb.id,
                "question_order": fb.question_order,
                "question_text": fb.question_text,
                "answer_text": fb.answer_text,
                "evaluation_text": fb.evaluation_text,
                "is_correct": fb.is_correct,
                "content_relevance_score": float(fb.content_relevance_score) if fb.content_relevance_score else None,
                "structure_score": float(fb.structure_score) if fb.structure_score else None,
                "fluency_score": float(fb.fluency_score) if fb.fluency_score else None,
                "confidence_score": float(fb.confidence_score) if fb.confidence_score else None,
                "overall_score": float(fb.overall_score) if fb.overall_score else None,
            }
            for fb in (session.feedbacks or [])
        ]
        
        result["summaries"] = {
            "id": session.summary.id,
            "strength_text": session.summary.strength_text,
            "areas_for_growth_text": session.summary.areas_for_growth_text,
        } if session.summary else None
        
        result["next_steps"] = [
            {
                "id": ns.id,
                "next_step_order": ns.next_step_order,
                "title": ns.title,
                "description_text": ns.description_text,
            }
            for ns in (session.next_steps or [])
        ]
        
        return result

    def _session_to_dict_with_student_info(self, session: Session) -> dict:
        """Convert Session model to admin/teacher view dict."""
        student = session.student
        
        return {
            "session_id": session.id,
            "interview_type": session.type,
            "student_name": student.user.full_name if student and student.user else None,
            "student_identifier": student.student_id if student else None,
            "school_name": student.school.school_name if student and student.school else None,
            "major_name": student.major.major_name if student and student.major else None,
            "class_name": student.current_class.class_name if student and student.current_class else None,
            "grade_level": student.current_class.grade_level if student and student.current_class else None,
            "total_score": float(session.total_score) if session.total_score else None,
            "status": session.status,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }
