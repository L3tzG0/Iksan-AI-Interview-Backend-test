from supabase import Client
from fastapi import HTTPException, status
from app.schemas.summary import SummaryCreate
from app.schemas.detailed_feedback import DetailedFeedbackCreate
from app.schemas.next_step import NextStepCreate

class FeedbackService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_summary(self, summary: SummaryCreate):
        pass

    async def create_detailed_feedback(self, feedback: DetailedFeedbackCreate):
        pass

    async def create_next_step(self, next_step: NextStepCreate):
        pass
