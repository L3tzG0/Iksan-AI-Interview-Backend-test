from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.school import SchoolResponse, SchoolCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
SCHOOL_COLUMNS = "id, school_name"


@router.get("/", response_model=PaginatedResponse[SchoolResponse])
async def read_schools(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
    # Build base query with filters
    query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('school_name', f'%{search}%')
    
    # First get count with limit(0) to avoid 416 error when skip > total
    count_response = await query.limit(0).execute()
    total = count_response.count if count_response.count is not None else 0
    
    # If skip is beyond total, return empty result
    if skip >= total:
        return create_paginated_response(items=[], total=total, skip=skip, limit=limit)
    
    # Re-build query for actual data fetch
    query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
    if search:
        query = query.ilike('school_name', f'%{search}%')
    
    response = await query.offset(skip).limit(limit).execute()
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=SchoolResponse)
async def create_school(
    school_in: SchoolCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
