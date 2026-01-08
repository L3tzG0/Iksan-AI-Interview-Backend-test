"""
Student Service for student-related database operations.

Refactored from Supabase AsyncClient to SQLAlchemy AsyncSession.
Uses StudentRepository for database operations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.student import Student
from app.repositories.student_repository import StudentRepository


class StudentService:
    """
    Service for student database operations.
    
    All methods are async because SQLAlchemy AsyncSession
    uses async database calls. This ensures proper connection handling
    under concurrent load.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.repo = StudentRepository(db)

    async def get_student(self, student_id: int) -> dict:
        """
        Get student by ID (primary key).
        
        Args:
            student_id: Student's primary key ID
        
        Returns:
            dict: Student record
        """
        try:
            student = await self.repo.get_by_id(student_id)
            if not student:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return self._to_dict(student)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def consume_session_quota(self, student_id: int, expected_quota: int) -> int:
        """
        Atomically decrement interview_session_quota by 1 when the expected value matches.
        
        Uses optimistic locking pattern - only updates if the current
        quota matches the expected value. This prevents race conditions.
        
        Args:
            student_id: Student's primary key ID
            expected_quota: The expected current quota value
        
        Returns:
            int: New quota value after decrement
        
        Raises:
            HTTPException 409: If quota is exhausted or mismatch
        """
        if expected_quota <= 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Interview session quota exhausted"
            )

        try:
            success, new_quota = await self.repo.consume_quota(student_id, expected_quota)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Interview session quota could not be updated. Please try again."
                )

            # Commit the transaction
            await self.db.commit()
            
            return new_quota
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def _to_dict(self, student: Student) -> dict:
        """
        Convert Student model to dictionary.
        
        Args:
            student: Student SQLAlchemy model instance
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": student.id,
            "student_id": student.student_id,
            "user_id": str(student.user_id),
            "school_id": student.school_id,
            "major_id": student.major_id,
            "current_class_id": student.current_class_id,
            "interview_session_quota": student.interview_session_quota,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None,
        }
