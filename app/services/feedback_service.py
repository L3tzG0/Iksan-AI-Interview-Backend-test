from typing import List
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

    async def create_detailed_feedbacks_batch(
        self, 
        session_id: int, 
        questions: List[str]
    ) -> List[dict]:
        """
        Create multiple detailed_feedback records for a session with generated questions.
        
        Args:
            session_id: ID of the interview session
            questions: List of question texts (should be 10 questions)
        
        Returns:
            List[dict]: List of created detailed_feedback records
        
        Raises:
            HTTPException: If creation fails
        """
        try:
            # Build batch insert data with question_order and question_text
            feedback_records = [
                {
                    "session_id": session_id,
                    "question_order": idx + 1,  # 1-indexed
                    "question_text": question_text,
                    # Other fields remain NULL until answers are submitted
                }
                for idx, question_text in enumerate(questions)
            ]
            
            response = self.supabase.table('detailed_feedbacks').insert(feedback_records).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create detailed_feedback records"
                )
            
            return response.data
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating detailed_feedbacks batch: {str(e)}"
            )

    async def create_next_step(self, next_step: InterviewNextStepCreate):
        pass
