"""
Session model for interview session management.

Sessions represent individual AI interview practice sessions
conducted by students.

Schema Reference:
- migrations/001_initial_schema.sql lines 74-81
- migrations/007_add_session_type_to_sessions.sql (adds type column)
"""
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import String, ForeignKey, CheckConstraint, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.document import Document
    from app.models.summary import Summary
    from app.models.detailed_feedback import DetailedFeedback
    from app.models.next_step import NextStep


class Session(Base):
    """
    Session entity for interview sessions.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        student_id: Foreign key to students (cascade delete)
        status: Session status (e.g., 'pending', 'in_progress', 'completed', 'failed')
        type: Session type ('job' or 'university')
        total_score: Final session score (0.0 - 10.0)
        completed_at: Timestamp when session was completed
        created_at: Timestamp when session was created
        
    Relationships:
        student: The Student who conducted this session
        document: The uploaded document for this session (one-to-one)
        summary: The summary feedback for this session (one-to-one)
        feedbacks: Detailed feedback items for this session
        next_steps: Recommended next steps for this session
    """
    __tablename__ = "sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    status: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Session status: pending, in_progress, completed, failed",
    )
    
    # Session type added in migration 007
    type: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="job",
        server_default="job",
        comment="Session type: job or university",
    )
    
    total_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Final session score (0.0 - 10.0)",
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default="now()",
        nullable=False,
    )
    
    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="sessions",
        lazy="joined",
    )
    
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="session",
        uselist=False,  # One-to-one
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    summary: Mapped[Optional["Summary"]] = relationship(
        "Summary",
        back_populates="session",
        uselist=False,  # One-to-one (unique constraint)
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    feedbacks: Mapped[List["DetailedFeedback"]] = relationship(
        "DetailedFeedback",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="DetailedFeedback.question_order",
    )
    
    next_steps: Mapped[List["NextStep"]] = relationship(
        "NextStep",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="NextStep.next_step_order",
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "total_score >= 0 AND total_score <= 10",
            name="sessions_total_score_check",
        ),
        CheckConstraint(
            "type IN ('job', 'university')",
            name="sessions_type_check",
        ),
        Index("idx_sessions_student_id", "student_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, student_id={self.student_id}, status='{self.status}', type='{self.type}')>"
