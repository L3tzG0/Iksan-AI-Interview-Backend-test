from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.teacher import TeacherResponse, TeacherCreate, TeacherUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.teacher_service import TeacherService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TeacherResponse])
def read_teachers(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    school_id: Optional[int] = Query(default=None, description="Filter by school ID"),
    with_user: bool = Query(default=False, description="Include user profile details"),
    with_details: bool = Query(default=False, description="Include user profile and school details")
):
    """
    Get all teachers with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **school_id**: Filter by school ID
    - **with_user**: Include related user profile info
    - **with_details**: Include user profile and school info (overrides with_user)
    """
    service = TeacherService(supabase)
    teachers, total = service.get_all_teachers(
        skip=skip,
        limit=limit,
        school_id=school_id,
        with_user=with_user,
        with_details=with_details
    )
    return create_paginated_response(items=teachers, total=total, skip=skip, limit=limit)


@router.get("/{teacher_id}", response_model=TeacherResponse)
def read_teacher(
    teacher_id: int,
    supabase: Annotated[Client, Depends(get_supabase)],
    with_details: bool = Query(default=False, description="Include user profile and school details")
):
    """
    Get a specific teacher by ID.
    
    - **teacher_id**: The ID of the teacher
    - **with_details**: Include user profile and school info
    """
    service = TeacherService(supabase)
    if with_details:
        return service.get_teacher_with_details(teacher_id)
    return service.get_teacher(teacher_id)


@router.post("/", response_model=TeacherResponse)
def create_teacher(
    teacher_in: TeacherCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Create a new teacher.
    
    - **user_id**: UUID of the user profile
    - **school_id**: Optional school ID to assign the teacher to
    """
    service = TeacherService(supabase)
    return service.create_teacher(teacher_in)


@router.patch("/{teacher_id}", response_model=TeacherResponse)
def update_teacher(
    teacher_id: int,
    teacher_in: TeacherUpdate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Update a teacher's information (e.g., school assignment).
    
    - **teacher_id**: The ID of the teacher to update
    - **school_id**: New school ID to assign the teacher to
    """
    service = TeacherService(supabase)
    return service.update_teacher(teacher_id, teacher_in)
