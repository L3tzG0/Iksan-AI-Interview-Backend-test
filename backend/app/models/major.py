"""
Major model for academic major/department management.

Majors are reference data representing academic departments
or fields of study that students are enrolled in.

Schema Reference: 
- migrations/001_initial_schema.sql lines 24-27
- migrations/003_student_registration.sql (adds major_number)
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, CHAR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student


class Major(Base):
    """
    Major entity representing an academic major/department.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        major_name: Unique major name
        major_number: 4-character code for student ID generation (e.g., '0001')
        students: Back-reference to Student entities enrolled in this major
    
    Note: The migration shows CHAR(4) but the schema comment says 4-digit.
          Verify with actual database if discrepancy exists.
    """
    __tablename__ = "majors"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    major_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    major_number: Mapped[Optional[str]] = mapped_column(
        CHAR(4),
        unique=True,
        nullable=True,
        comment="4-digit major code for student ID generation",
    )
    
    # Relationships
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="major",
        lazy="noload", # No direct usage of Major.students anywhere.
    )
    
    def __repr__(self) -> str:
        return f"<Major(id={self.id}, major_name='{self.major_name}', major_number='{self.major_number}')>"
