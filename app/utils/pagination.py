"""
Pagination utilities for SQLAlchemy queries.

This module provides helper functions for implementing pagination
in database queries. Updated from Supabase PostgREST to SQLAlchemy.
"""
from typing import Tuple, List, Any, Sequence, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

# Type variable for model class
T = TypeVar("T")


async def paginate_query(
    session: AsyncSession,
    query: Select,
    skip: int,
    limit: int,
) -> Tuple[Sequence[Any], int]:
    """
    Execute a paginated SQLAlchemy query with count.
    
    Args:
        session: SQLAlchemy async session
        query: Base SQLAlchemy select query (without offset/limit)
        skip: Number of records to skip
        limit: Maximum records to return
    
    Returns:
        Tuple of (list of results, total count)
    """
    # Get total count using subquery
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute
    paginated_query = query.offset(skip).limit(limit)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    return items, total


async def paginate_query_unique(
    session: AsyncSession,
    query: Select,
    skip: int,
    limit: int,
) -> Tuple[Sequence[Any], int]:
    """
    Execute a paginated SQLAlchemy query with count, handling joins.
    
    Use this version when the query includes eager-loaded relationships
    that may produce duplicate rows.
    
    Args:
        session: SQLAlchemy async session
        query: Base SQLAlchemy select query (without offset/limit)
        skip: Number of records to skip
        limit: Maximum records to return
    
    Returns:
        Tuple of (list of results, total count)
    """
    # Get total count using subquery
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and execute with unique() for joined queries
    paginated_query = query.offset(skip).limit(limit)
    result = await session.execute(paginated_query)
    items = result.unique().scalars().all()
    
    return items, total


# =============================================================================
# Legacy Supabase pagination helpers (deprecated - for backward compatibility)
# =============================================================================

# Type alias for legacy query factory pattern
QueryFactory = Any


async def paginate_supabase_query(
    query_factory: QueryFactory,
    skip: int,
    limit: int,
) -> Tuple[List[dict], int]:
    """
    [DEPRECATED] Execute a paginated Supabase query with consistent 416 handling.
    
    This function is maintained for backward compatibility during migration.
    New code should use paginate_query() with SQLAlchemy sessions.
    
    `query_factory` must return a new query builder each time so we avoid
    in-place mutation side effects from offset/limit calls.
    """
    from postgrest.exceptions import APIError
    
    paginated_query = query_factory().offset(skip).limit(limit)
    try:
        response = await paginated_query.execute()
        total = response.count if response.count is not None else 0
        return response.data or [], total
    except APIError as exc:
        if exc.code in ("416", 416):
            count_response = await query_factory().limit(0).execute()
            total = count_response.count if count_response.count is not None else 0
            return [], total
        raise
