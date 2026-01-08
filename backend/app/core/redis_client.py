import redis
from typing import Optional
from app.core.config import settings
from fastapi import HTTPException, status
import logging

# Set up logging for the client initialization process
logging.basicConfig(level=logging.INFO, format='%(asctime)s - RedisClient - %(message)s')

# Global variable to hold the connected client instance
_REDIS_CLIENT: Optional[redis.Redis] = None

def initialize_redis_client() -> Optional[redis.Redis]:
    """
    Initializes and returns the Redis client connection using properties 
    from settings. This should be called once during application startup.
    """
    global _REDIS_CLIENT
    
    if _REDIS_CLIENT is not None:
        logging.warning("Redis client already initialized.")
        return _REDIS_CLIENT

    if not settings.REDIS_URL:
        logging.warning("REDIS_URL not configured. Redis services will be unavailable.")
        return None 

    try:
        # Use the computed properties from the centralized config
        r = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=0,
            # CRITICAL FIX: decode_responses must be False for a queue 
            # where JSON payloads are managed as bytes/strings by QueueService.
            decode_responses=False 
        )
        
        # Test the connection to ensure it's live
        r.ping() 
        _REDIS_CLIENT = r
        logging.info(f"Connected successfully to Redis at {settings.redis_host}:{settings.redis_port}")
        return r
    except Exception as e:
        logging.error(f"FATAL: Error connecting to Redis at {settings.redis_host}:{settings.redis_port}. Error: {e}")
        _REDIS_CLIENT = None
        return None

def close_redis_client():
    """
    Closes the global Redis client connection.
    """
    global _REDIS_CLIENT
    if _REDIS_CLIENT:
        try:
            _REDIS_CLIENT.close()
            logging.info("Redis client connection closed gracefully.")
        except Exception as e:
            logging.error(f"Error closing Redis connection: {e}")
        finally:
            _REDIS_CLIENT = None

def get_redis_connection() -> redis.Redis:
    """
    FastAPI Dependency Injection function to get the connected client.
    """
    if _REDIS_CLIENT is None:
        # If the dependency is accessed and the client is None, it means the 
        # startup failed or the service is down. Raise 503.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service is currently unavailable or disconnected. Check server logs."
        )
    return _REDIS_CLIENT