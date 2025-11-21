from sqlalchemy import Integer, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class InterviewScore(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))
    content_relevance_score: Mapped[Numeric] = mapped_column(Numeric)
    structure_score: Mapped[Numeric] = mapped_column(Numeric)
    fluency_score: Mapped[Numeric] = mapped_column(Numeric)
    confidence_score: Mapped[Numeric] = mapped_column(Numeric)
    overall_score: Mapped[Numeric] = mapped_column(Numeric)

    session = relationship("InterviewSession", back_populates="score")
