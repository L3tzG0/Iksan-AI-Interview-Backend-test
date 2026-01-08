import json
import redis
from typing import Dict, Any, Optional
from app.core.redis_client import get_redis_connection

# Define the name of the Redis queue list (Job Name)
QUEUE_NAME = "llm:interview_generation_jobs"

class QueueService:
    """
    Handles all interactions with the Redis Job Queue.
    """
    # NOTE: QUEUE_NAME is imported from the module level
    QUEUE_NAME = QUEUE_NAME 
    
    def __init__(self, redis_conn: redis.Redis):
        self.redis_conn = redis_conn

    def enqueue_job(self, job_data: Dict[str, Any]) -> int:
        """
        Pushes a new job onto the right side of the Redis list (Queue).
        """
        job_payload = json.dumps(job_data)
        queue_length = self.redis_conn.rpush(self.QUEUE_NAME, job_payload)
        return queue_length

    def dequeue_job(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Pulls a job from the left side of the Redis list (Queue).
        Uses BLPOP to block and wait for a job to appear.
        """
        # BLPOP returns a tuple (key, value)
        result = self.redis_conn.blpop(self.QUEUE_NAME, timeout=timeout)
        if result:
            # result is (b'queue_name', b'job_payload_json')
            _, job_payload_bytes = result
            job_payload_str = job_payload_bytes.decode('utf-8')
            job_data = json.loads(job_payload_str)
            return job_data
        return None