import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

class QueueServicePG:
    def __init__(self, db_engine: AsyncEngine):
        self.engine = db_engine


    async def enqueue_job(self, job_data: Dict[str, Any]) -> int:
        """
        Inserts a new job into the interview_queue table.
        Used by the Main FastAPI service.
        """
        job_type = job_data.get("job_type", "unknown")
        
        query = text("""
            INSERT INTO interview_queue (job_type, payload, status) 
            VALUES (:jt, :p, 'pending')
        """)
        
        # We use .begin() to automatically commit at the end of the block
        async with self.engine.begin() as conn:
            await conn.execute(query, {
                "jt": job_type, 
                "p": json.dumps(job_data)
            })
            
        return 1
    
    async def dequeue_job(self) -> Optional[Dict[str, Any]]:
        query = text("""
            UPDATE interview_queue
            SET status = 'processing', locked_at = NOW()
            WHERE id = (
                SELECT id FROM interview_queue 
                WHERE status = 'pending' 
                ORDER BY created_at ASC 
                FOR UPDATE SKIP LOCKED LIMIT 1
            )
            RETURNING id, payload;
        """)
        
        async with self.engine.begin() as conn:
            result = await conn.execute(query)
            row = result.fetchone()
            
            if row:
                job_id, payload = row
                if isinstance(payload, str):
                    payload = json.loads(payload)
                payload["_queue_id"] = job_id 
                return payload
            return None

    async def mark_completed(self, queue_id: int):
        query = text("UPDATE interview_queue SET status = 'completed' WHERE id = :id")
        async with self.engine.begin() as conn:
            await conn.execute(query, {"id": queue_id})