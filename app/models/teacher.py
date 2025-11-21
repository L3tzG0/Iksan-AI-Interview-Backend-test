from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), primary_key=True)

    user = relationship("User", back_populates="teacher")
    classes = relationship("Class", back_populates="homeroom_teacher")
