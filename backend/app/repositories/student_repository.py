"""
Student Repository for student-related database operations.

This repository handles CRUD operations and specialized queries
for the Student model, including quota management.
"""
from typing import Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.student import Student
from app.models.user_profile import UserProfile
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    """
    Repository for Student entity operations.
    
    Provides methods for student management, quota tracking,
    and relationship queries.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and Student model."""
        super().__init__(session, Student)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[Student]:
        """
        Get student by their user profile ID.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            Student if found, None otherwise
        """
        return await self.get_one_by(user_id=user_id)
    
    async def get_by_student_id(self, student_id: str) -> Optional[Student]:
        """
        Get student by their business student ID.
        
        Args:
            student_id: The student's business identifier (e.g., "001-0001-26-0001")
        
        Returns:
            Student if found, None otherwise
        """
        return await self.get_one_by(student_id=student_id)
    
    async def get_with_relations(self, student_id: int) -> Optional[Student]:
        """
        Get student with all relationships eagerly loaded.
        
        Args:
            student_id: The student's primary key ID
        
        Returns:
            Student with user, school, major, and class loaded
        """
        stmt = (
            select(Student)
            .options(
                joinedload(Student.user).options(
                    joinedload(UserProfile.role),
                ),
                joinedload(Student.school),
                joinedload(Student.major),
                joinedload(Student.current_class),
            )
            .where(Student.id == student_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def get_by_user_id_with_relations(self, user_id: UUID) -> Optional[Student]:
        """
        Get student by user ID with all relationships loaded.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            Student with all relationships loaded
        """
        stmt = (
            select(Student)
            .options(
                joinedload(Student.user).options(
                    joinedload(UserProfile.role),
                ),
                joinedload(Student.school),
                joinedload(Student.major),
                joinedload(Student.current_class),
            )
            .where(Student.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def consume_quota(
        self,
        student_id: int,
        expected_quota: int,
    ) -> Tuple[bool, int]:
        """
        Atomically consume one interview session quota.
        
        Uses optimistic locking pattern - only updates if the current
        quota matches the expected value. This prevents race conditions
        when multiple requests try to consume quota simultaneously.
        
        Args:
            student_id: The student's primary key ID
            expected_quota: The expected current quota value
        
        Returns:
            Tuple of (success: bool, new_quota: int)
            - success is False if student not found or quota mismatch
            - new_quota is the quota after the operation (or current if failed)
        """
        if expected_quota <= 0:
            return False, expected_quota
        
        # Atomic update with optimistic locking
        stmt = (
            update(Student)
            .where(
                Student.id == student_id,
                Student.interview_session_quota == expected_quota,
            )
            .values(interview_session_quota=expected_quota - 1)
            .returning(Student.interview_session_quota)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        
        if row is None:
            # Either student not found or quota mismatch
            student = await self.get_by_id(student_id)
            current_quota = student.interview_session_quota if student else 0
            return False, current_quota
        
        return True, row
    
    async def restore_quota(
        self,
        student_id: int,
        amount: int = 1,
    ) -> Optional[int]:
        """
        Restore interview session quota for a student.
        
        Args:
            student_id: The student's primary key ID
            amount: Amount to restore (default 1)
        
        Returns:
            New quota value, or None if student not found
        """
        student = await self.get_by_id(student_id)
        if student is None:
            return None
        
        new_quota = student.interview_session_quota + amount
        student.interview_session_quota = new_quota
        await self.session.flush()
        return new_quota
    
    async def get_students_by_school(
        self,
        school_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Student]:
        """
        Get all students enrolled in a specific school.
        
        Args:
            school_id: The school's primary key ID
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of Student entities
        """
        stmt = (
            select(Student)
            .options(
                joinedload(Student.user),
                joinedload(Student.major),
                joinedload(Student.current_class),
            )
            .where(Student.school_id == school_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
    
    async def get_students_by_class(
        self,
        class_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Student]:
        """
        Get all students in a specific class.
        
        Args:
            class_id: The class's primary key ID
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of Student entities
        """
        stmt = (
            select(Student)
            .options(
                joinedload(Student.user),
                joinedload(Student.school),
                joinedload(Student.major),
            )
            .where(Student.current_class_id == class_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
