from supabase import Client
from fastapi import HTTPException, status
from app.schemas.user import UserProfileCreate, UserProfileUpdate
from uuid import UUID

class UserProfileService:
    """
    Service for managing user profiles in public.user_profiles table.
    Note: User profiles are auto-created via database trigger when users register.
    This service is mainly for querying and updating existing profiles.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_profile(self, user_id: UUID):
        """Get user profile by UUID from user_profiles table"""
        try:
            response = self.supabase.table('user_profiles').select('*').eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_profile_by_email(self, email: str):
        """Get user profile by email from user_profiles table"""
        try:
            response = self.supabase.table('user_profiles').select('*').eq('email', email).execute()
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_profile(self, user_id: UUID, profile: UserProfileUpdate):
        """Update user profile information"""
        try:
            response = self.supabase.table('user_profiles').update(
                profile.model_dump(exclude_unset=True)
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    async def get_all_profiles(self, skip: int = 0, limit: int = 100):
        """Get all user profiles with pagination"""
        try:
            response = self.supabase.table('user_profiles').select('*').range(skip, skip + limit - 1).execute()
            return response.data
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
