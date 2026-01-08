"""
Base Repository class providing generic CRUD operations.

This module defines a generic repository pattern that can be extended
for specific entity types. It provides common database operations
using SQLAlchemy's async session.

The generic type parameter T represents the SQLAlchemy model class.
"""
from typing import Any, Generic, List, Optional, Type, TypeVar, Sequence
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import Base

# Type variable for the model class
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic repository providing CRUD operations for SQLAlchemy models.
    
    This class implements the Repository pattern, encapsulating database
    access logic and providing a clean interface for data operations.
    
    Attributes:
        session: The SQLAlchemy async session for database operations
        model: The SQLAlchemy model class this repository manages
    
    Usage:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
            
            async def get_by_email(self, email: str) -> Optional[User]:
                return await self.get_one_by(email=email)
    """
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        """
        Initialize the repository with a session and model class.
        
        Args:
            session: SQLAlchemy AsyncSession for database operations
            model: The SQLAlchemy model class this repository manages
        """
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: Any) -> Optional[T]:
        """
        Retrieve an entity by its primary key.
        
        Args:
            id: The primary key value (can be int, UUID, etc.)
        
        Returns:
            The entity if found, None otherwise
        """
        return await self.session.get(self.model, id)
    
    async def get_one_by(self, **filters) -> Optional[T]:
        """
        Retrieve a single entity matching the given filters.
        
        Args:
            **filters: Column=value pairs for filtering
        
        Returns:
            The first matching entity, or None if not found
        
        Example:
            user = await repo.get_one_by(email="test@example.com")
        """
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> Sequence[T]:
        """
        Retrieve multiple entities with optional filtering and pagination.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            **filters: Column=value pairs for filtering
        
        Returns:
            List of matching entities
        """
        stmt = select(self.model).filter_by(**filters).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_all_by(self, **filters) -> Sequence[T]:
        """
        Retrieve all entities matching the given filters (no pagination).
        
        Args:
            **filters: Column=value pairs for filtering
        
        Returns:
            List of all matching entities
        """
        stmt = select(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def count(self, **filters) -> int:
        """
        Count entities matching the given filters.
        
        Args:
            **filters: Column=value pairs for filtering
        
        Returns:
            Number of matching entities
        """
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def create(self, **data) -> T:
        """
        Create a new entity with the given data.
        
        Args:
            **data: Column=value pairs for the new entity
        
        Returns:
            The created entity instance
        
        Note:
            The entity is added to the session but not committed.
            The caller is responsible for committing the transaction.
        """
        entity = self.model(**data)
        self.session.add(entity)
        await self.session.flush()  # Flush to get generated values (e.g., id)
        await self.session.refresh(entity)
        return entity
    
    async def create_from_model(self, entity: T) -> T:
        """
        Add an existing model instance to the session.
        
        Args:
            entity: The model instance to add
        
        Returns:
            The same entity instance (now attached to session)
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def update_by_id(self, id: Any, **data) -> Optional[T]:
        """
        Update an entity by its primary key.
        
        Args:
            id: The primary key value
            **data: Column=value pairs to update
        
        Returns:
            The updated entity, or None if not found
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return None
        
        for key, value in data.items():
            setattr(entity, key, value)
        
        await self.session.flush()
        await self.session.refresh(entity)
        return entity
    
    async def delete_by_id(self, id: Any) -> bool:
        """
        Delete an entity by its primary key.
        
        Args:
            id: The primary key value
        
        Returns:
            True if entity was deleted, False if not found
        """
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        
        await self.session.delete(entity)
        await self.session.flush()
        return True
    
    async def delete_by(self, **filters) -> int:
        """
        Delete entities matching the given filters.
        
        Args:
            **filters: Column=value pairs for filtering
        
        Returns:
            Number of deleted entities
        """
        stmt = delete(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.rowcount or 0
    
    async def exists(self, **filters) -> bool:
        """
        Check if any entity matches the given filters.
        
        Args:
            **filters: Column=value pairs for filtering
        
        Returns:
            True if at least one matching entity exists
        """
        return await self.count(**filters) > 0
    
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in a single operation.
        
        Args:
            entities: List of model instances to create
        
        Returns:
            List of created entities
        
        Note:
            More efficient than individual creates for large batches.
        """
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities
