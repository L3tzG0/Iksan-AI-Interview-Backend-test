"""
Database dependency module for Supabase client access.

This module provides a FastAPI dependency that retrieves the Supabase client
from the application state. The client is initialized during application
startup via the lifespan context manager in main.py.

Pattern benefits:
- Single client instance shared across all requests
- Explicit lifecycle management via lifespan
- Better testability (can override app.state in tests)
- Connection pooling handled by underlying httpx client

Usage:
    @router.get("/example")
    def example_endpoint(
        supabase: Annotated[Client, Depends(get_supabase)]
    ):
        return supabase.table('example').select('*').execute()
"""
from fastapi import Request
from supabase import Client


def get_supabase(request: Request) -> Client:
    """
    Dependency to get Supabase client instance from app.state.
    
    The Supabase client is initialized during application startup
    via the lifespan context manager and stored in app.state.
    
    Args:
        request: FastAPI Request object (injected automatically)
    
    Returns:
        Client: The shared Supabase client instance
    
    Raises:
        AttributeError: If Supabase client was not initialized in lifespan
    """
    return request.app.state.supabase
