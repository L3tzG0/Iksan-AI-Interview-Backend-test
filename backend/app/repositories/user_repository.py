"""
User Repository for user profile operations.

This repository handles CRUD operations and specialized queries
for the UserProfile model.
"""
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.user_profile import UserProfile
from app.models.role import Role
from app.models.student import Student
from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserProfile]):
    """
    Repository for UserProfile entity operations.
    
    Provides methods for user authentication, profile management,
    and role-based queries.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and UserProfile model."""
        super().__init__(session, UserProfile)
    
    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email address.
        
        Args:
            email: The user's email address
        
        Returns:
            UserProfile if found, None otherwise
        """
        return await self.get_one_by(email=email)
    
    async def get_with_role(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Get user profile with role eagerly loaded.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            UserProfile with role relationship loaded
        """
        stmt = (
            select(UserProfile)
            .options(joinedload(UserProfile.role))
            .where(UserProfile.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_full_context(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Get user profile with all relationships eagerly loaded.
        
        Loads role, student (with school, major, class),
        and teacher relationships.
        
        Args:
            user_id: The user's UUID
        
        Returns:
            UserProfile with all relationships loaded
        """
        stmt = (
            select(UserProfile)
            .options(
                joinedload(UserProfile.role),
                selectinload(UserProfile.student).options(
                    joinedload(Student.school),
                    joinedload(Student.major),
                    joinedload(Student.current_class),
                ),
                selectinload(UserProfile.teacher).options(
                    joinedload(Teacher.school),
                ),
            )
            .where(UserProfile.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()
    
    async def get_by_email_with_role(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email with role loaded (for auth).
        
        Args:
            email: The user's email address
        
        Returns:
            UserProfile with role relationship loaded
        """
        stmt = (
            select(UserProfile)
            .options(joinedload(UserProfile.role))
            .where(UserProfile.email == email)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_users_by_role(
        self,
        role_name: str,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[UserProfile]:
        """
        Get all users with a specific role name.
        
        Args:
            role_name: The role name to filter by
            skip: Number of records to skip
            limit: Maximum records to return
        
        Returns:
            List of UserProfile entities with the specified role
        """
        stmt = (
            select(UserProfile)
            .join(UserProfile.role)
            .where(Role.role_name == role_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_user(
        self,
        id: UUID,
        email: str,
        full_name: str,
        hashed_password: Optional[str] = None,
        role_id: Optional[int] = None,
    ) -> UserProfile:
        """
        Create a new user profile.
        
        Args:
            id: UUID for the new user
            email: User's email address
            full_name: User's display name
            hashed_password: BCrypt hashed password
            role_id: Optional role ID
        
        Returns:
            The created UserProfile entity
        """
        return await self.create(
            id=id,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role_id=role_id,
        )
    
    async def update_password(
        self,
        user_id: UUID,
        hashed_password: str,
    ) -> Optional[UserProfile]:
        """
        Update a user's hashed password.
        
        Args:
            user_id: The user's UUID
            hashed_password: New BCrypt hashed password
        
        Returns:
            Updated UserProfile, or None if not found
        """
        return await self.update_by_id(user_id, hashed_password=hashed_password)
