from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from supabase import acreate_client, AsyncClient
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Initialize async Supabase client and store in app.state
    - Shutdown: Cleanup resources
    
    This pattern ensures:
    - Single async client instance shared across all requests
    - Explicit lifecycle management
    - Better testability (can override app.state in tests)
    - Proper async connection pooling under concurrent load
    """
    # Startup: Initialize async Supabase client
    app.state.supabase = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    # Initialize rate limiter state
    app.state.limiter = limiter
    
    yield
    
    # Shutdown: Cleanup async client resources
    # Close the async client's underlying httpx session
    await app.state.supabase.postgrest.aclose()


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
