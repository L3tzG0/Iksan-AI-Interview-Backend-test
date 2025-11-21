from supabase import Client
from fastapi import HTTPException, status
from app.schemas.interview_session import InterviewSessionCreate

class InterviewSessionService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def create_session(self, session: InterviewSessionCreate):
        pass

    async def get_session(self, session_id: int):
        pass

    async def update_session(self, session_id: int, session: InterviewSessionUpdate):
        pass
