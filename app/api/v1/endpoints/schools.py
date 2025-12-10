from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from postgrest.exceptions import APIError
from app.core.database import get_supabase
from app.schemas.school import SchoolResponse
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
    # Build query with filters - count='exact' returns total count with data
    query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('school_name', f'%{search}%')
    
    # Single query with pagination - PostgreSQL returns total count with data
    # Handle 416 error when offset exceeds total records
    try:
        response = await query.offset(skip).limit(limit).execute()
        total = response.count if response.count is not None else 0
        return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)
    except APIError as e:
        if e.code == '416' or e.code == 416:  # Range not satisfiable - offset beyond total
            count_query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
            if search:
                count_query = count_query.ilike('school_name', f'%{search}%')
            count_response = await count_query.limit(0).execute()
            total = count_response.count if count_response.count is not None else 0
            return create_paginated_response(items=[], total=total, skip=skip, limit=limit)
        raise
