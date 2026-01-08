"""
API endpoints for majors.

Updated to use SQLAlchemy AsyncSession instead of Supabase.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.major import Major
from app.schemas.major import MajorResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[MajorResponse])
async def read_majors(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(default=None, description="Search by major name")
):
    """
    Get all majors with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **search**: Search by major name (partial match)
    """
    # Build query
    query = select(Major)
    count_query = select(func.count()).select_from(Major)
    
    if search:
        query = query.where(Major.major_name.ilike(f'%{search}%'))
        count_query = count_query.where(Major.major_name.ilike(f'%{search}%'))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated items
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    majors = result.scalars().all()
    
    # Convert to response format
    items = [{"id": m.id, "major_name": m.major_name} for m in majors]
    
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)
