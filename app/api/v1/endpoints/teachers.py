from typing import List, Annotated
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.teacher import TeacherResponse, TeacherCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.teacher_service import TeacherService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TeacherResponse])
def read_teachers(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    with_user: bool = Query(default=False, description="Include user profile details")
):
    """
    Get all teachers with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **with_user**: Include related user profile info
    """
    service = TeacherService(supabase)
    teachers, total = service.get_all_teachers(
        skip=skip,
        limit=limit,
        with_user=with_user
    )
    return create_paginated_response(items=teachers, total=total, skip=skip, limit=limit)

@router.post("/", response_model=TeacherResponse)
def create_teacher(
    teacher_in: TeacherCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    pass
