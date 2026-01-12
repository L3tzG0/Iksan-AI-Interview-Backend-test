"""
Role model for user role management.

Roles are reference data that define user permissions:
- admin: Full system access
- teacher: Can manage students and view sessions
- student: Can participate in interviews

Schema Reference: migrations/001_initial_schema.sql lines 14-17
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class Role(Base):
    """
    Role entity for user authorization.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        role_name: Unique role identifier (e.g., 'admin', 'teacher', 'student')
        users: Back-reference to UserProfile entities with this role
    """
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    
    # Relationships
    users: Mapped[List["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="role",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, role_name='{self.role_name}')>"
