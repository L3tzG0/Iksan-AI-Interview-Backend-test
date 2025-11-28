from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.teacher import TeacherResponse, TeacherCreate

router = APIRouter()

@router.get("/", response_model=List[TeacherResponse])
def read_teachers(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all teachers"""
    response = supabase.table('teachers').select('*').execute()
    return response.data

@router.post("/", response_model=TeacherResponse)
def create_teacher(
    teacher_in: TeacherCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
