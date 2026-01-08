"""
SQLAlchemy Models Package.

This package contains all SQLAlchemy ORM model definitions for the
Iksan AI Interview Backend. Each model corresponds to a database table.

Model Organization:
- base.py: Base class and common mixins
- role.py, school.py, major.py: Reference tables
- user_profile.py, teacher.py, student.py, class_.py: User management
- session.py, document.py, summary.py: Interview sessions
- detailed_feedback.py, next_step.py: Session feedback
- allowed_email_domain.py: Email domain restrictions

All models inherit from Base (declared in app.core.database) and use
SQLAlchemy 2.0 Mapped[] annotation style for type safety.
"""

# Import all models for easy access and Alembic metadata discovery
from app.models.base import TimestampMixin
from app.models.role import Role
from app.models.school import School
from app.models.major import Major
from app.models.user_profile import UserProfile
from app.models.teacher import Teacher
from app.models.student import Student
from app.models.class_ import Class
from app.models.session import Session
from app.models.document import Document
from app.models.summary import Summary
from app.models.detailed_feedback import DetailedFeedback
from app.models.next_step import NextStep
from app.models.allowed_email_domain import AllowedEmailDomain

__all__ = [
    "TimestampMixin",
    "Role",
    "School",
    "Major",
    "UserProfile",
    "Teacher",
    "Student",
    "Class",
    "Session",
    "Document",
    "Summary",
    "DetailedFeedback",
    "NextStep",
    "AllowedEmailDomain",
]
