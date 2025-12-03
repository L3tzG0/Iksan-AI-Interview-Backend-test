from typing import Optional, Tuple, List
from supabase import AsyncClient
from fastapi import HTTPException, status
from app.schemas.teacher import TeacherCreate, TeacherUpdate

# Explicit columns to select for teachers (avoiding SELECT *)
TEACHER_COLUMNS = "id, user_id, school_id, created_at, updated_at"
TEACHER_COLUMNS_WITH_USER = """
    id, user_id, school_id, created_at, updated_at,
    user_profiles(id, email, full_name, role_id)
"""
TEACHER_COLUMNS_WITH_DETAILS = """
    id, user_id, school_id, created_at, updated_at,
    user_profiles(id, email, full_name, role_id),
    schools(id, school_name)
"""


class TeacherService:
    """
    Service for teacher database operations.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def create_teacher(self, teacher: TeacherCreate):
        """Create a new teacher"""
        try:
            response = await self.supabase.table('teachers').insert(teacher.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher(self, teacher_id: int):
        """Get teacher by ID with explicit column selection"""
        try:
            response = await self.supabase.table('teachers').select(TEACHER_COLUMNS).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_with_user(self, teacher_id: int):
        """
        Get teacher by ID with related user profile info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = await self.supabase.table('teachers').select(
                TEACHER_COLUMNS_WITH_USER
            ).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_with_details(self, teacher_id: int):
        """
        Get teacher by ID with user profile and school info.
        Uses relational select to avoid N+1 queries.
        """
        try:
            response = await self.supabase.table('teachers').select(
                TEACHER_COLUMNS_WITH_DETAILS
            ).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_all_teachers(
        self,
        skip: int = 0,
        limit: int = 20,
        school_id: Optional[int] = None,
        with_user: bool = False,
        with_details: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all teachers with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            school_id: Filter by school ID
            with_user: Include related user profile data
            with_details: Include user profile and school data (overrides with_user)
        
        Returns:
            Tuple of (list of teachers, total count)
        """
        try:
            if with_details:
                columns = TEACHER_COLUMNS_WITH_DETAILS
            elif with_user:
                columns = TEACHER_COLUMNS_WITH_USER
            else:
                columns = TEACHER_COLUMNS
            
            # Build query with filters - count='exact' returns total count with data
            query = self.supabase.table('teachers').select(columns, count='exact')
            if school_id is not None:
                query = query.eq('school_id', school_id)
            
            # Single query with pagination - PostgreSQL returns total count with data
            response = await query.offset(skip).limit(limit).execute()
            total = response.count if response.count is not None else 0
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_teacher(self, teacher_id: int, teacher_data: TeacherUpdate):
        """Update teacher information (e.g., school assignment)"""
        try:
            response = await self.supabase.table('teachers').update(
                teacher_data.model_dump(exclude_unset=True)
            ).eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_by_user_id(self, user_id: str):
        """Get teacher by user_id (UUID)"""
        try:
            response = await self.supabase.table('teachers').select(TEACHER_COLUMNS).eq('user_id', user_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
