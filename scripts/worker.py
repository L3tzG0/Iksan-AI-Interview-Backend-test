import asyncio
import time
import logging
import redis
import os
import sys
from supabase import create_client, Client
# Removed unused imports (json, dotenv, urlparse)

# Local Imports
# NOTE: We assume these services exist relative to the root directory
# Adjust path to correctly find app/core/config.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.services.job_processor import process_interview_job
from app.services.queue_service import QueueService
from app.core.config import settings # <-- Use centralized settings

# --- Initialization ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - WORKER - %(message)s')

def initialize_supabase() -> Client:
    """Initializes and returns the Supabase client using settings."""
    try:
        logging.info("Initializing Supabase Client...")
        
        # Access config values directly from settings
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
             raise ValueError("Supabase credentials are not fully configured.")
             
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        logging.error(f"Failed to initialize Supabase: {e}")
        sys.exit(1)

def initialize_redis() -> redis.Redis:
    """Initializes and returns the Redis client using settings properties for URL parsing."""
    try:
        # Access computed properties from settings
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

# --- The Main Loop ---

async def run_worker():
    """
    Main function for the consumer process.
    """
    logging.info("Starting Interview Generation Worker...")
    
    # Initialize services
    supabase = initialize_supabase()
    redis_conn = initialize_redis()
    queue_service = QueueService(redis_conn)
    
    # Use a basic event loop runner for the async job processing logic
    loop = asyncio.get_event_loop()

    while True:
        start_time = time.time()
        
        # 1. Block and Wait for a Job (BLPOP)
        logging.info(f"Waiting for a job in queue '{queue_service.QUEUE_NAME}'...")
        
        # Run synchronous blocking operation in a thread pool executor
        job_data = await loop.run_in_executor(
            None, 
            lambda: queue_service.dequeue_job(timeout=30)
        )

        if job_data:
            session_id = job_data.get("session_id", "UNKNOWN")
            job_type = job_data.get("job_type", "UNKNOWN")
            logging.info(f"Job pulled for Session ID: {session_id}, Type: {job_type}. Starting processing...")
            
            try:
                # 2. Dispatch the Job based on type
                if job_type == "interview_generation":
                    await process_interview_job(job_data, supabase)
                else:
                    logging.warning(f"Session ID: {session_id} -> Skipping unknown job type: {job_type}")

                logging.info(f"Session ID: {session_id} -> Job finished successfully.")
                
            except Exception as e:
                logging.error(f"Session ID: {session_id} -> Critical failure during processing: {e}")
                
            # 3. Enforce Global Rate Limit Pause
            end_time = time.time()
            processing_duration = end_time - start_time
            
            # Use the setting from config.py
            time_to_sleep = settings.JOB_PROCESSING_INTERVAL_SECONDS - processing_duration
            
            if time_to_sleep > 0:
                logging.info(f"Rate Limiting: Pausing for {time_to_sleep:.2f} seconds.")
                time.sleep(time_to_sleep)
            else:
                # Use the setting from config.py
                logging.warning(f"Processing took {processing_duration:.2f}s, exceeding target interval of {settings.JOB_PROCESSING_INTERVAL_SECONDS}s. No pause applied.")
        else:
            # BLPOP timed out, just continue the loop
            logging.info("Queue empty, continuing wait...")

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logging.info("Worker gracefully shutting down.")
    except Exception as e:
        logging.critical(f"Worker crashed due to an unhandled exception: {e}")