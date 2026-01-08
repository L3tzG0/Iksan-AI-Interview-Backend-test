"""
API endpoints for schools.

Updated to use SQLAlchemy AsyncSession instead of Supabase.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.school import School
from app.schemas.school import SchoolResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[SchoolResponse])
async def read_schools(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    search: Optional[str] = Query(default=None, description="Search by school name")
):
    """
    Get all schools with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **search**: Search by school name (partial match)
    """
    # Build query
    query = select(School)
    count_query = select(func.count()).select_from(School)
    
    if search:
        query = query.where(School.school_name.ilike(f'%{search}%'))
        count_query = count_query.where(School.school_name.ilike(f'%{search}%'))
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated items
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    schools = result.scalars().all()
    
    # Convert to response format
    items = [{"id": s.id, "school_name": s.school_name} for s in schools]
    
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)
