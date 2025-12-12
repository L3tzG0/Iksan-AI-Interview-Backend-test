from typing import List, Dict, Any, Optional
from supabase import AsyncClient
from fastapi import HTTPException, status
# Assuming the following schemas are defined and imported correctly
# NOTE: We use .model_dump() on the incoming Pydantic objects to convert them to dicts
from app.schemas.summary import InterviewSummaryCreate
from app.schemas.detailed_feedback import InterviewDetailedFeedbackCreate, InterviewDetailedFeedbackUpdate
from app.schemas.next_step import InterviewNextStepCreate

class FeedbackService:
    """
    Service for feedback database operations.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    # --- Session Summary Functions ---
    
    async def create_session_summary(self, summary: InterviewSummaryCreate) -> dict:
        """
        Creates the overall summary record (strengths, growth areas) for a session.
        """
        try:
            # FIX: Convert Pydantic object to dictionary for Supabase
            summary_data = summary.model_dump()
            response = await self.supabase.table('summaries').insert(summary_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create session summary record"
                )
            
            return response.data[0]
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating session summary: {str(e)}"
            )

    # --- Detailed Feedback Functions (Q&A) ---
    
    async def create_detailed_feedback(self, session_id: int):
        """
        [DEPRECATED, replaced by batch version]
        Create initial detailed_feedback record for session
        """
        # ... (unchanged)
        pass

    async def create_detailed_feedbacks_batch(
        self, 
        session_id: int, 
        # Type hint changed to List[Any] as it receives Pydantic objects
        questions: List[Any] 
    ) -> List[dict]:
        """
        [Used by /initiate]
        Create multiple detailed_feedback records for a session with generated questions.
        
        Args:
            session_id: ID of the interview session
            questions: List of Pydantic GeneratedQuestion models
        
        Returns:
            List[dict]: List of created detailed_feedback records
        """
        try:
            # FIX: Use .model_dump() to convert Pydantic objects to serializable dictionaries
            feedback_records = [
                {
                    "session_id": session_id,
                    **question_model.model_dump(), # Extracts question_order and question_text
                }
                for question_model in questions
            ]
            
            response = await self.supabase.table('detailed_feedbacks').insert(feedback_records).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create detailed_feedback records"
                )
            
            return response.data
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                # Note: Changed error message to be generic as the original error masked the type problem
                detail=f"Database error while creating detailed_feedbacks batch: {str(e)}"
            )

    async def update_detailed_feedbacks_batch(
        self, 
        session_id: int,
        # Now expects a list of Pydantic models OR dictionaries (which will include answer_text)
        feedback_updates: List[Dict[str, Any] | Any] 
    ) -> List[dict]:
        """
        [Used by /submit]
        Updates existing detailed_feedback records with answers, scores, and evaluations.
        
        Args:
            session_id: The ID of the session.
            feedback_updates: List of Pydantic DetailedEvaluationItem models OR 
                              dictionaries containing scores, evaluation, AND answer_text updates.
        """
        updated_records = []
        
        for update_item in feedback_updates:
            
            if isinstance(update_item, dict):
                # If it's already a dictionary (from combining LLM output and user answer in the endpoint)
                update_data = update_item.copy() 
            else:
                # If it's a Pydantic object (e.g., DetailedEvaluationItem from LLM)
                # Use model_dump to convert it, excluding unset fields
                update_data = update_item.model_dump(exclude_none=True, exclude_unset=True)

            # Safely extract and remove question_order from the update payload 
            # (it's used for the .eq() clause, not the .update() payload)
            question_order = update_data.pop("question_order", None)
            
            # update_data now contains all the fields to be updated, including the new 'answer_text'
            
            if question_order is None:
                continue
                
            try:
                # Update the record matching session_id AND question_order
                response = await self.supabase.table('detailed_feedbacks').update(update_data)\
                    .eq('session_id', session_id)\
                    .eq('question_order', question_order)\
                    .execute()
                
                if response.data:
                    updated_records.append(response.data[0])
                    
            except Exception as e:
                print(f"Error updating detailed feedback for Q{question_order} in session {session_id}: {e}")
                
        if not updated_records and feedback_updates:
             raise HTTPException(
                 status_code=500,
                 detail=f"Failed to update any detailed feedback records for session {session_id} - check logs for specific errors."
             )
            
        return updated_records

    # --- Next Steps Functions ---
    
    async def create_next_steps_batch(self, next_steps: List[InterviewNextStepCreate]) -> List[dict]:
        """
        [Used by /submit]
        Creates multiple next_step records for a session in a batch, assigning the order.
        """
        if not next_steps:
            return []
            
        try:
            steps_data = []
            for idx, step in enumerate(next_steps):
                # FIX: Convert Pydantic object to dictionary and add the order
                data = step.model_dump() 
                data["next_step_order"] = idx + 1
                steps_data.append(data)
                
            # Batch insert the next steps
            response = await self.supabase.table('next_steps').insert(steps_data).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create next steps records"
                )
            return response.data
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating next steps batch: {str(e)}"
            )

    async def create_next_step(self, next_step: InterviewNextStepCreate):
        """[DEPRECATED, replaced by batch version]"""
        pass