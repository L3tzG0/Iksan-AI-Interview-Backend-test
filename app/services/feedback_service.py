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

    async def create_detailed_feedback(self, session_id: int):
        """
        Create initial detailed_feedback record for session
        
        Args:
            session_id: ID of the interview session
        
        Returns:
            dict: Created detailed_feedback record
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            feedback_data = {
                "session_id": session_id
                # All other fields are NULL or default
            }
            
            response = self.supabase.table('detailed_feedbacks').insert(feedback_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create detailed_feedback record"
                )
            
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating detailed_feedback: {str(e)}"
            )

    async def create_next_step(self, next_step: InterviewNextStepCreate):
        pass
