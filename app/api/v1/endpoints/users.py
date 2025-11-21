from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.user import UserProfileResponse, UserProfileUpdate
from app.services.user_service import UserProfileService
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[UserProfileResponse])
async def read_user_profiles(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve user profiles.
    """
    service = UserProfileService(supabase)
    profiles = await service.get_all_profiles(skip, limit)
    return profiles

@router.get("/{user_id}", response_model=UserProfileResponse)
async def read_user_profile_by_id(
    user_id: UUID,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Get a specific user profile by UUID.
    """
    service = UserProfileService(supabase)
    profile = await service.get_profile(user_id)
    return profile

@router.put("/{user_id}", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: UUID,
    profile_in: UserProfileUpdate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Update a user profile.
    """
    service = UserProfileService(supabase)
    profile = await service.update_profile(user_id, profile_in)
    return profile
