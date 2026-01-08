"""
Summary model for session summary feedback.

Summaries contain high-level feedback about the interview session,
including strengths and areas for improvement.

Schema Reference: migrations/001_initial_schema.sql lines 89-94
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class Summary(Base):
    """
    Summary entity for session summary feedback.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        session_id: Foreign key to sessions (cascade delete, unique)
        strength_text: Summary of student's strengths
        areas_for_growth_text: Summary of areas needing improvement
        
    Relationships:
        session: The Session this summary belongs to (one-to-one)
    """
    __tablename__ = "summaries"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One summary per session
        index=True,
    )
    
    strength_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Summary of student's demonstrated strengths",
    )
    
    areas_for_growth_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Summary of areas needing improvement",
    )
    
    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="summary",
        lazy="joined",
    )
    
    def __repr__(self) -> str:
        return f"<Summary(id={self.id}, session_id={self.session_id})>"
