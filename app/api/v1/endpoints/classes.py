from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.class_schema import ClassResponse, ClassCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.class_service import ClassService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ClassResponse])
async def read_classes(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    class_year: Optional[int] = Query(default=None, description="Filter by class year"),
    homeroom_teacher_id: Optional[int] = Query(default=None, description="Filter by homeroom teacher"),
    with_teacher: bool = Query(default=False, description="Include homeroom teacher details")
):
    """
    Get all classes with pagination and optional filtering.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **class_year**: Filter by class year
    - **homeroom_teacher_id**: Filter by teacher ID
    - **with_teacher**: Include homeroom teacher details
    """
    service = ClassService(supabase)
    classes, total = await service.get_all_classes(
        skip=skip,
        limit=limit,
        class_year=class_year,
        homeroom_teacher_id=homeroom_teacher_id,
        with_teacher=with_teacher
    )
    return create_paginated_response(items=classes, total=total, skip=skip, limit=limit)

@router.post("/", response_model=ClassResponse)
async def create_class(
    class_in: ClassCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    pass
