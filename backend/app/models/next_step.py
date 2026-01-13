"""
NextStep model for recommended actions after interview.

NextSteps contain actionable recommendations for students
based on their interview performance.

Schema Reference: migrations/001_initial_schema.sql lines 111-117
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class NextStep(Base):
    """
    NextStep entity for post-interview recommendations.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        session_id: Foreign key to sessions (cascade delete)
        next_step_order: Order of this recommendation
        title: Short title for the recommendation
        description_text: Detailed description of the recommended action
        
    Relationships:
        session: The Session this recommendation belongs to
    """
    __tablename__ = "next_steps"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    next_step_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Order of this recommendation in the list",
    )
    
    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Short title for the recommendation",
    )
    
    description_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the recommended action",
    )
    
    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="next_steps",
        lazy="noload",  # No direct usage of NextStep.session anywhere.
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_next_steps_session_id", "session_id"),
    )
    
    def __repr__(self) -> str:
        return f"<NextStep(id={self.id}, session_id={self.session_id}, title='{self.title}')>"
