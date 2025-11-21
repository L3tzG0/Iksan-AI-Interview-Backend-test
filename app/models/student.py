from sqlalchemy import Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import TimestampMixin
import uuid

class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_profiles.id"))
    school_id: Mapped[int] = mapped_column(Integer, ForeignKey("schools.id"))
    major_id: Mapped[int] = mapped_column(Integer, ForeignKey("majors.id"))
    current_class_id: Mapped[int] = mapped_column(Integer, ForeignKey("classes.id"))

    user_profile = relationship("UserProfile", back_populates="student")
    school = relationship("School", back_populates="students")
    major = relationship("Major", back_populates="students")
    current_class = relationship("Class", back_populates="students")
    sessions = relationship("InterviewSession", back_populates="student")
