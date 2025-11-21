from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Major(Base):
    __tablename__ = "majors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    major_name: Mapped[str] = mapped_column(String, unique=True, index=True)

    students = relationship("Student", back_populates="major")
