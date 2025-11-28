from typing import Optional, Tuple, List
from supabase import Client
from fastapi import HTTPException, status
from app.schemas.teacher import TeacherCreate

# Explicit columns to select for teachers (avoiding SELECT *)
TEACHER_COLUMNS = "id, user_id, created_at, updated_at"
TEACHER_COLUMNS_WITH_USER = """
    id, user_id, created_at, updated_at,
    user_profiles(id, email, full_name, role_id)
"""


class TeacherService:
    """
    Service for teacher database operations.
    
    All methods are synchronous (def) because the Supabase Python client
    uses synchronous HTTP calls internally. FastAPI will automatically
    run these in a thread pool when called from async endpoints.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_teacher(self, teacher: TeacherCreate):
        """Create a new teacher"""
        try:
            response = self.supabase.table('teachers').insert(teacher.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_teacher(self, teacher_id: int):
        """Get teacher by ID with explicit column selection"""
        try:
            response = self.supabase.table('teachers').select(TEACHER_COLUMNS).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_teacher_with_user(self, teacher_id: int):
        """
        Get teacher by ID with related user profile info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = self.supabase.table('teachers').select(
                TEACHER_COLUMNS_WITH_USER
            ).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_all_teachers(
        self,
        skip: int = 0,
        limit: int = 20,
        with_user: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all teachers with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            with_user: Include related user profile data
        
        Returns:
            Tuple of (list of teachers, total count)
        """
        try:
            columns = TEACHER_COLUMNS_WITH_USER if with_user else TEACHER_COLUMNS
            
            query = self.supabase.table('teachers').select(columns, count='exact')
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
