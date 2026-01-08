"""
Teacher model for teacher-specific data.

Teachers are users with the 'teacher' role who can manage students
and monitor interview sessions within their affiliated school.

Schema Reference: migrations/001_initial_schema.sql lines 45-51
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.school import School


class Teacher(Base, TimestampMixin):
    """
    Teacher entity for teacher-specific data.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        user_id: Foreign key to user_profiles (unique, one-to-one)
        school_id: Foreign key to schools (optional)
        created_at: Timestamp when record was created
        updated_at: Timestamp of last modification
        
    Relationships:
        user: The teacher's UserProfile entity
        school: The teacher's affiliated School entity
    """
    __tablename__ = "teachers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        unique=True,  # One-to-one with user_profiles
        nullable=False,
        index=True,
    )
    
    school_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("schools.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Relationships
    user: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="teacher",
        lazy="joined",
    )
    
    school: Mapped[Optional["School"]] = relationship(
        "School",
        back_populates="teachers",
        lazy="joined",
    )
    
    # Indexes defined in migration
    __table_args__ = (
        Index("idx_teachers_user_id", "user_id"),
        Index("idx_teachers_school_id", "school_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, user_id={self.user_id}, school_id={self.school_id})>"
