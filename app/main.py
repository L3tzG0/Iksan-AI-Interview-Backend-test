from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from supabase import create_client
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1.router import api_router
from app.core.redis_client import initialize_redis_client, close_redis_client 


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Initialize Supabase client and store in app.state
    - Shutdown: Cleanup resources (optional for httpx-based clients)
    
    This pattern ensures:
    - Single client instance shared across all requests
    - Explicit lifecycle management
    - Better testability (can override app.state in tests)
    - Connection pooling handled by underlying httpx client
    """
    # Startup: Initialize Supabase client
    app.state.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Initialize rate limiter state
    app.state.limiter = limiter
    
    # Initialize Redis client (Opens the connection)
    redis_client = initialize_redis_client()
    app.state.redis_client = redis_client

    yield
    
    # Shutdown: Cleanup (optional - httpx handles connection cleanup automatically)
    # If explicit cleanup is needed in the future, add it here
    # Example: app.state.supabase.postgrest.aclose()
    close_redis_client()
    


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware FIRST (before other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if settings.BACKEND_CORS_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def root(request: Request):
    return JSONResponse(content={"message": "Welcome to Iksan AI Interview Backend"})

@app.get("/health")
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def health_check(request: Request):
    return JSONResponse(content={"status": "healthy"})
