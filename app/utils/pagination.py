"""
Pagination utilities for SQLAlchemy queries.

This module provides helper functions for implementing pagination
in database queries.
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
