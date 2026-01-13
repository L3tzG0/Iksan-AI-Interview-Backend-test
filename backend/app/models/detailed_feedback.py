"""
DetailedFeedback model for per-question interview feedback.

DetailedFeedback stores the evaluation for each question in an
interview session, including scores across multiple dimensions.

Schema Reference: migrations/001_initial_schema.sql lines 96-109
"""
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Boolean, ForeignKey, Text, Numeric, CheckConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.session import Session


class DetailedFeedback(Base):
    """
    DetailedFeedback entity for per-question evaluation.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        session_id: Foreign key to sessions (cascade delete)
        question_order: Order of the question in the session
        question_text: The interview question asked
        answer_text: The student's transcribed answer
        evaluation_text: AI-generated evaluation narrative
        is_correct: Whether the answer was deemed correct
        content_relevance_score: Score for answer relevance (0.0 - 10.0)
        structure_score: Score for answer structure (0.0 - 10.0)
        fluency_score: Score for language fluency (0.0 - 10.0)
        confidence_score: Score for perceived confidence (0.0 - 10.0)
        overall_score: Combined overall score (0.0 - 10.0)
        
    Relationships:
        session: The Session this feedback belongs to
    """
    __tablename__ = "detailed_feedbacks"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    question_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Order of question in the interview session",
    )
    
    question_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="The interview question asked",
    )
    
    answer_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Student's transcribed answer",
    )
    
    evaluation_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated evaluation narrative",
    )
    
    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    
    # Scoring dimensions (all 0.0 - 10.0)
    content_relevance_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Score for answer relevance (0.0 - 10.0)",
    )
    
    structure_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Score for answer structure (0.0 - 10.0)",
    )
    
    fluency_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Score for language fluency (0.0 - 10.0)",
    )
    
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Score for perceived confidence (0.0 - 10.0)",
    )
    
    overall_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(3, 1),
        nullable=True,
        comment="Combined overall score (0.0 - 10.0)",
    )
    
    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="feedbacks",
        lazy="noload",  # No direct usage of DetailedFeedback.session anywhere.
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "content_relevance_score >= 0 AND content_relevance_score <= 10",
            name="detailed_feedbacks_content_relevance_score_check",
        ),
        CheckConstraint(
            "structure_score >= 0 AND structure_score <= 10",
            name="detailed_feedbacks_structure_score_check",
        ),
        CheckConstraint(
            "fluency_score >= 0 AND fluency_score <= 10",
            name="detailed_feedbacks_fluency_score_check",
        ),
        CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 10",
            name="detailed_feedbacks_confidence_score_check",
        ),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 10",
            name="detailed_feedbacks_overall_score_check",
        ),
        Index("idx_detailed_feedbacks_session_id", "session_id"),
        Index("idx_detailed_feedbacks_session_question_order", "session_id", "question_order"),
    )
    
    def __repr__(self) -> str:
        return f"<DetailedFeedback(id={self.id}, session_id={self.session_id}, question_order={self.question_order}, overall_score={self.overall_score})>"
