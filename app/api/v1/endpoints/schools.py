from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.school import SchoolResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.utils.pagination import paginate_query

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
    def build_query():
        base_query = supabase.table('schools').select(SCHOOL_COLUMNS, count='exact')
        if search:
            base_query = base_query.ilike('school_name', f'%{search}%')
        return base_query

    items, total = await paginate_query(build_query, skip, limit)
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)
