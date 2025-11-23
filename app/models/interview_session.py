from sqlalchemy import String, Integer, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin

class InterviewSession(Base, TimestampMixin):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"))
    status: Mapped[str] = mapped_column(String)
    completed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    total_score: Mapped[Numeric] = mapped_column(Numeric, nullable=True)

    student = relationship("Student", back_populates="sessions")
    documents = relationship("Document", back_populates="session")
    score = relationship("InterviewScore", back_populates="session", uselist=False)
    summary = relationship("InterviewSummary", back_populates="session", uselist=False)
    detailed_feedbacks = relationship("InterviewDetailedFeedback", back_populates="session")
    next_steps = relationship("InterviewNextStep", back_populates="session")
