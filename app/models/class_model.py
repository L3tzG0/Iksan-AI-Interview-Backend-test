from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_name: Mapped[str] = mapped_column(String, index=True)
    grade_level: Mapped[str] = mapped_column(String)
    homeroom_teacher_id: Mapped[int] = mapped_column(Integer, ForeignKey("teachers.user_id"))

    homeroom_teacher = relationship("Teacher", back_populates="classes")
    students = relationship("Student", back_populates="current_class")
