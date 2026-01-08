"""
Teacher Repository for teacher-related database operations.

This repository handles CRUD operations and specialized queries
for the Teacher model.
"""
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.teacher import Teacher
from app.models.user_profile import UserProfile
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    """
    Repository for Teacher entity operations.
    
    Provides methods for teacher management and school-based queries.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and Teacher model."""
        super().__init__(session, Teacher)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[Teacher]:
        """
        Get teacher by their user profile ID.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            Teacher if found, None otherwise
        """
        return await self.get_one_by(user_id=user_id)
    
    async def get_with_relations(self, teacher_id: int) -> Optional[Teacher]:
        """
        Get teacher with all relationships eagerly loaded.
        
        Args:
            teacher_id: The teacher's primary key ID
        
        Returns:
            Teacher with user and school loaded
        """
        stmt = (
            select(Teacher)
            .options(
                joinedload(Teacher.user).options(
                    joinedload(UserProfile.role),
                ),
                joinedload(Teacher.school),
            )
            .where(Teacher.id == teacher_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def get_by_user_id_with_relations(self, user_id: UUID) -> Optional[Teacher]:
        """
        Get teacher by user ID with all relationships loaded.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            Teacher with user and school loaded
        """
        stmt = (
            select(Teacher)
            .options(
                joinedload(Teacher.user).options(
                    joinedload(UserProfile.role),
                ),
                joinedload(Teacher.school),
            )
            .where(Teacher.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def get_teachers_by_school(
        self,
        school_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Teacher]:
        """
        Get all teachers affiliated with a specific school.
        
        Args:
            school_id: The school's primary key ID
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of Teacher entities
        """
        stmt = (
            select(Teacher)
            .options(joinedload(Teacher.user))
            .where(Teacher.school_id == school_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()
    
    async def create_teacher(
        self,
        user_id: UUID,
        school_id: Optional[int] = None,
    ) -> Teacher:
        """
        Create a new teacher record.
        
        Args:
            user_id: The user's UUID
            school_id: Optional school affiliation
        
        Returns:
            The created Teacher entity
        """
        return await self.create(
            user_id=user_id,
            school_id=school_id,
        )
