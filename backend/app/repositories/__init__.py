"""
Repository Package for Database Access Layer.

This package provides a Repository pattern abstraction over SQLAlchemy
for cleaner separation between business logic and data access.

Repository Benefits:
- Encapsulates query logic in reusable methods
- Enables easier testing via dependency injection
- Provides consistent error handling and logging
- Allows future database backend changes with minimal impact

Usage:
    from app.repositories import UserRepository, StudentRepository
    
    async def get_users_handler(db: AsyncSession):
        user_repo = UserRepository(db)
        users = await user_repo.get_all()
        return users
"""

from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.feedback_repository import FeedbackRepository
from app.repositories.school_repository import SchoolRepository
from app.repositories.major_repository import MajorRepository
from app.repositories.class_repository import ClassRepository
from app.repositories.domain_repository import DomainRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "StudentRepository",
    "TeacherRepository",
    "SessionRepository",
    "FeedbackRepository",
    "SchoolRepository",
    "MajorRepository",
    "ClassRepository",
    "DomainRepository",
]
