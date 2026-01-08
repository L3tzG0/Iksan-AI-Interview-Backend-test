"""
Feedback Repository for detailed feedback database operations.

This repository handles CRUD operations for DetailedFeedback,
Summary, and NextStep models.
"""
from decimal import Decimal
from typing import Optional, Sequence, List, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detailed_feedback import DetailedFeedback
from app.models.summary import Summary
from app.models.next_step import NextStep
from app.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[DetailedFeedback]):
    """
    Repository for feedback-related entity operations.
    
    Provides methods for managing detailed feedbacks, summaries,
    and next steps associated with interview sessions.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and DetailedFeedback model."""
        super().__init__(session, DetailedFeedback)
    
    # =========================================================================
    # DetailedFeedback Operations
    # =========================================================================
    
    async def get_by_session(
        self,
        session_id: int,
    ) -> Sequence[DetailedFeedback]:
        """
        Get all detailed feedbacks for a session, ordered by question.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            List of DetailedFeedback entities ordered by question_order
        """
        stmt = (
            select(DetailedFeedback)
            .where(DetailedFeedback.session_id == session_id)
            .order_by(DetailedFeedback.question_order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_feedback(
        self,
        session_id: int,
        question_order: int,
        question_text: str,
        answer_text: Optional[str] = None,
        evaluation_text: Optional[str] = None,
        is_correct: bool = False,
        content_relevance_score: Optional[Decimal] = None,
        structure_score: Optional[Decimal] = None,
        fluency_score: Optional[Decimal] = None,
        confidence_score: Optional[Decimal] = None,
        overall_score: Optional[Decimal] = None,
    ) -> DetailedFeedback:
        """
        Create a new detailed feedback entry.
        
        Args:
            session_id: The session's primary key ID
            question_order: Order of the question
            question_text: The interview question
            answer_text: Student's answer (optional)
            evaluation_text: AI evaluation (optional)
            is_correct: Whether answer was correct
            *_score: Various score dimensions (0.0 - 10.0)
        
        Returns:
            The created DetailedFeedback entity
        """
        return await self.create(
            session_id=session_id,
            question_order=question_order,
            question_text=question_text,
            answer_text=answer_text,
            evaluation_text=evaluation_text,
            is_correct=is_correct,
            content_relevance_score=content_relevance_score,
            structure_score=structure_score,
            fluency_score=fluency_score,
            confidence_score=confidence_score,
            overall_score=overall_score,
        )
    
    async def bulk_create_feedbacks(
        self,
        feedbacks_data: List[Dict[str, Any]],
    ) -> List[DetailedFeedback]:
        """
        Create multiple feedback entries in a single operation.
        
        Args:
            feedbacks_data: List of dicts with feedback data
        
        Returns:
            List of created DetailedFeedback entities
        """
        entities = [DetailedFeedback(**data) for data in feedbacks_data]
        return await self.bulk_create(entities)
    
    async def update_evaluation(
        self,
        feedback_id: int,
        evaluation_text: str,
        is_correct: bool,
        content_relevance_score: Optional[Decimal] = None,
        structure_score: Optional[Decimal] = None,
        fluency_score: Optional[Decimal] = None,
        confidence_score: Optional[Decimal] = None,
        overall_score: Optional[Decimal] = None,
    ) -> Optional[DetailedFeedback]:
        """
        Update evaluation data for a feedback entry.
        
        Args:
            feedback_id: The feedback's primary key ID
            evaluation_text: AI evaluation text
            is_correct: Whether answer was correct
            *_score: Various score dimensions
        
        Returns:
            Updated DetailedFeedback, or None if not found
        """
        update_data = {
            "evaluation_text": evaluation_text,
            "is_correct": is_correct,
        }
        if content_relevance_score is not None:
            update_data["content_relevance_score"] = content_relevance_score
        if structure_score is not None:
            update_data["structure_score"] = structure_score
        if fluency_score is not None:
            update_data["fluency_score"] = fluency_score
        if confidence_score is not None:
            update_data["confidence_score"] = confidence_score
        if overall_score is not None:
            update_data["overall_score"] = overall_score
        
        return await self.update_by_id(feedback_id, **update_data)
    
    async def delete_by_session(self, session_id: int) -> int:
        """
        Delete all feedbacks for a session.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            Number of deleted records
        """
        return await self.delete_by(session_id=session_id)
    
    # =========================================================================
    # Summary Operations
    # =========================================================================
    
    async def get_summary_by_session(
        self,
        session_id: int,
    ) -> Optional[Summary]:
        """
        Get the summary for a session.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            Summary if found, None otherwise
        """
        stmt = select(Summary).where(Summary.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_summary(
        self,
        session_id: int,
        strength_text: Optional[str] = None,
        areas_for_growth_text: Optional[str] = None,
    ) -> Summary:
        """
        Create a summary for a session.
        
        Args:
            session_id: The session's primary key ID
            strength_text: Summary of strengths
            areas_for_growth_text: Summary of improvement areas
        
        Returns:
            The created Summary entity
        """
        summary = Summary(
            session_id=session_id,
            strength_text=strength_text,
            areas_for_growth_text=areas_for_growth_text,
        )
        self.session.add(summary)
        await self.session.flush()
        await self.session.refresh(summary)
        return summary
    
    async def update_summary(
        self,
        session_id: int,
        strength_text: Optional[str] = None,
        areas_for_growth_text: Optional[str] = None,
    ) -> Optional[Summary]:
        """
        Update or create a summary for a session.
        
        Args:
            session_id: The session's primary key ID
            strength_text: Summary of strengths
            areas_for_growth_text: Summary of improvement areas
        
        Returns:
            The updated or created Summary entity
        """
        summary = await self.get_summary_by_session(session_id)
        if summary is None:
            return await self.create_summary(
                session_id, strength_text, areas_for_growth_text
            )
        
        if strength_text is not None:
            summary.strength_text = strength_text
        if areas_for_growth_text is not None:
            summary.areas_for_growth_text = areas_for_growth_text
        
        await self.session.flush()
        await self.session.refresh(summary)
        return summary
    
    # =========================================================================
    # NextStep Operations
    # =========================================================================
    
    async def get_next_steps_by_session(
        self,
        session_id: int,
    ) -> Sequence[NextStep]:
        """
        Get all next steps for a session, ordered.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            List of NextStep entities ordered by next_step_order
        """
        stmt = (
            select(NextStep)
            .where(NextStep.session_id == session_id)
            .order_by(NextStep.next_step_order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def create_next_step(
        self,
        session_id: int,
        title: str,
        description_text: Optional[str] = None,
        next_step_order: Optional[int] = None,
    ) -> NextStep:
        """
        Create a next step recommendation.
        
        Args:
            session_id: The session's primary key ID
            title: Short title for the recommendation
            description_text: Detailed description
            next_step_order: Order in the list
        
        Returns:
            The created NextStep entity
        """
        next_step = NextStep(
            session_id=session_id,
            title=title,
            description_text=description_text,
            next_step_order=next_step_order,
        )
        self.session.add(next_step)
        await self.session.flush()
        await self.session.refresh(next_step)
        return next_step
    
    async def bulk_create_next_steps(
        self,
        next_steps_data: List[Dict[str, Any]],
    ) -> List[NextStep]:
        """
        Create multiple next steps in a single operation.
        
        Args:
            next_steps_data: List of dicts with next step data
        
        Returns:
            List of created NextStep entities
        """
        entities = [NextStep(**data) for data in next_steps_data]
        self.session.add_all(entities)
        await self.session.flush()
        for entity in entities:
            await self.session.refresh(entity)
        return entities
    
    async def delete_next_steps_by_session(self, session_id: int) -> int:
        """
        Delete all next steps for a session.
        
        Args:
            session_id: The session's primary key ID
        
        Returns:
            Number of deleted records
        """
        stmt = delete(NextStep).where(NextStep.session_id == session_id)
        result = await self.session.execute(stmt)
        return result.rowcount or 0
