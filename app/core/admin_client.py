"""
Admin Supabase client utilities.

Provides a context manager that yields a fresh Supabase AsyncClient for
Auth Admin operations. This avoids stale Authorization headers and ensures
proper cleanup of HTTP resources.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from supabase import AsyncClient, acreate_client

from app.core.config import settings


@asynccontextmanager
async def get_admin_client() -> AsyncGenerator[AsyncClient, None]:
    """Yield a fresh Supabase client for auth.admin operations.

    A new client instance ensures the service role key is used directly and
    prevents token refresh side effects from long-lived clients. Connections are
    closed after use to avoid leaking HTTP resources.
    """
    client = await acreate_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    try:
        yield client
    finally:
        try:
            await client.postgrest.aclose()
        except Exception:
            pass
