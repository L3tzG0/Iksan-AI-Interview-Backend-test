from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.school import SchoolResponse, SchoolCreate

router = APIRouter()

@router.get("/", response_model=List[SchoolResponse])
async def read_schools(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all schools"""
    response = supabase.table('schools').select('*').execute()
    return response.data

@router.post("/", response_model=SchoolResponse)
async def create_school(
    school_in: SchoolCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
