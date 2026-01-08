"""
Job Processor for background interview processing tasks.

Handles async job processing for interview generation and evaluation
using SQLAlchemy AsyncSession.
"""
import asyncio
from typing import Dict, Any, List
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.question_generator import generate_interview_questions
from app.services.university_question_generator import generate_university_prep_questions
from app.services.evaluation_generator import generate_session_evaluation
from app.services.rag_service import retrieve_questions_from_rag
from app.services.feedback_service import FeedbackService
from app.services.interview_session_service import InterviewSessionService
from app.schemas.interview_session import GeneratedQuestion, QuestionAnswerPair 
from app.schemas.summary import InterviewSummaryCreate
from app.schemas.next_step import InterviewNextStepCreate

# from app.services.question_generator_qwen import generate_interview_questions_qwen
from app.services.question_generator_gpt import generate_interview_questions_gpt
from app.services.university_question_generator_gpt import generate_university_prep_questions_gpt
from app.services.evaluation_generator_gpt import generate_session_evaluation_gpt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - JobProcessor - %(message)s')

# Constants for retry logic
MAX_JOB_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 7


async def process_interview_job(
    job_data: Dict[str, Any], 
    db: AsyncSession
) -> List[GeneratedQuestion]:
    """
    Executes the slow, core logic for an interview session job, with retry mechanism.
    This function is executed by the background worker process.
    
    Args:
        job_data: Dictionary containing session_id, cv_text, field, role
        db: SQLAlchemy AsyncSession for database operations
    
    Returns:
        List of generated questions
    """
    session_id = job_data["session_id"]
    cv_text = job_data["cv_text"]
    field = job_data["field"]
    role = job_data["role"]
    
    session_service = InterviewSessionService(db)
    feedback_service = FeedbackService(db)

    try:
        logging.info(f"Session {session_id}: Starting RAG query and LLM generation...")
        
        # 1. Update session status to 'generating'
        await session_service.update_session_status(session_id, status="generating")

        generated_questions_list = None
        for attempt in range(MAX_JOB_RETRIES):
            try:
                logging.info(f"Session {session_id}: Attempt {attempt + 1}/{MAX_JOB_RETRIES} to generate questions...")
                
                # 2. RAG Implementation
                rag_context = await retrieve_questions_from_rag(cv_text=cv_text, q_type="job", k=5)

                # 3. Generate interview questions using LLM (The slow step)
                generated_questions_list = await generate_interview_questions(
                    cv_text=cv_text,
                    field=field,
                    role=role,
                    reference_questions=rag_context.reference_questions
                )
                # Success! Break the retry loop
                break 
            except Exception as e:
                if attempt == MAX_JOB_RETRIES - 1:
                    raise # Re-raise on final failure
                
                # Log the retry and wait with exponential backoff
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(f"Session {session_id}: Question generation failed (Attempt {attempt + 1}). Retrying in {wait_time}s. Error: {e}")
                await asyncio.sleep(wait_time)

        # Check if generation was successful after all retries
        if generated_questions_list is None:
            raise Exception("Question generation failed after all retries.")
            
        # 4. Create detailed_feedbacks records
        await feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        # 5. Update final status
        await session_service.update_session_status(session_id, status="in_progress")
        logging.info(f"Session {session_id}: Successfully processed and updated to in_progress.")
        
        return generated_questions_list

    except Exception as e:
        # If processing fails after all retries, mark the session as failed
        logging.error(f"Session {session_id}: Processing failed after all retries. Error: {e}")
        await session_service.update_session_status(session_id, status="failed")
        return []
    

async def process_interview_uni(
    job_data: Dict[str, Any], 
    db: AsyncSession
) -> List[GeneratedQuestion]:
    """
    Executes the core logic for a university preparation session job, with retry mechanism.
    
    Args:
        job_data: Dictionary containing session_id, student_record_text, universities, departments
        db: SQLAlchemy AsyncSession for database operations
    
    Returns:
        List of generated questions
    """
    session_id = job_data["session_id"]
    student_record_text = job_data["student_record_text"]
    universities = job_data["universities"]
    departments = job_data["departments"]
    
    session_service = InterviewSessionService(db)
    feedback_service = FeedbackService(db)

    try:
        logging.info(f"Session {session_id}: Starting University Prep RAG query and LLM generation...")
        
        # 1. Update session status to 'generating'
        await session_service.update_session_status(session_id, status="generating")

        generated_questions_list = None
        for attempt in range(MAX_JOB_RETRIES):
            try:
                logging.info(f"Session {session_id}: Attempt {attempt + 1}/{MAX_JOB_RETRIES} to generate university prep questions...")
                
                # 2. RAG Implementation
                academic_context = await retrieve_questions_from_rag(cv_text=student_record_text, q_type="uni", k=5)

                # 3. Generate questions using LLM
                generated_questions_list = await generate_university_prep_questions(
                    student_record_text=student_record_text,
                    universities=universities,
                    departments=departments,
                    reference_questions=academic_context.reference_questions
                )
                # Success! Break the retry loop
                break
            except Exception as e:
                if attempt == MAX_JOB_RETRIES - 1:
                    raise # Re-raise on final failure
                
                # Log the retry and wait with exponential backoff
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(f"Session {session_id}: University Prep generation failed (Attempt {attempt + 1}). Retrying in {wait_time}s. Error: {e}")
                await asyncio.sleep(wait_time)

        # Check if generation was successful after all retries
        if generated_questions_list is None:
            raise Exception("University Prep generation failed after all retries.")
            
        # 4. Create detailed_feedbacks records
        await feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        # 5. Update final status
        await session_service.update_session_status(session_id, status="in_progress")
        logging.info(f"Session {session_id}: Successfully processed University Prep and updated to in_progress.")
        
        return generated_questions_list

    except Exception as e:
        # If processing fails after all retries, mark the session as failed
        logging.error(f"Session {session_id}: University Prep Processing failed after all retries. Error: {e}")
        await session_service.update_session_status(session_id, status="failed")
        return []
    

