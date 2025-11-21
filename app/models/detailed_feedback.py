from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class DetailedFeedback(Base):
    __tablename__ = "detailed_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))
    question_order: Mapped[int] = mapped_column(Integer)
    question_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    evaluation_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[Numeric] = mapped_column(Numeric)
    transcript: Mapped[str] = mapped_column(Text)
    audio_path: Mapped[str] = mapped_column(String)

    session = relationship("InterviewSession", back_populates="detailed_feedbacks")
