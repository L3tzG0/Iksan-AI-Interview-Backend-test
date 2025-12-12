from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.major import MajorResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.utils.pagination import paginate_query

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
    def build_query():
        base_query = supabase.table('majors').select(MAJOR_COLUMNS, count='exact')
        if search:
            base_query = base_query.ilike('major_name', f'%{search}%')
        return base_query

    items, total = await paginate_query(build_query, skip, limit)
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)
