from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.class_schema import ClassResponse, ClassCreate

router = APIRouter()

@router.get("/", response_model=List[ClassResponse])
async def read_classes(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all classes"""
    response = supabase.table('classes').select('*').execute()
    return response.data

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_in: ClassCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
