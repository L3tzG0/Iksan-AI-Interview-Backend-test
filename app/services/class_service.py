from supabase import Client
from fastapi import HTTPException, status
from app.schemas.class_schema import ClassCreate

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
        pass

    def get_class(self, class_id: int):
        pass
