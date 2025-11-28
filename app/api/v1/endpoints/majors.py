from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.major import MajorResponse, MajorCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
MAJOR_COLUMNS = "id, major_name"


@router.get("/", response_model=PaginatedResponse[MajorResponse])
def read_majors(
    supabase: Annotated[Client, Depends(get_supabase)],
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
    query = supabase.table('majors').select(MAJOR_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('major_name', f'%{search}%')
    
    query = query.range(skip, skip + limit - 1)
    response = query.execute()
    
    total = response.count if response.count is not None else len(response.data)
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=MajorResponse)
def create_major(
    major_in: MajorCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
