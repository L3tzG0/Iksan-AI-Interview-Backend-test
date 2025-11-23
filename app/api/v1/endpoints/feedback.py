from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.summary import InterviewSummaryResponse, InterviewSummaryCreate
from app.schemas.detailed_feedback import InterviewDetailedFeedbackResponse, InterviewDetailedFeedbackCreate
from app.schemas.next_step import InterviewNextStepResponse, InterviewNextStepCreate

router = APIRouter()

@router.post("/summaries", response_model=InterviewSummaryResponse)
async def create_summary(
    summary_in: InterviewSummaryCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass

@router.post("/detailed-feedback", response_model=InterviewDetailedFeedbackResponse)
async def create_detailed_feedback(
    feedback_in: InterviewDetailedFeedbackCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass

@router.post("/next-steps", response_model=InterviewNextStepResponse)
async def create_next_step(
    next_step_in: InterviewNextStepCreate,
    supabase: Annotated[Client, Depends(get_supabase)] = None
):
    pass
