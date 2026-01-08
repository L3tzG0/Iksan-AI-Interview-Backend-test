"""
Student model for student-specific data and interview tracking.

Students are users with the 'student' role who participate in
AI-powered interview practice sessions.

Schema Reference:
- migrations/001_initial_schema.sql lines 59-67
- migrations/003_student_registration.sql (adds stored_password)
- migrations/010_add_interview_session_quota.sql (adds interview_session_quota)
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import String, Integer, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.school import School
    from app.models.major import Major
    from app.models.class_ import Class
    from app.models.session import Session


class Student(Base, TimestampMixin):
    """
    Student entity for student-specific data.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        student_id: Unique business identifier (format: SSS-MM-YY-NNNN)
        user_id: Foreign key to user_profiles (unique, one-to-one)
        school_id: Foreign key to schools (required)
        major_id: Foreign key to majors (required)
        current_class_id: Foreign key to classes (required)
        interview_session_quota: Remaining interview sessions allowed (default 2)
        stored_password: Plaintext password for admin/teacher display
        created_at: Timestamp when record was created
        updated_at: Timestamp of last modification
        
    Relationships:
        user: The student's UserProfile entity
        school: The student's School entity
        major: The student's Major entity
        current_class: The student's Class entity
        sessions: Interview sessions for this student
    """
    __tablename__ = "students"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Business identifier for the student
    student_id: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
        comment="Unique student ID (format: SSS-MM-YY-NNNN)",
    )
    
    # Link to user profile (one-to-one)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # School affiliation (required, restrict delete)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Major/department (required, restrict delete)
    major_id: Mapped[int] = mapped_column(
        ForeignKey("majors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Current class enrollment (required, restrict delete)
    current_class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Interview quota management (added in migration 010)
    interview_session_quota: Mapped[int] = mapped_column(
        Integer,
        default=2,
        server_default="2",
        nullable=False,
        comment="Remaining interview sessions student can initiate",
    )
    
    # Stored password for admin/teacher display (added in migration 003)
    stored_password: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Plaintext password for admin/teacher display",
    )
    
    # Relationships
    user: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="student",
        lazy="joined",
    )
    
    school: Mapped["School"] = relationship(
        "School",
        back_populates="students",
        lazy="joined",
    )
    
    major: Mapped["Major"] = relationship(
        "Major",
        back_populates="students",
        lazy="joined",
    )
    
    current_class: Mapped["Class"] = relationship(
        "Class",
        back_populates="students",
        lazy="joined",
    )
    
    sessions: Mapped[List["Session"]] = relationship(
        "Session",
        back_populates="student",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "interview_session_quota >= 0",
            name="students_interview_session_quota_check",
        ),
        Index("idx_students_user_id", "user_id"),
        Index("idx_students_student_id", "student_id"),
        Index("idx_students_school_id", "school_id"),
        Index("idx_students_major_id", "major_id"),
        Index("idx_students_class_id", "current_class_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_id='{self.student_id}', quota={self.interview_session_quota})>"
