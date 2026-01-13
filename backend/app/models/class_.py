"""
Class model for student class/grade management.

Classes represent student groupings within a school,
typically organized by grade level.

Schema Reference: migrations/001_initial_schema.sql lines 53-57
"""
from typing import TYPE_CHECKING, List

from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.student import Student


class Class(Base):
    """
    Class entity representing a student class/grade grouping.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        class_name: Name of the class (e.g., "Class 1-A", "Senior Class")
        grade_level: Grade level (1, 2, or 3 per CHECK constraint)
        students: Back-reference to Student entities in this class
    
    Note: Using class_ as filename since 'class' is a Python reserved keyword.
    """
    __tablename__ = "classes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_name: Mapped[str] = mapped_column(String, nullable=False)
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    students: Mapped[List["Student"]] = relationship(
        "Student",
        back_populates="current_class",
        lazy="noload",  # No direct usage of Class.students anywhere.
    )
    
    # Check constraint for grade_level
    __table_args__ = (
        CheckConstraint(
            "grade_level IN (1, 2, 3)",
            name="classes_grade_level_check",
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Class(id={self.id}, class_name='{self.class_name}', grade_level={self.grade_level})>"
