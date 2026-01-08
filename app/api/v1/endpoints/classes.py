"""
Classes API endpoints.

Uses SQLAlchemy AsyncSession for database operations.
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.class_schema import ClassResponse, ClassCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.types import GradeLevel
from app.services.class_service import ClassService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ClassResponse])
async def read_classes(
    db: Annotated[AsyncSession, Depends(get_db)],
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
    service = ClassService(db)
    items, total = await service.get_all_classes(
        skip=skip,
        limit=limit,
        grade_level=grade_level.value if grade_level else None
    )
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)


@router.post("/", response_model=ClassResponse)
async def create_class(
    class_in: ClassCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Create a new class."""
    service = ClassService(db)
    return await service.create_class(class_in)
