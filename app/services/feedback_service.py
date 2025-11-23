from supabase import Client
from fastapi import HTTPException, status
from app.schemas.summary import InterviewSummaryCreate
from app.schemas.detailed_feedback import InterviewDetailedFeedbackCreate
from app.schemas.next_step import InterviewNextStepCreate

class FeedbackService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_summary(self, summary: InterviewSummaryCreate):
        pass

    async def create_detailed_feedback(self, feedback: InterviewDetailedFeedbackCreate):
        pass

    async def create_next_step(self, next_step: InterviewNextStepCreate):
        pass
