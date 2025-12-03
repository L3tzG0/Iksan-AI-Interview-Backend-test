from typing import Optional, Tuple, List
from supabase import Client
from fastapi import HTTPException, status
from app.schemas.class_schema import ClassCreate, ClassUpdate

# Explicit columns to select for classes (avoiding SELECT *)
CLASS_COLUMNS = "id, class_name, grade_level, homeroom_teacher_id"
CLASS_COLUMNS_WITH_TEACHER = """
    id, class_name, grade_level, homeroom_teacher_id,
    teachers(id, user_id, school_id, user_profiles(id, full_name, email), schools(id, school_name))
"""


class ClassService:
    """
    Service for class database operations.
    
    All methods are synchronous (def) because the Supabase Python client
    uses synchronous HTTP calls internally. FastAPI will automatically
    run these in a thread pool when called from async endpoints.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_class(self, class_data: ClassCreate):
        """Create a new class"""
        try:
            response = self.supabase.table('classes').insert(class_data.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_class(self, class_id: int):
        """Get class by ID with explicit column selection"""
        try:
            response = self.supabase.table('classes').select(CLASS_COLUMNS).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_class_with_teacher(self, class_id: int):
        """
        Get class by ID with homeroom teacher info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = self.supabase.table('classes').select(
                CLASS_COLUMNS_WITH_TEACHER
            ).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_all_classes(
        self,
        skip: int = 0,
        limit: int = 20,
        grade_level: Optional[str] = None,
        homeroom_teacher_id: Optional[int] = None,
        with_teacher: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all classes with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            grade_level: Filter by grade level
            homeroom_teacher_id: Filter by homeroom teacher
            with_teacher: Include teacher details
        
        Returns:
            Tuple of (list of classes, total count)
        """
        try:
            columns = CLASS_COLUMNS_WITH_TEACHER if with_teacher else CLASS_COLUMNS
            
            query = self.supabase.table('classes').select(columns, count='exact')
            
            if grade_level is not None:
                query = query.eq('grade_level', grade_level)
            if homeroom_teacher_id is not None:
                query = query.eq('homeroom_teacher_id', homeroom_teacher_id)
            
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def update_class(self, class_id: int, class_data: ClassUpdate):
        """Update class information"""
        try:
            response = self.supabase.table('classes').update(
                class_data.model_dump(exclude_unset=True)
            ).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
