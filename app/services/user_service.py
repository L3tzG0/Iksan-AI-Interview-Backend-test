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

    async def get_profile_with_role(self, user_id: UUID):
        """Get user profile with role information"""
        try:
            response = self.supabase.table('user_profiles').select(
                '*, roles(id, role_name)'
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_student_details(self, user_id: UUID):
        """Get student details by user_id with related information"""
        try:
            response = self.supabase.table('students').select(
                '*, schools(id, school_name), majors(id, major_name), classes(id, class_name, grade_level)'
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_teacher_details(self, user_id: UUID):
        """Get teacher details by user_id"""
        try:
            response = self.supabase.table('teachers').select('*').eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
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
