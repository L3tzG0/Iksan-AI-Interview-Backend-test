from supabase import Client
from fastapi import HTTPException, status
from app.schemas.teacher import TeacherCreate

class TeacherService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_teacher(self, teacher: TeacherCreate):
        """Create a new teacher"""
        try:
            response = self.supabase.table('teachers').insert(teacher.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher(self, teacher_id: int):
        """Get teacher by ID"""
        try:
            response = self.supabase.table('teachers').select('*').eq('id', teacher_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
