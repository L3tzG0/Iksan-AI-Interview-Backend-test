"""
Class Repository for class/grade database operations.

This repository handles CRUD operations and specialized queries
for the Class model.
"""
from typing import Optional, Sequence, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.repositories.base import BaseRepository


class ClassRepository(BaseRepository[Class]):
    """
    Repository for Class entity operations.
    
    Provides methods for class management and queries.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and Class model."""
        super().__init__(session, Class)
    
    async def get_by_name_and_grade(
        self,
        class_name: str,
        grade_level: int,
    ) -> Optional[Class]:
        """
        Get class by name and grade level.
        
        Args:
            class_name: The class name
            grade_level: The grade level (1, 2, or 3)
        
        Returns:
            Class if found, None otherwise
        """
        stmt = (
            select(Class)
            .where(
                Class.class_name == class_name,
                Class.grade_level == grade_level,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def resolve_or_create(
        self,
        class_name: str,
        grade_level: int,
    ) -> Tuple[int, str, int]:
        """
        Resolve existing class or create a new one atomically.
        
        Calls the PostgreSQL RPC function `resolve_or_create_class`
        which handles concurrent insertions safely.
        
        Args:
            class_name: Name of the class
            grade_level: Grade level (1, 2, or 3)
        
        Returns:
            Tuple of (class_id, class_name, grade_level)
        """
        # Call the PostgreSQL function via raw SQL
        result = await self.session.execute(
            text("""
                SELECT * FROM public.resolve_or_create_class(
                    :p_class_name, :p_grade_level
                )
            """),
            {"p_class_name": class_name, "p_grade_level": grade_level}
        )
        row = result.fetchone()
        if row:
            return row.class_id, row.class_name, row.grade_level
        
        # Fallback: manual creation if function doesn't exist
        existing = await self.get_by_name_and_grade(class_name, grade_level)
        if existing:
            return existing.id, existing.class_name, existing.grade_level
        
        new_class = await self.create(
            class_name=class_name,
            grade_level=grade_level,
        )
        return new_class.id, new_class.class_name, new_class.grade_level
    
    async def get_by_grade_level(
        self,
        grade_level: int,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Class]:
        """
        Get all classes for a specific grade level.
        
        Args:
            grade_level: The grade level (1, 2, or 3)
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of Class entities
        """
        stmt = (
            select(Class)
            .where(Class.grade_level == grade_level)
            .order_by(Class.class_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_with_students_count(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Tuple[Class, int]]:
        """
        Get all classes with student count.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of (Class, student_count) tuples
        """
        from app.models.student import Student
        from sqlalchemy import func
        
        stmt = (
            select(Class, func.count(Student.id).label("student_count"))
            .outerjoin(Student, Class.id == Student.current_class_id)
            .group_by(Class.id)
            .order_by(Class.grade_level, Class.class_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row.Class, row.student_count) for row in result.all()]
    
    async def search_classes(
        self,
        query: str,
        grade_level: Optional[int] = None,
        limit: int = 10,
    ) -> Sequence[Class]:
        """
        Search classes by name with optional grade filter.
        
        Args:
            query: Search query string
            grade_level: Optional grade level filter
            limit: Maximum results to return
        
        Returns:
            List of matching Class entities
        """
        from sqlalchemy import and_
        
        conditions = [Class.class_name.ilike(f"%{query}%")]
        if grade_level is not None:
            conditions.append(Class.grade_level == grade_level)
        
        stmt = (
            select(Class)
            .where(and_(*conditions))
            .order_by(Class.grade_level, Class.class_name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
