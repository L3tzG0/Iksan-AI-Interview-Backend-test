"""
Major Repository for major/department database operations.

This repository handles CRUD operations and specialized queries
for the Major model, including RPC function calls for major
resolution and number assignment.
"""
from typing import Optional, Sequence, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.major import Major
from app.repositories.base import BaseRepository


class MajorRepository(BaseRepository[Major]):
    """
    Repository for Major entity operations.
    
    Provides methods for major management, including PostgreSQL
    RPC function wrappers for atomic operations.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and Major model."""
        super().__init__(session, Major)
    
    async def get_by_name(self, major_name: str) -> Optional[Major]:
        """
        Get major by name (case-insensitive).
        
        Args:
            major_name: The major name to search for
        
        Returns:
            Major if found, None otherwise
        """
        stmt = (
            select(Major)
            .where(Major.major_name.ilike(major_name))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_number(self, major_number: str) -> Optional[Major]:
        """
        Get major by its 4-digit number.
        
        Args:
            major_number: The major's 4-digit code
        
        Returns:
            Major if found, None otherwise
        """
        return await self.get_one_by(major_number=major_number)
    
    async def resolve_or_create(
        self,
        major_name: str,
    ) -> Tuple[int, Optional[str]]:
        """
        Resolve existing major or create a new one atomically.
        
        Calls the PostgreSQL RPC function `resolve_or_create_major`
        which handles concurrent insertions safely.
        
        Args:
            major_name: Name of the major to resolve or create
        
        Returns:
            Tuple of (major_id, major_number)
        """
        # Call the PostgreSQL function via raw SQL
        result = await self.session.execute(
            text("SELECT * FROM public.resolve_or_create_major(:p_major_name)"),
            {"p_major_name": major_name}
        )
        row = result.fetchone()
        if row:
            return row.major_id, row.major_number
        
        # Fallback: manual creation if function doesn't exist
        major = await self.get_by_name(major_name)
        if major:
            return major.id, major.major_number
        
        new_major = await self.create(major_name=major_name)
        return new_major.id, new_major.major_number
    
    async def assign_number(self, major_id: int) -> Optional[str]:
        """
        Assign a major number to a major atomically.
        
        Calls the PostgreSQL RPC function `assign_major_number`
        which generates and assigns a unique 4-digit number.
        
        Args:
            major_id: The major's primary key ID
        
        Returns:
            The assigned major number, or None on failure
        """
        result = await self.session.execute(
            text("SELECT public.assign_major_number(:p_major_id) as major_number"),
            {"p_major_id": major_id}
        )
        row = result.fetchone()
        return row.major_number if row else None
    
    async def get_all_with_students_count(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Tuple[Major, int]]:
        """
        Get all majors with student count.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of (Major, student_count) tuples
        """
        from app.models.student import Student
        from sqlalchemy import func
        
        stmt = (
            select(Major, func.count(Student.id).label("student_count"))
            .outerjoin(Student, Major.id == Student.major_id)
            .group_by(Major.id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row.Major, row.student_count) for row in result.all()]
    
    async def search_majors(
        self,
        query: str,
        limit: int = 10,
    ) -> Sequence[Major]:
        """
        Search majors by name prefix.
        
        Args:
            query: Search query string
            limit: Maximum results to return
        
        Returns:
            List of matching Major entities
        """
        stmt = (
            select(Major)
            .where(Major.major_name.ilike(f"{query}%"))
            .order_by(Major.major_name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
