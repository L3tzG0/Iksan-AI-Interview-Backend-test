"""
Session Repository for interview session database operations.

This repository handles CRUD operations and specialized queries
for the Session model, including complex relationship loading.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence, Tuple, List, Any

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.session import Session
from app.models.document import Document
from app.models.summary import Summary
from app.models.detailed_feedback import DetailedFeedback
from app.models.next_step import NextStep
from app.models.student import Student
from app.repositories.base import BaseRepository


class SessionRepository(BaseRepository[Session]):
    """
    Repository for Session entity operations.
    
    Provides methods for session management, including complex
    queries with related feedback data.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and Session model."""
        super().__init__(session, Session)
    
    async def get_with_feedbacks(self, session_id: int) -> Optional[Session]:
        """
        Get session with all feedback-related data loaded.
        
        This replaces the complex nested select query from PostgREST.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            Session with document, summary, feedbacks, and next_steps loaded
        """
        stmt = (
            select(Session)
            .options(
                joinedload(Session.student),
                selectinload(Session.document),
                selectinload(Session.summary),
                selectinload(Session.feedbacks),
                selectinload(Session.next_steps),
            )
            .where(Session.id == session_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def get_by_student_paginated(
        self,
        student_id: int,
        skip: int = 0,
        limit: int = 10,
        status: Optional[str] = None,
        session_type: Optional[str] = None,
    ) -> Tuple[Sequence[Session], int]:
        """
        Get paginated sessions for a student with optional filters.
        
        Args:
            student_id: The student's primary key ID
            skip: Number of records to skip
            limit: Maximum records to return
            status: Optional status filter
            session_type: Optional type filter ('job' or 'university')
        
        Returns:
            Tuple of (sessions list, total count)
        """
        # Build base conditions
        conditions = [Session.student_id == student_id]
        if status:
            conditions.append(Session.status == status)
        if session_type:
            conditions.append(Session.type == session_type)
        
        # Count query
        count_stmt = (
            select(func.count())
            .select_from(Session)
            .where(and_(*conditions))
        )
        total = (await self.session.execute(count_stmt)).scalar() or 0
        
        # Data query
        data_stmt = (
            select(Session)
            .options(
                selectinload(Session.summary),
                selectinload(Session.feedbacks),
            )
            .where(and_(*conditions))
            .order_by(Session.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(data_stmt)
        sessions = result.unique().scalars().all()
        
        return sessions, total
    
    async def create_with_document(
        self,
        student_id: int,
        status: str,
        session_type: str,
        cleaned_text: Optional[str] = None,
    ) -> Session:
        """
        Create a session with its document in a single transaction.
        
        Args:
            student_id: The student's primary key ID
            status: Initial session status
            session_type: Session type ('job' or 'university')
            cleaned_text: Optional extracted document text
        
        Returns:
            The created Session with document attached
        """
        # Create session
        session_entity = Session(
            student_id=student_id,
            status=status,
            type=session_type,
        )
        self.session.add(session_entity)
        await self.session.flush()
        
        # Create document
        document = Document(
            session_id=session_entity.id,
            cleaned_text=cleaned_text,
        )
        self.session.add(document)
        await self.session.flush()
        
        # Refresh to get relationships
        await self.session.refresh(session_entity)
        return session_entity
    
    async def update_status(
        self,
        session_id: int,
        status: str,
        completed_at: Optional[datetime] = None,
        total_score: Optional[Decimal] = None,
    ) -> Optional[Session]:
        """
        Update session status and optionally completion data.
        
        Args:
            session_id: The session's primary key ID
            status: New status value
            completed_at: Optional completion timestamp
            total_score: Optional final score
        
        Returns:
            Updated Session, or None if not found
        """
        update_data: dict = {"status": status}
        if completed_at is not None:
            update_data["completed_at"] = completed_at
        if total_score is not None:
            update_data["total_score"] = total_score
        
        return await self.update_by_id(session_id, **update_data)
    
    async def get_recent_sessions(
        self,
        student_id: int,
        limit: int = 5,
    ) -> Sequence[Session]:
        """
        Get most recent sessions for a student.
        
        Args:
            student_id: The student's primary key ID
            limit: Maximum sessions to return
        
        Returns:
            List of recent Session entities
        """
        stmt = (
            select(Session)
            .where(Session.student_id == student_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_sessions_for_school(
        self,
        school_id: int,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> Tuple[Sequence[Session], int]:
        """
        Get sessions for all students in a school (for teacher view).
        
        Args:
            school_id: The school's primary key ID
            skip: Number of records to skip
            limit: Maximum records to return
            status: Optional status filter
        
        Returns:
            Tuple of (sessions list, total count)
        """
        # Build conditions
        conditions = [Student.school_id == school_id]
        if status:
            conditions.append(Session.status == status)
        
        # Count query
        count_stmt = (
            select(func.count())
            .select_from(Session)
            .join(Session.student)
            .where(and_(*conditions))
        )
        total = (await self.session.execute(count_stmt)).scalar() or 0
        
        # Data query
        data_stmt = (
            select(Session)
            .join(Session.student)
            .options(
                joinedload(Session.student).options(
                    joinedload(Student.user),
                    joinedload(Student.major),
                    joinedload(Student.current_class),
                ),
            )
            .where(and_(*conditions))
            .order_by(Session.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(data_stmt)
        sessions = result.unique().scalars().all()
        
        return sessions, total
