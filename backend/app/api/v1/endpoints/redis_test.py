from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
import redis
from app.core.redis_client import get_redis_connection

router = APIRouter()

@router.get("/redis/status", summary="Check Redis Connection and Functionality")
async def check_redis_status(
    # FastAPI automatically calls get_redis_connection() and injects the result
    redis_conn: Annotated[redis.Redis, Depends(get_redis_connection)]
):
    """
    Verifies that the Redis client is active and can perform simple PING, SET, and GET operations.
    If the connection failed during startup, the get_redis_connection dependency will raise 503.
    """
    try:
        # 1. PING: Verify the connection is alive
        ping_result = redis_conn.ping()
        
        # 2. SET/GET: Test read/write functionality
        test_key = "api_redis_test_key"
        test_value = "connection_successful"
        
        # SET the key with a short expiration
        redis_conn.set(test_key, test_value, ex=60) 
        
        # GET the key
        retrieved_value = redis_conn.get(test_key)

        return {
            "status": "success",
            "message": "Redis is operational and accessible.",
            "ping_result": ping_result,
            "test_key_written": test_value,
            "test_key_retrieved": retrieved_value,
            "storage_location": "External Redis Server (Railway)"
        }

    except Exception as e:
        # If any operation fails after startup, return a 500 error
        print(f"Redis operational test failed unexpectedly: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redis operational test failed: {e}"
        )