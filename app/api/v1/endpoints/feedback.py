from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.summary import SummaryResponse, SummaryCreate
from app.schemas.detailed_feedback import DetailedFeedbackResponse, DetailedFeedbackCreate
from app.schemas.next_step import NextStepResponse, NextStepCreate

router = APIRouter()

@router.post("/summaries", response_model=SummaryResponse)
async def create_summary(
    summary_in: SummaryCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass

@router.post("/detailed-feedback", response_model=DetailedFeedbackResponse)
async def create_detailed_feedback(
    feedback_in: DetailedFeedbackCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass

@router.post("/next-steps", response_model=NextStepResponse)
async def create_next_step(
    next_step_in: NextStepCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass
