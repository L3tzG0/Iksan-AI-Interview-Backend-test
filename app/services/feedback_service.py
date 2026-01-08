"""
Feedback Service for feedback database operations.

Uses FeedbackRepository for database operations with SQLAlchemy AsyncSession.
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.schemas.summary import InterviewSummaryCreate
from app.schemas.detailed_feedback import InterviewDetailedFeedbackCreate, InterviewDetailedFeedbackUpdate
from app.schemas.next_step import InterviewNextStepCreate
from app.models.detailed_feedback import DetailedFeedback
from app.models.summary import Summary
from app.models.next_step import NextStep
from app.repositories.feedback_repository import FeedbackRepository


class FeedbackService:
    """
    Service for feedback database operations.
    
    All methods are async because SQLAlchemy AsyncSession
    uses async database calls. This ensures proper connection handling
    under concurrent load.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.repo = FeedbackRepository(db)

    # =========================================================================
    # Session Summary Functions
    # =========================================================================
    
    async def create_session_summary(self, summary: InterviewSummaryCreate) -> dict:
        """
        Creates the overall summary record (strengths, growth areas) for a session.
        
        Args:
            summary: Summary creation data
        
        Returns:
            dict: Created summary record
        """
        try:
            summary_data = summary.model_dump()
            created_summary = await self.repo.create_summary(
                session_id=summary_data.get("session_id"),
                strength_text=summary_data.get("strength_text"),
                areas_for_growth_text=summary_data.get("areas_for_growth_text"),
            )
            
            await self.db.flush()
            await self.db.refresh(created_summary)
            
            return self._summary_to_dict(created_summary)
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating session summary: {str(e)}"
            )

    # =========================================================================
    # Detailed Feedback Functions (Q&A)
    # =========================================================================
    
    async def create_detailed_feedback(self, session_id: int):
        """
        [DEPRECATED, replaced by batch version]
        Create initial detailed_feedback record for session.
        """
        pass

    async def create_detailed_feedbacks_batch(
        self, 
        session_id: int, 
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
            feedback_records_data = [
                {
                    "session_id": session_id,
                    **question_model.model_dump(),  # Extracts question_order and question_text
                }
                for question_model in questions
            ]
            
            created_feedbacks = await self.repo.bulk_create_feedbacks(feedback_records_data)
            
            if not created_feedbacks:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create detailed_feedback records"
                )
            
            await self.db.flush()
            
            return [self._feedback_to_dict(fb) for fb in created_feedbacks]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating detailed_feedbacks batch: {str(e)}"
            )

    async def update_detailed_feedbacks_batch(
        self, 
        session_id: int,
        feedback_updates: List[Dict[str, Any] | Any]
    ) -> List[dict]:
        """
        [Used by /submit]
        Updates existing detailed_feedback records with answers, scores, and evaluations.
        
        Args:
            session_id: The ID of the session.
            feedback_updates: List of Pydantic DetailedEvaluationItem models OR 
                              dictionaries containing scores, evaluation, AND answer_text updates.
        
        Returns:
            List[dict]: List of updated feedback records
        """
        updated_records = []
        
        for update_item in feedback_updates:
            
            if isinstance(update_item, dict):
                update_data = update_item.copy()
            else:
                update_data = update_item.model_dump(exclude_none=True, exclude_unset=True)

            question_order = update_data.pop("question_order", None)
            
            if question_order is None:
                continue
                
            try:
                # Find the feedback record by session_id and question_order
                feedbacks = await self.repo.get_by_session(session_id)
                target_feedback = next(
                    (fb for fb in feedbacks if fb.question_order == question_order),
                    None
                )
                
                if target_feedback:
                    # Update the record
                    for key, value in update_data.items():
                        if hasattr(target_feedback, key):
                            setattr(target_feedback, key, value)
                    
                    await self.db.flush()
                    await self.db.refresh(target_feedback)
                    updated_records.append(self._feedback_to_dict(target_feedback))
                    
            except Exception as e:
                print(f"Error updating detailed feedback for Q{question_order} in session {session_id}: {e}")
                
        if not updated_records and feedback_updates:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update any detailed feedback records for session {session_id} - check logs for specific errors."
            )
            
        return updated_records

    # =========================================================================
    # Next Steps Functions
    # =========================================================================
    
    async def create_next_steps_batch(self, next_steps: List[InterviewNextStepCreate]) -> List[dict]:
        """
        [Used by /submit]
        Creates multiple next_step records for a session in a batch, assigning the order.
        
        Args:
            next_steps: List of next step creation data
        
        Returns:
            List[dict]: Created next step records
        """
        if not next_steps:
            return []
            
        try:
            steps_data = []
            for idx, step in enumerate(next_steps):
                data = step.model_dump()
                data["next_step_order"] = idx + 1
                steps_data.append(data)
            
            created_steps = await self.repo.bulk_create_next_steps(steps_data)
            
            if not created_steps:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to create next steps records"
                )
            
            await self.db.flush()
            
            return [self._next_step_to_dict(step) for step in created_steps]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database error while creating next steps batch: {str(e)}"
            )

    async def create_next_step(self, next_step: InterviewNextStepCreate):
        """[DEPRECATED, replaced by batch version]"""
        pass

    # =========================================================================
    # Helper methods for model-to-dict conversion
    # =========================================================================

    def _feedback_to_dict(self, feedback: DetailedFeedback) -> dict:
        """Convert DetailedFeedback model to dictionary."""
        return {
            "id": feedback.id,
            "session_id": feedback.session_id,
            "question_order": feedback.question_order,
            "question_text": feedback.question_text,
            "answer_text": feedback.answer_text,
            "evaluation_text": feedback.evaluation_text,
            "is_correct": feedback.is_correct,
            "content_relevance_score": float(feedback.content_relevance_score) if feedback.content_relevance_score else None,
            "structure_score": float(feedback.structure_score) if feedback.structure_score else None,
            "fluency_score": float(feedback.fluency_score) if feedback.fluency_score else None,
            "confidence_score": float(feedback.confidence_score) if feedback.confidence_score else None,
            "overall_score": float(feedback.overall_score) if feedback.overall_score else None,
        }

    def _summary_to_dict(self, summary: Summary) -> dict:
        """Convert Summary model to dictionary."""
        return {
            "id": summary.id,
            "session_id": summary.session_id,
            "strength_text": summary.strength_text,
            "areas_for_growth_text": summary.areas_for_growth_text,
        }

    def _next_step_to_dict(self, next_step: NextStep) -> dict:
        """Convert NextStep model to dictionary."""
        return {
            "id": next_step.id,
            "session_id": next_step.session_id,
            "next_step_order": next_step.next_step_order,
            "title": next_step.title,
            "description_text": next_step.description_text,
        }
