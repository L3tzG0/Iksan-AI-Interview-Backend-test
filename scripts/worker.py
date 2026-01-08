"""
Background Worker for Interview Processing Jobs.

Refactored from Supabase AsyncClient to SQLAlchemy AsyncSession.
Processes interview generation and evaluation jobs from Redis queue.
"""
import asyncio
import time
import logging
import redis
import os
import sys
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

# --- Setup Imports and Path ---
# Adjust path to correctly find app/core/config.py and app/services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.job_processor import process_interview_job, process_interview_uni, process_evaluation_job, process_interview_job_gpt, process_interview_uni_gpt
from app.services.queue_service import QueueService
from app.core.config import settings
from app.core.database import get_db_context

# --- Initialization ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - WORKER - %(message)s')

# Global variable to track the next moment a job is allowed to START processing.
# This is the core of the rate limiting enforcement.
next_allowed_start_time = time.time()

def initialize_redis() -> redis.Redis:
    """Initializes and returns the Redis client."""
    try:
        host = settings.redis_host
        port = settings.redis_port
        password = settings.redis_password
        
        logging.info(f"Initializing Redis Client at {host}:{port}...")
        
        return redis.Redis(
            host=host, 
            port=port, 
            password=password, 
            decode_responses=False 
        )
    except Exception as e:
        logging.error(f"Failed to initialize Redis: {e}")
        sys.exit(1)

async def pull_job_from_redis(queue_service: QueueService, loop: asyncio.AbstractEventLoop) -> Dict[str, Any] | None:
    """Runs the blocking Redis BLPOP command in a separate thread."""
    # We use a short timeout (5s) so the main loop can periodically check rate limit status
    return await loop.run_in_executor(
        None, 
        lambda: queue_service.dequeue_job(timeout=5)
    )

# --- The Main Loop (Concurrent and Rate-Limited) ---

async def run_worker():
    """
    The main worker function that enforces rate limiting at the START of each job 
    and uses asyncio.create_task() for non-blocking concurrent processing.
    
    Uses SQLAlchemy sessions for database operations - creates a new session
    for each job to ensure proper connection management.
    """
    global next_allowed_start_time
    
    # Initialize services
    redis_conn = initialize_redis()
    queue_service = QueueService(redis_conn)
    
    # Get the event loop for running synchronous Redis calls in the executor
    loop = asyncio.get_event_loop()
    
    logging.info("Database connection using SQLAlchemy AsyncSession")
    TARGET_INTERVAL = settings.JOB_PROCESSING_INTERVAL_SECONDS # e.g., 7.0 seconds

    logging.info(f"Starting Interview Generation Worker. Target interval: {TARGET_INTERVAL}s")

    while True:
        # --- 1. ENFORCE RATE LIMIT PAUSE ---
        
        current_time = time.time()
        # Calculate how long we must wait until the next job is ALLOWED to start
        wait_time = max(0, next_allowed_start_time - current_time)
        
        if wait_time > 0:
            logging.info(f"Rate limit enforcement: Pausing for {wait_time:.2f}s before next job pull.")
            # Non-blocking pause: allows the worker thread to handle background task completions
            await asyncio.sleep(wait_time) 

        # --- 2. PULL JOB (We are now guaranteed to be past the minimum interval) ---
        
        job_data = await pull_job_from_redis(queue_service, loop)

        if job_data:
            session_id = job_data.get("session_id", "UNKNOWN")
            job_type = job_data.get("job_type", "UNKNOWN")
            
            logging.info(f"Job pulled for Session ID: {session_id}, Type: {job_type}. Scheduling concurrent execution.")
            
            try:
                # --- 3. CRITICAL: SCHEDULE CONCURRENT TASK ---
                # Create a wrapper to manage database session lifecycle for each job
                async def run_job_with_session(job_func, job_data):
                    """Wrapper that creates a new DB session for each job and ensures cleanup."""
                    async with get_db_context() as db:
                        try:
                            await job_func(job_data, db)
                        except Exception as e:
                            logging.error(f"Job processing error for {job_data.get('session_id')}: {e}", exc_info=True)
                            raise e
                
                if job_type == "interview_generation":
                    # Start the slow job in the background and continue immediately.
                    asyncio.create_task(run_job_with_session(process_interview_job, job_data))
                elif job_type == "university_generation":
                    # Start the slow job in the background and continue immediately.
                    asyncio.create_task(run_job_with_session(process_interview_uni, job_data))
                elif job_type == "evaluation":
                    # Start the slow job (LLM evaluation) in the background
                    asyncio.create_task(run_job_with_session(process_evaluation_job, job_data))
                elif job_type == "interview_generation_gpt":
                    # Start the slow job in the background
                    asyncio.create_task(run_job_with_session(process_interview_job_gpt, job_data))
                elif job_type == "university_generation_gpt":
                    # Start the slow job in the background
                    asyncio.create_task(run_job_with_session(process_interview_uni_gpt, job_data))
                else:
                    logging.warning(f"Session ID: {session_id} -> Skipping unknown job type: {job_type}")
                    
                # --- 4. UPDATE NEXT ALLOWED START TIME ---
                # Calculate the exact time the next job can start, relative to NOW.
                next_allowed_start_time = time.time() + TARGET_INTERVAL
                logging.debug(f"Next job start scheduled for: {time.ctime(next_allowed_start_time)}")

            except Exception as e:
                logging.error(f"Session ID: {session_id} -> Critical error scheduling task: {e}")
                
        else:
            # BLPOP timed out, just continue the loop
            logging.debug("Queue empty, continuing wait...")
            
if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logging.info("Worker gracefully shutting down.")
    except Exception as e:
        logging.critical(f"Worker crashed due to an unhandled exception: {e}", exc_info=True)