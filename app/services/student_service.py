from typing import Optional, Tuple, List
from supabase import Client
from fastapi import HTTPException, status
from app.schemas.student import StudentCreate, StudentUpdate

# Explicit columns to select for students (avoiding SELECT *)
STUDENT_COLUMNS = "id, user_id, school_id, major_id, current_class_id, created_at, updated_at"
STUDENT_COLUMNS_WITH_RELATIONS = """
    id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
    schools(id, school_name),
    majors(id, major_name),
    classes(id, class_name, grade_level)
"""


class StudentService:
    """
    Service for student database operations.
    
    All methods are synchronous (def) because the Supabase Python client
    uses synchronous HTTP calls internally. FastAPI will automatically
    run these in a thread pool when called from async endpoints.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_student(self, student: StudentCreate):
        """Create a new student"""
        try:
            response = self.supabase.table('students').insert(student.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student(self, student_id: int):
        """Get student by ID with explicit column selection"""
        try:
            response = self.supabase.table('students').select(STUDENT_COLUMNS).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student_with_details(self, student_id: int):
        """
        Get student by ID with related school, major, and class info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = self.supabase.table('students').select(
                STUDENT_COLUMNS_WITH_RELATIONS
            ).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_all_students(
        self,
        skip: int = 0,
        limit: int = 20,
        school_id: Optional[int] = None,
        major_id: Optional[int] = None,
        class_id: Optional[int] = None,
        with_details: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all students with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            school_id: Filter by school ID
            major_id: Filter by major ID
            class_id: Filter by class ID
            with_details: Include related school/major/class data
        
        Returns:
            Tuple of (list of students, total count)
        """
        try:
            columns = STUDENT_COLUMNS_WITH_RELATIONS if with_details else STUDENT_COLUMNS
            
            # Build query with filters
            query = self.supabase.table('students').select(columns, count='exact')
            
            if school_id is not None:
                query = query.eq('school_id', school_id)
            if major_id is not None:
                query = query.eq('major_id', major_id)
            if class_id is not None:
                query = query.eq('current_class_id', class_id)
            
            # Apply pagination
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def update_student(self, student_id: int, student: StudentUpdate):
        """Update student information"""
        try:
            response = self.supabase.table('students').update(student.model_dump(exclude_unset=True)).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
