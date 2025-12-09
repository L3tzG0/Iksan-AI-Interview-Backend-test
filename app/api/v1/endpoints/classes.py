from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.class_schema import ClassResponse, ClassCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.class_service import ClassService
from app.schemas.types import GradeLevel

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
    service = ClassService(supabase)
    classes, total = await service.get_all_classes(
        skip=skip,
        limit=limit,
        grade_level=grade_level
    )
    return create_paginated_response(items=classes, total=total, skip=skip, limit=limit)

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_in: ClassCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
