from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.interview_score import InterviewScoreResponse, InterviewScoreCreate

router = APIRouter()

@router.get("/", response_model=List[InterviewScoreResponse])
async def read_scores(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all interview scores"""
    response = supabase.table('scores').select('*').execute()
    return response.data

@router.post("/", response_model=InterviewScoreResponse)
async def create_score(
    score_in: InterviewScoreCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