async def process_evaluation_job(
    job_data: Dict[str, Any], 
    db: AsyncSession
) -> None:
    """
    Executes the core LLM evaluation and database update logic for a completed session.
    Implements a retry mechanism for transient LLM API errors.
    
    Args:
        job_data: Dictionary containing session_id, qa_pairs, q_type
        db: SQLAlchemy AsyncSession for database operations
    """
    session_id = job_data["session_id"]
    
    # Reconstruct the list of QuestionAnswerPair objects from serialized data
    qa_pairs_dicts = job_data["qa_pairs"]
    qa_pairs = [QuestionAnswerPair(**p) for p in qa_pairs_dicts]
    
    q_type = job_data["q_type"]

    session_service = InterviewSessionService(db)
    feedback_service = FeedbackService(db)
    
    try:
        logging.info(f"Session {session_id}: Starting LLM evaluation...")
        
        # 1. Update session status to 'evaluating'
        await session_service.update_session_status(session_id, status="evaluating")

        evaluation_result = None
        for attempt in range(MAX_JOB_RETRIES):
            try:
                # 2. Call LLM Evaluation Service (The heavy lifting)
                logging.info(f"Session {session_id}: Attempt {attempt + 1}/{MAX_JOB_RETRIES} to call LLM...")
                # evaluation_result = await generate_session_evaluation(qa_pairs, q_type)
                evaluation_result = await generate_session_evaluation_gpt(qa_pairs, q_type)
                # Success! Break the retry loop
                break 
            except Exception as e:
                # Check if it's the last attempt
                if attempt == MAX_JOB_RETRIES - 1:
                    raise # Re-raise on final failure to be caught by the outer block
                
                # Log the retry and wait with exponential backoff
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(f"Session {session_id}: LLM call failed (Attempt {attempt + 1}). Retrying in {wait_time}s. Error: {e}")
                await asyncio.sleep(wait_time)

        # Check if evaluation was successful after all retries
        if evaluation_result is None:
            raise Exception("LLM evaluation failed after all retries.")

        # --- DATABASE UPDATES START HERE (Executed only on successful evaluation) ---
        
        # A. Update main session table with overall score
        overall_score_10 = round(evaluation_result.overall_scores.overall_score, 1)

        await session_service.update_session_status(
            session_id=session_id, 
            status="completed", # Final status on successful evaluation
            total_score=overall_score_10,
            completed_at=datetime.now()
        )
        logging.info(f"Session {session_id}: Main session table updated with score {overall_score_10}.")
        
        # B. Save summaries
        summary_data = InterviewSummaryCreate(
            session_id=session_id,
            strength_text=evaluation_result.session_summary.strength_text,
            areas_for_growth_text=evaluation_result.session_summary.areas_for_growth_text
        )
        await feedback_service.create_session_summary(summary=summary_data)
        logging.info(f"Session {session_id}: Summary saved.")

        # C. Save next steps
        next_step_creates = [
            InterviewNextStepCreate(
                session_id=session_id,
                next_step_order=idx + 1,
                title=ns.title,
                description_text=ns.description_text
            )
            for idx, ns in enumerate(evaluation_result.next_steps)
        ]
        await feedback_service.create_next_steps_batch(next_steps=next_step_creates)
        logging.info(f"Session {session_id}: Next steps saved.")


        # D. Update detailed feedbacks (Q&A and scores)
        qa_map = {p.question_order: p.answer_text for p in qa_pairs}
        combined_feedback_updates = []
        for fb_item in evaluation_result.per_question_feedback:
            # Convert the Pydantic object to a mutable dictionary
            update_data = fb_item.model_dump(exclude_none=True, exclude_unset=True)
            
            # Look up the corresponding answer text using the question order
            answer_text_for_q = qa_map.get(fb_item.question_order)
            
            if answer_text_for_q is not None:
                update_data["answer_text"] = answer_text_for_q
            
            combined_feedback_updates.append(update_data)

        # Send the updated list of dictionaries
        await feedback_service.update_detailed_feedbacks_batch(
            session_id=session_id,
            feedback_updates=combined_feedback_updates 
        )
        logging.info(f"Session {session_id}: Detailed feedbacks updated.")
        
        logging.info(f"Session {session_id}: Evaluation successfully processed and marked completed.")

    except Exception as e:
        # If processing fails after all retries, mark the session as failed
        logging.error(f"Session {session_id}: Evaluation processing failed after all retries. Error: {e}")
        # Ensure the session is marked as failed on error
        await session_service.update_session_status(
            session_id, 
            status="failed",
            completed_at=datetime.now()
        )
        return # Do not re-raise in the worker

