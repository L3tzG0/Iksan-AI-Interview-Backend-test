from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"))
    major_id: Mapped[int] = mapped_column(Integer, ForeignKey("majors.id"))
    current_class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"))

    user = relationship("User", back_populates="student")
    school = relationship("School", back_populates="students")
    major = relationship("Major", back_populates="students")
    current_class = relationship("Class", back_populates="students")
    sessions = relationship("InterviewSession", back_populates="student")
