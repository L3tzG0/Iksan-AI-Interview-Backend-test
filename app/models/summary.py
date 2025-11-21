from sqlalchemy import Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))
    strength_text: Mapped[str] = mapped_column(Text)
    areas_for_growth_text: Mapped[str] = mapped_column(Text)

    session = relationship("InterviewSession", back_populates="summary")
