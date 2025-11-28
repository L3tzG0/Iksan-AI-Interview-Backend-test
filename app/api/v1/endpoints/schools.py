from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.school import SchoolResponse, SchoolCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
SCHOOL_COLUMNS = "id, school_name"


@router.get("/", response_model=PaginatedResponse[SchoolResponse])
def read_schools(
    supabase: Annotated[Client, Depends(get_supabase)],
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
    query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('school_name', f'%{search}%')
    
    query = query.range(skip, skip + limit - 1)
    response = query.execute()
    
    total = response.count if response.count is not None else len(response.data)
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=SchoolResponse)
def create_school(
    school_in: SchoolCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
