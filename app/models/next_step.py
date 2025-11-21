from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class NextStep(Base):
    __tablename__ = "next_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))
    title: Mapped[str] = mapped_column(String)
    description_text: Mapped[str] = mapped_column(Text)

    session = relationship("InterviewSession", back_populates="next_steps")
