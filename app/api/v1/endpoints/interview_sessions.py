from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.interview_session import InterviewSessionResponse, InterviewSessionCreate

router = APIRouter()

@router.get("/", response_model=List[InterviewSessionResponse])
async def read_sessions(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all interview sessions"""
    response = supabase.table('sessions').select('*').execute()
    return response.data

@router.post("/", response_model=InterviewSessionResponse)
async def create_session(
    session_in: InterviewSessionCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
