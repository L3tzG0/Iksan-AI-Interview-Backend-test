from supabase import Client
from fastapi import HTTPException, status
from app.schemas.interview_score import InterviewScoreCreate

class InterviewScoreService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_score(self, score: InterviewScoreCreate):
        pass

    async def get_score(self, score_id: int):
        pass
