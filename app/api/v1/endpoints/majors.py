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
    # Build query with filters - count='exact' returns total count with data
    query = supabase.table('majors').select(MAJOR_COLUMNS, count='exact')
    
    if search:
        query = query.ilike('major_name', f'%{search}%')
    
    # Single query with pagination - PostgreSQL returns total count with data
    response = await query.offset(skip).limit(limit).execute()
    total = response.count if response.count is not None else 0
    
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=MajorResponse)
async def create_major(
    major_in: MajorCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