async def process_interview_job_gpt(
    job_data: Dict[str, Any], 
    db: AsyncSession
) -> List[GeneratedQuestion]:
    """
    Executes the interview generation logic using GPT-4o.
    
    Args:
        job_data: Dictionary containing session_id, cv_text, field, role
        db: SQLAlchemy AsyncSession for database operations
    
    Returns:
        List of generated questions
    """
    session_id = job_data["session_id"]
    cv_text = job_data["cv_text"]
    field = job_data["field"]
    role = job_data["role"]
    
    session_service = InterviewSessionService(db)
    feedback_service = FeedbackService(db)

    try:
        logging.info(f"Session {session_id}: Starting GPT-4o generation job...")
        await session_service.update_session_status(session_id, status="generating")

        generated_questions_list = None
        for attempt in range(MAX_JOB_RETRIES):
            try:
                logging.info(f"Session {session_id}: GPT-4o Attempt {attempt + 1}/{MAX_JOB_RETRIES}")
                
                # RAG Context
                rag_context = await retrieve_questions_from_rag(cv_text=cv_text, q_type="job", k=5)

                # Call GPT-4o Service
                generated_questions_list = await generate_interview_questions_gpt(
                    cv_text=cv_text,
                    field=field,
                    role=role,
                    reference_questions=rag_context.reference_questions
                )
                break 
            except Exception as e:
                if attempt == MAX_JOB_RETRIES - 1:
                    raise
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(f"Session {session_id}: GPT-4o failed. Retrying in {wait_time}s. Error: {e}")
                await asyncio.sleep(wait_time)

        if generated_questions_list is None:
            raise Exception("GPT-4o Question generation failed after all retries.")
            
        await feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        await session_service.update_session_status(session_id, status="in_progress")
        logging.info(f"Session {session_id}: Successfully processed with GPT-4o.")
        return generated_questions_list

    except Exception as e:
        logging.error(f"Session {session_id}: GPT-4o Job failed. Error: {e}")
        await session_service.update_session_status(session_id, status="failed")
        return []
    

async def process_interview_uni_gpt(
    job_data: Dict[str, Any], 
    db: AsyncSession
) -> List[GeneratedQuestion]:
    """
    Executes the university prep generation logic using GPT-4o.
    
    Args:
        job_data: Dictionary containing session_id, student_record_text
        db: SQLAlchemy AsyncSession for database operations
    
    Returns:
        List of generated questions
    """
    session_id = job_data["session_id"]
    student_record_text = job_data["student_record_text"]
    # universities = job_data["universities"]
    # departments = job_data["departments"]
    
    session_service = InterviewSessionService(db)
    feedback_service = FeedbackService(db)

    try:
        logging.info(f"Session {session_id}: Starting GPT-4o University Prep job...")
        await session_service.update_session_status(session_id, status="generating")

        generated_questions_list = None
        for attempt in range(MAX_JOB_RETRIES):
            try:
                logging.info(f"Session {session_id}: GPT-4o Uni Attempt {attempt + 1}/{MAX_JOB_RETRIES}")
                
                # RAG Context
                academic_context = await retrieve_questions_from_rag(cv_text=student_record_text, q_type="uni", k=5)

                # Call GPT-4o Service
                generated_questions_list = await generate_university_prep_questions_gpt(
                    student_record_text=student_record_text,
                    # universities=universities,
                    # departments=departments,
                    reference_questions=academic_context.reference_questions
                )
                break
            except Exception as e:
                if attempt == MAX_JOB_RETRIES - 1:
                    raise
                wait_time = INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logging.warning(f"Session {session_id}: GPT-4o Uni failed. Retrying in {wait_time}s. Error: {e}")
                await asyncio.sleep(wait_time)

        if generated_questions_list is None:
            raise Exception("GPT-4o University Prep generation failed after all retries.")
            
        await feedback_service.create_detailed_feedbacks_batch(
            session_id=session_id,
            questions=generated_questions_list
        )
        
        await session_service.update_session_status(session_id, status="in_progress")
        logging.info(f"Session {session_id}: Successfully processed University Prep with GPT-4o.")
        return generated_questions_list

    except Exception as e:
        logging.error(f"Session {session_id}: GPT-4o University Prep job failed. Error: {e}")
        await session_service.update_session_status(session_id, status="failed")
        return []