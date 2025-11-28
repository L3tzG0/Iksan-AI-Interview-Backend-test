from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.major import MajorResponse, MajorCreate

router = APIRouter()

@router.get("/", response_model=List[MajorResponse])
def read_majors(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all majors"""
    response = supabase.table('majors').select('*').execute()
    return response.data

@router.post("/", response_model=MajorResponse)
def create_major(
    major_in: MajorCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
