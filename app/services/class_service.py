from supabase import Client
from fastapi import HTTPException, status
from app.schemas.class_schema import ClassCreate

class ClassService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_class(self, class_data: ClassCreate):
        pass

    async def get_class(self, class_id: int):
        pass
