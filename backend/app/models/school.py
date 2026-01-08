"""
School model for educational institution management.

Schools are reference data representing educational institutions
where teachers and students are affiliated.

Schema Reference: 
- migrations/001_initial_schema.sql lines 19-22
- migrations/003_student_registration.sql (adds school_number)
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.teacher import Teacher
    from app.models.student import Student


class School(Base):
    """
    School entity representing an educational institution.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        school_name: Unique school name
        school_number: 3-character code for student ID generation (e.g., '001')
        teachers: Back-reference to Teacher entities affiliated with this school
        students: Back-reference to Student entities enrolled in this school
    """
    __tablename__ = "schools"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    school_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    school_number: Mapped[Optional[str]] = mapped_column(
        CHAR(3),
        unique=True,
        nullable=True,
        comment="3-digit school code for student ID generation",
    )
    
    # Relationships
    teachers: Mapped[List["Teacher"]] = relationship(
        "Teacher",
        back_populates="school",
        lazy="selectin",
    )
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="school",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<School(id={self.id}, school_name='{self.school_name}', school_number='{self.school_number}')>"
