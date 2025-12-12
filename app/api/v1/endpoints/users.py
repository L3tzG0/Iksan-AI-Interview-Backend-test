from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.user import UserProfileResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.user_service import UserProfileService
from app.schemas.types import RoleType

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserProfileResponse])
async def read_user_profiles(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    role_id: Optional[RoleType] = Query(default=None, description="Filter by role ID"),
    search: Optional[str] = Query(default=None, description="Search by name or email"),
    with_role: bool = Query(default=False, description="Include role information")
):
    """
    Retrieve user profiles with pagination and optional filtering.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    - **role_id**: Filter by role ID
    - **search**: Search by name or email (partial match)
    - **with_role**: Include role information
    """
    service = UserProfileService(supabase)
    profiles, total = await service.get_all_profiles(
        skip=skip,
        limit=limit,
        role_id=role_id,
        search=search,
        with_role=with_role
    )
    return create_paginated_response(items=profiles, total=total, skip=skip, limit=limit)