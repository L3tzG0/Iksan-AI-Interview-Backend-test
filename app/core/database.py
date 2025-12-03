"""
Database dependency module for Supabase client access.

This module provides a FastAPI dependency that retrieves the async Supabase client
from the application state. The client is initialized during application
startup via the lifespan context manager in main.py.

Pattern benefits:
- Single async client instance shared across all requests
- Explicit lifecycle management via lifespan
- Better testability (can override app.state in tests)
- Async connection pooling for high concurrency

Usage:
    @router.get("/example")
    async def example_endpoint(
        supabase: Annotated[AsyncClient, Depends(get_supabase)]
    ):
        return await supabase.table('example').select('*').execute()
"""
from fastapi import Request
from supabase import AsyncClient


def get_supabase(request: Request) -> AsyncClient:
    """
    Dependency to get async Supabase client instance from app.state.
    
    The async Supabase client is initialized during application startup
    via the lifespan context manager and stored in app.state.
    
    Args:
        request: FastAPI Request object (injected automatically)
    
    Returns:
        AsyncClient: The shared async Supabase client instance
    
    Raises:
        AttributeError: If Supabase client was not initialized in lifespan
    """
    return request.app.state.supabase
