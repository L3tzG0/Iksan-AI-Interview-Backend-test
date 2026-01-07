from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.class_schema import ClassResponse, ClassCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.types import GradeLevel
from app.utils.pagination import paginate_query

router = APIRouter()

@router.get("/", response_model=PaginatedResponse[ClassResponse])
async def read_classes(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    grade_level: Optional[GradeLevel] = Query(default=None, description="Filter by grade level (1, 2, or 3)")
):
    """
    Get all classes with pagination and optional filtering.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **grade_level**: Filter by grade level (1, 2, or 3)
    """
    def build_query():
        base_query = supabase.table('classes').select("id, class_name, grade_level", count='exact')
        if grade_level is not None:
            base_query = base_query.eq('grade_level', grade_level)
        return base_query

    items, total = await paginate_query(build_query, skip, limit)
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_in: ClassCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
