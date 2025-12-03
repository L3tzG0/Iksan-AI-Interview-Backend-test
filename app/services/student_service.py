from typing import Optional, Tuple, List
from supabase import Client
from fastapi import HTTPException, status
from app.schemas.student import StudentCreate, StudentUpdate

# Explicit columns to select for students (avoiding SELECT *)
STUDENT_COLUMNS = "id, student_id, user_id, school_id, major_id, current_class_id, created_at, updated_at"
STUDENT_COLUMNS_WITH_RELATIONS = """
    id, student_id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
    user_profiles(id, email, full_name, role_id),
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
        """Get student by ID (primary key) with explicit column selection"""
        try:
            response = self.supabase.table('students').select(STUDENT_COLUMNS).eq('id', student_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student_by_student_id(self, student_id_number: str):
        """Get student by student_id (the student's ID number, not primary key)"""
        try:
            response = self.supabase.table('students').select(STUDENT_COLUMNS).eq('student_id', student_id_number).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student_by_user_id(self, user_id: str):
        """Get student by user_id (UUID from user_profiles)"""
        try:
            response = self.supabase.table('students').select(STUDENT_COLUMNS).eq('user_id', user_id).execute()
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
        student_id_filter: Optional[str] = None,
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
            student_id_filter: Filter by student ID number (partial match)
            school_id: Filter by school ID
            major_id: Filter by major ID
            class_id: Filter by class ID
            with_details: Include related school/major/class data
        
        Returns:
            Tuple of (list of students, total count)
        """
        try:
            columns = STUDENT_COLUMNS_WITH_RELATIONS if with_details else STUDENT_COLUMNS
            
            # First get count with limit(0) to avoid 416 error when skip > total
            count_query = self.supabase.table('students').select(columns, count='exact')
            if student_id_filter is not None:
                count_query = count_query.ilike('student_id', f'%{student_id_filter}%')
            if school_id is not None:
                count_query = count_query.eq('school_id', school_id)
            if major_id is not None:
                count_query = count_query.eq('major_id', major_id)
            if class_id is not None:
                count_query = count_query.eq('current_class_id', class_id)
            count_response = count_query.limit(0).execute()
            total = count_response.count if count_response.count is not None else 0
            
            # If skip is beyond total, return empty result
            if skip >= total:
                return [], total
            
            # Re-build query for actual data fetch
            query = self.supabase.table('students').select(columns, count='exact')
            if student_id_filter is not None:
                query = query.ilike('student_id', f'%{student_id_filter}%')
            if school_id is not None:
                query = query.eq('school_id', school_id)
            if major_id is not None:
                query = query.eq('major_id', major_id)
            if class_id is not None:
                query = query.eq('current_class_id', class_id)
            
            response = query.offset(skip).limit(limit).execute()
            
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
