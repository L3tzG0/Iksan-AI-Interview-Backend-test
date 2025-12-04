from typing import Optional, Tuple, List
from supabase import AsyncClient
from postgrest.exceptions import APIError
from fastapi import HTTPException, status
from app.schemas.class_schema import ClassCreate, ClassUpdate

# Explicit columns to select for classes (avoiding SELECT *)
CLASS_COLUMNS = "id, class_year, homeroom_teacher_id"
CLASS_COLUMNS_WITH_TEACHER = """
    id, class_year, homeroom_teacher_id,
    teachers(id, user_id, school_id, user_profiles(id, full_name, email), schools(id, school_name))
"""


class ClassService:
    """
    Service for class database operations.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def create_class(self, class_data: ClassCreate):
        """Create a new class"""
        try:
            response = await self.supabase.table('classes').insert(class_data.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_class(self, class_id: int):
        """Get class by ID with explicit column selection"""
        try:
            response = await self.supabase.table('classes').select(CLASS_COLUMNS).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_class_with_teacher(self, class_id: int):
        """
        Get class by ID with homeroom teacher info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = await self.supabase.table('classes').select(
                CLASS_COLUMNS_WITH_TEACHER
            ).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_all_classes(
        self,
        skip: int = 0,
        limit: int = 20,
        class_year: Optional[int] = None,
        homeroom_teacher_id: Optional[int] = None,
        with_teacher: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all classes with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            class_year: Filter by class year
            homeroom_teacher_id: Filter by homeroom teacher
            with_teacher: Include teacher details
        
        Returns:
            Tuple of (list of classes, total count)
        """
        try:
            columns = CLASS_COLUMNS_WITH_TEACHER if with_teacher else CLASS_COLUMNS
            
            # Build query with filters - count='exact' returns total count with data
            query = self.supabase.table('classes').select(columns, count='exact')
            if class_year is not None:
                query = query.eq('class_year', class_year)
            if homeroom_teacher_id is not None:
                query = query.eq('homeroom_teacher_id', homeroom_teacher_id)
            
            # Single query with pagination - PostgreSQL returns total count with data
            # Handle 416 error when offset exceeds total records
            try:
                response = await query.offset(skip).limit(limit).execute()
                total = response.count if response.count is not None else 0
                return response.data, total
            except APIError as e:
                if e.code == '416' or e.code == 416:  # Range not satisfiable - offset beyond total
                    count_query = self.supabase.table('classes').select(columns, count='exact')
                    if class_year is not None:
                        count_query = count_query.eq('class_year', class_year)
                    if homeroom_teacher_id is not None:
                        count_query = count_query.eq('homeroom_teacher_id', homeroom_teacher_id)
                    count_response = await count_query.limit(0).execute()
                    total = count_response.count if count_response.count is not None else 0
                    return [], total
                raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_class(self, class_id: int, class_data: ClassUpdate):
        """Update class information"""
        try:
            response = await self.supabase.table('classes').update(
                class_data.model_dump(exclude_unset=True)
            ).eq('id', class_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
