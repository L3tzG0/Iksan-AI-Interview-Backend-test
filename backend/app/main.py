"""
FastAPI Application Main Entry Point.

Uses SQLAlchemy for all database operations.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.core.database import init_db, close_db
from app.api.v1.router import api_router
from app.api.v1.endpoints.stt import http_client, executor

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(
        send_default_pii=True,
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        integrations=[
            StarletteIntegration(transaction_style="url"),
            FastApiIntegration(transaction_style="url"),
        ],
        attach_stacktrace=True,
        before_send=lambda event, hint: event if settings.ENVIRONMENT != "development" else None,
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Handles startup and shutdown events:
    - Startup: Initialize SQLAlchemy engine
    - Shutdown: Cleanup all resources
    
    This pattern ensures:
    - Single async engine instance shared across all requests
    - Explicit lifecycle management
    - Better testability (can override app.state in tests)
    - Proper async connection pooling under concurrent load
    """
    # Startup: Initialize SQLAlchemy async engine
    if settings.DATABASE_URL:
        await init_db()
    
    # Initialize rate limiter state
    app.state.limiter = limiter
    
    yield
    
    # Shutdown: Close SQLAlchemy engine (new)
    await close_db()
    
    # STT related shutdown
    await http_client.aclose()
    executor.shutdown(wait=True)


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0

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
