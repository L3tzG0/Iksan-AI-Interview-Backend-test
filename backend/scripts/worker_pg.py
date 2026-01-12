import asyncio
import time
import logging
import os
import sys
from typing import Dict, Any

# Setup Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.job_processor import (
    process_evaluation_job, process_interview_job_gpt, 
    process_interview_uni_gpt
)
from app.services.queue_service_pg import QueueServicePG
from app.core.config import settings
from app.core.database import get_db_context, get_engine, close_db

# Initialization
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - PG_WORKER - %(message)s'
)
logger = logging.getLogger(__name__)

stop_event = asyncio.Event()

next_allowed_start_time = time.time()

async def wrapper_process_job(job_data: Dict[str, Any], queue_service: QueueServicePG):
    """
    Handles the actual job execution logic in the background.
    The try/finally block ensures the DB is updated even if the LLM call fails.
    """
    queue_id = job_data.get("_queue_id")
    job_type = job_data.get("job_type")
    session_id = job_data.get("session_id", "UNK")

    async with get_db_context() as db:
        try:
            logger.info(f"Starting execution: Job {queue_id} (Session {session_id})")

            if job_type == "evaluation":
                await process_evaluation_job(job_data, db)
            elif job_type == "interview_generation_gpt":
                await process_interview_job_gpt(job_data, db)
            elif job_type == "university_generation_gpt":
                await process_interview_uni_gpt(job_data, db)
            else:
                logger.warning(f"Unknown job type: {job_type}")
                
        except Exception as e:
            logger.error(f"Error in job {queue_id}: {e}", exc_info=True)
        finally:
            try:
                await queue_service.mark_completed(queue_id)
                logger.info(f"Task Completed: QueueID {queue_id}")
            except Exception as fe:
                logger.error(f"Finalize Error (QID {queue_id}): {fe}")

async def run_worker():
    global next_allowed_start_time

    async_engine = get_engine()
    queue_service = QueueServicePG(async_engine)
    
    next_allowed_start_time = time.time()
    TARGET_INTERVAL = settings.JOB_PROCESSING_INTERVAL_SECONDS 

    logger.info(f"Worker Online. Target interval between starts: {TARGET_INTERVAL}s")
    logger.info("Database connection using SQLAlchemy AsyncSession")

    while True:
        # 1. Enforce Start-Time Throttling
        current_time = time.time()
        wait_time = max(0, next_allowed_start_time - current_time)
        if wait_time > 0:
            await asyncio.sleep(wait_time) 

        # 2. Dequeue a job (Non-blocking I/O)
        job_data = await queue_service.dequeue_job()

        if job_data:
            # 3. Dispatch to background without awaiting
            asyncio.create_task(wrapper_process_job(job_data, queue_service))
            
            # 4. Schedule the next window
            next_allowed_start_time = time.time() + TARGET_INTERVAL
        else:
            # Idle poll sleep
            await asyncio.sleep(1.0) 


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(run_worker())
    except KeyboardInterrupt:
        logger.info("Interrupt received, stopping worker...")
        stop_event.set()
        # Give pending tasks a moment to finish and run the 'finally' block
        loop.run_until_complete(asyncio.sleep(0.5))
    finally:
        loop.close()
        logger.info("Process exited.")