from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("sessions.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    document_path: Mapped[str] = mapped_column(String)
    processed_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session = relationship("InterviewSession", back_populates="documents")
