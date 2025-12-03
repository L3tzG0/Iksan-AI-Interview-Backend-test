from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.major import MajorResponse, MajorCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
MAJOR_COLUMNS = "id, major_name"


@router.get("/", response_model=PaginatedResponse[MajorResponse])
async def read_majors(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
    # Build base query with filters
    query = supabase.table('majors').select(MAJOR_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('major_name', f'%{search}%')
    
    # First get count with limit(0) to avoid 416 error when skip > total
    count_response = await query.limit(0).execute()
    total = count_response.count if count_response.count is not None else 0
    
    # If skip is beyond total, return empty result
    if skip >= total:
        return create_paginated_response(items=[], total=total, skip=skip, limit=limit)
    
    # Re-build query for actual data fetch (query object was modified by limit(0))
    query = supabase.table('majors').select(MAJOR_COLUMNS, count='exact')
    if search:
        query = query.ilike('major_name', f'%{search}%')
    
    response = await query.offset(skip).limit(limit).execute()
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=MajorResponse)
async def create_major(
    major_in: MajorCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
