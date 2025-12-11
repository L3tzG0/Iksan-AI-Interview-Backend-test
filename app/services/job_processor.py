import asyncio
from typing import Dict, Any, List
import logging
from app.services.question_generator import generate_interview_questions
from app.services.rag_service import retrieve_questions_from_rag
from app.services.feedback_service import FeedbackService
from app.services.interview_session_service import InterviewSessionService
from app.schemas.interview_session import GeneratedQuestion # For typing
from supabase import Client
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - JobProcessor - %(message)s')


async def process_interview_job(
    job_data: Dict[str, Any], 
    supabase: Client
) -> List[GeneratedQuestion]:
    """
    Executes the slow, core logic for an interview session job.
    This function is executed by the background worker process.
    """
    session_id = job_data["session_id"]
    cv_text = job_data["cv_text"]
    field = job_data["field"]
    role = job_data["role"]
    
    session_service = InterviewSessionService(supabase)
    feedback_service = FeedbackService(supabase)

    try:
        logging.info(f"Session {session_id}: Starting RAG query and LLM generation...")
        
        # 1. Update session status to 'in_progress'
        session_service.update_session_status(session_id, status="generating")

        # 2. RAG Implementation
        rag_context = await retrieve_questions_from_rag(cv_text=cv_text, k=5)

        # 3. Generate interview questions using LLM (The slow step, approx 30 seconds)
        generated_questions_list = await generate_interview_questions(
            cv_text=cv_text,
            field=field,
            role=role,
            reference_questions=rag_context.reference_questions
        )
        
        # 4. Create detailed_feedbacks records
        feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        # 5. Update final status
        session_service.update_session_status(session_id, status="in_progress")
        logging.info(f"Session {session_id}: Successfully processed and updated to completed.")
        
        return generated_questions_list

    except Exception as e:
        # If processing fails, mark the session as failed
        logging.error(f"Session {session_id}: Processing failed. Error: {e}")
        session_service.update_session_status(session_id, status="failed")
        # Do not re-raise in the worker; just log the error and move on to the next job
        return []