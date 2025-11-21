from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    school_name: Mapped[str] = mapped_column(String, unique=True, index=True)

    students = relationship("Student", back_populates="school")
