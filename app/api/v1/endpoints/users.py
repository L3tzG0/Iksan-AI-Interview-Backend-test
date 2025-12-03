from typing import List, Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.services.user_service import UserProfileService
from uuid import UUID

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserProfileResponse])
def read_user_profiles(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    role_id: Optional[int] = Query(default=None, description="Filter by role ID"),
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
    profiles, total = service.get_all_profiles(
        skip=skip,
        limit=limit,
        role_id=role_id,
        search=search,
        with_role=with_role
    )
    return create_paginated_response(items=profiles, total=total, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserProfileResponse)
def read_user_profile_by_id(
    user_id: UUID,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Get a specific user profile by UUID.
    """
    service = UserProfileService(supabase)
    profile = service.get_profile(user_id)
    return profile

@router.put("/{user_id}", response_model=UserProfileResponse)
def update_user_profile(
    user_id: UUID,
    profile_in: UserProfileUpdate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Update a user profile.
    """
    service = UserProfileService(supabase)
    profile = service.update_profile(user_id, profile_in)
    return profile
