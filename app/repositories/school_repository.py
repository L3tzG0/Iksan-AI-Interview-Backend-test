"""
School Repository for school-related database operations.

This repository handles CRUD operations and specialized queries
for the School model, including RPC function calls for school
resolution and number assignment.
"""
from typing import Optional, Sequence, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    """
    Repository for School entity operations.
    
    Provides methods for school management, including PostgreSQL
    RPC function wrappers for atomic operations.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and School model."""
        super().__init__(session, School)
    
    async def get_by_name(self, school_name: str) -> Optional[School]:
        """
        Get school by name (case-insensitive).
        
        Args:
            school_name: The school name to search for
        
        Returns:
            School if found, None otherwise
        """
        stmt = (
            select(School)
            .where(School.school_name.ilike(school_name))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_number(self, school_number: str) -> Optional[School]:
        """
        Get school by its 3-digit number.
        
        Args:
            school_number: The school's 3-digit code
        
        Returns:
            School if found, None otherwise
        """
        return await self.get_one_by(school_number=school_number)
    
    async def resolve_or_create(
        self,
        school_name: str,
    ) -> Tuple[int, Optional[str]]:
        """
        Resolve existing school or create a new one atomically.
        
        Calls the PostgreSQL RPC function `resolve_or_create_school`
        which handles concurrent insertions safely.
        
        Args:
            school_name: Name of the school to resolve or create
        
        Returns:
            Tuple of (school_id, school_number)
        """
        # Call the PostgreSQL function via raw SQL
        result = await self.session.execute(
            text("SELECT * FROM public.resolve_or_create_school(:p_school_name)"),
            {"p_school_name": school_name}
        )
        row = result.fetchone()
        if row:
            return row.school_id, row.school_number
        
        # Fallback: manual creation if function doesn't exist
        school = await self.get_by_name(school_name)
        if school:
            return school.id, school.school_number
        
        new_school = await self.create(school_name=school_name)
        return new_school.id, new_school.school_number
    
    async def assign_number(self, school_id: int) -> Optional[str]:
        """
        Assign a school number to a school atomically.
        
        Calls the PostgreSQL RPC function `assign_school_number`
        which generates and assigns a unique 3-digit number.
        
        Args:
            school_id: The school's primary key ID
        
        Returns:
            The assigned school number, or None on failure
        """
        result = await self.session.execute(
            text("SELECT public.assign_school_number(:p_school_id) as school_number"),
            {"p_school_id": school_id}
        )
        row = result.fetchone()
        return row.school_number if row else None
    
    async def get_all_with_students_count(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Tuple[School, int]]:
        """
        Get all schools with student count.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of (School, student_count) tuples
        """
        from app.models.student import Student
        from sqlalchemy import func
        
        stmt = (
            select(School, func.count(Student.id).label("student_count"))
            .outerjoin(Student, School.id == Student.school_id)
            .group_by(School.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row.School, row.student_count) for row in result.all()]
    
    async def search_schools(
        self,
        query: str,
        limit: int = 10,
    ) -> Sequence[School]:
        """
        Search schools by name prefix.
        
        Args:
            query: Search query string
            limit: Maximum results to return
        
        Returns:
            List of matching School entities
        """
        stmt = (
            select(School)
            .where(School.school_name.ilike(f"{query}%"))
            .order_by(School.school_name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
