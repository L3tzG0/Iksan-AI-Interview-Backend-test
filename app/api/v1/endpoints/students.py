from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.student import StudentResponse, StudentCreate

router = APIRouter()

@router.get("/", response_model=List[StudentResponse])
async def read_students(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all students"""
    response = supabase.table('students').select('*').execute()
    return response.data

@router.post("/", response_model=StudentResponse)
async def create_student(
    student_in: StudentCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
