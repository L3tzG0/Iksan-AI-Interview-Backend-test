"""
Class Service for class/grade management operations.

Refactored from Supabase AsyncClient to SQLAlchemy AsyncSession.
Uses ClassRepository for database operations.
"""
from typing import Optional, Tuple, List, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.schemas.class_schema import ClassCreate, ClassUpdate
from app.models.class_ import Class
from app.repositories.class_repository import ClassRepository
from app.utils.pagination import paginate_query


class ClassService:
    """
    Service for class database operations.
    
    All methods are async because SQLAlchemy AsyncSession
    uses async database calls. This ensures proper connection handling
    under concurrent load.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.repo = ClassRepository(db)

    async def create_class(self, class_data: ClassCreate) -> dict:
        """
        Create a new class.
        
        Args:
            class_data: Class creation data
        
        Returns:
            dict: Created class record
        """
        try:
            new_class = await self.repo.create(**class_data.model_dump())
            return self._to_dict(new_class)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_class(self, class_id: int) -> dict:
        """
        Get class by ID.
        
        Args:
            class_id: Class primary key ID
        
        Returns:
            dict: Class record
        """
        try:
            class_obj = await self.repo.get_by_id(class_id)
            if not class_obj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return self._to_dict(class_obj)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_all_classes(
        self,
        skip: int = 0,
        limit: int = 20,
        grade_level: Optional[int] = None
    ) -> Tuple[List[dict], int]:
        """
        Get all classes with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            grade_level: Filter by grade level (1, 2, or 3)
        
        Returns:
            Tuple of (list of classes, total count)
        """
        try:
            # Build base query
            query = select(Class)
            if grade_level is not None:
                query = query.where(Class.grade_level == grade_level)
            query = query.order_by(Class.grade_level, Class.class_name)
            
            # Execute with pagination
            classes, total = await paginate_query(self.db, query, skip, limit)
            
            return [self._to_dict(c) for c in classes], total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_class(self, class_id: int, class_data: ClassUpdate) -> dict:
        """
        Update class information.
        
        Args:
            class_id: Class primary key ID
            class_data: Fields to update
        
        Returns:
            dict: Updated class record
        """
        try:
            update_data = class_data.model_dump(exclude_unset=True)
            updated_class = await self.repo.update_by_id(class_id, **update_data)
            if not updated_class:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return self._to_dict(updated_class)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def _to_dict(self, class_obj: Class) -> dict:
        """
        Convert Class model to dictionary.
        
        Args:
            class_obj: Class SQLAlchemy model instance
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": class_obj.id,
            "class_name": class_obj.class_name,
            "grade_level": class_obj.grade_level,
        }
