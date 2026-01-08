"""
API endpoints for roles.

Uses SQLAlchemy AsyncSession for database operations.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.role import Role
from app.schemas.role import RoleResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[RoleResponse])
async def read_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return")
):
    """
    Get all roles with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    """
    # Build query
    query = select(Role)
    count_query = select(func.count()).select_from(Role)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated items
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    roles = result.scalars().all()
    
    # Convert to response format
    items = [{"id": r.id, "role_name": r.role_name} for r in roles]
    
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)