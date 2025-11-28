from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from app.core.config import settings
from app.api.v1.router import api_router


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
    
    yield
    
    # Shutdown: Cleanup (optional - httpx handles connection cleanup automatically)
    # If explicit cleanup is needed in the future, add it here
    # Example: app.state.supabase.postgrest.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to Iksan AI Interview Backend"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
