from typing import Optional, Tuple, List
from supabase import Client
from fastapi import HTTPException, status
from app.schemas.user import UserProfileCreate, UserProfileUpdate
from uuid import UUID

# Explicit columns to select for user profiles (avoiding SELECT *)
USER_PROFILE_COLUMNS = "id, email, full_name, role_id, created_at, updated_at"
USER_PROFILE_COLUMNS_WITH_ROLE = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name)
"""

# For fetching complete user with all details in a single query
USER_FULL_DETAILS_QUERY = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name)
"""


class UserProfileService:
    """
    Service for managing user profiles in public.user_profiles table.
    Note: User profiles are auto-created via database trigger when users register.
    This service is mainly for querying and updating existing profiles.
    
    All methods are synchronous (def) because the Supabase Python client
    uses synchronous HTTP calls internally. FastAPI will automatically
    run these in a thread pool when called from async endpoints.
    """
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def get_profile(self, user_id: UUID):
        """Get user profile by UUID from user_profiles table with explicit columns"""
        try:
            response = self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_profile_with_role(self, user_id: UUID):
        """Get user profile with role information using relational select"""
        try:
            response = self.supabase.table('user_profiles').select(
                USER_PROFILE_COLUMNS_WITH_ROLE
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_full_user_context(self, user_id: UUID):
        """
        Get complete user context including profile, role, and student/teacher details
        in optimized queries to avoid N+1 patterns.
        
        Returns a dict with profile, role, and optional student/teacher details.
        """
        try:
            # Get profile with role in single query
            profile_response = self.supabase.table('user_profiles').select(
                USER_PROFILE_COLUMNS_WITH_ROLE
            ).eq('id', str(user_id)).execute()
            
            if not profile_response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            
            profile = profile_response.data[0]
            result = {
                "profile": profile,
                "student_details": None,
                "teacher_details": None
            }
            
            # Based on role_id, fetch student or teacher details
            # Only make the necessary query based on role
            role_id = profile.get("role_id")
            
            # Try to get student details (with relations in single query)
            student_response = self.supabase.table('students').select(
                """id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
                   schools(id, school_name),
                   majors(id, major_name),
                   classes(id, class_name, grade_level)"""
            ).eq('user_id', str(user_id)).execute()
            
            if student_response.data:
                result["student_details"] = student_response.data[0]
            else:
                # Try teacher if not a student
                teacher_response = self.supabase.table('teachers').select(
                    "id, user_id, created_at, updated_at"
                ).eq('user_id', str(user_id)).execute()
                
                if teacher_response.data:
                    result["teacher_details"] = teacher_response.data[0]
            
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_student_details(self, user_id: UUID):
        """Get student details by user_id with related information in single query"""
        try:
            response = self.supabase.table('students').select(
                """id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
                   schools(id, school_name),
                   majors(id, major_name),
                   classes(id, class_name, grade_level)"""
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_teacher_details(self, user_id: UUID):
        """Get teacher details by user_id with explicit columns"""
        try:
            response = self.supabase.table('teachers').select(
                "id, user_id, created_at, updated_at"
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def get_profile_by_email(self, email: str):
        """Get user profile by email from user_profiles table with explicit columns"""
        try:
            response = self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('email', email).execute()
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def update_profile(self, user_id: UUID, profile: UserProfileUpdate):
        """Update user profile information"""
        try:
            response = self.supabase.table('user_profiles').update(
                profile.model_dump(exclude_unset=True)
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    def get_all_profiles(
        self,
        skip: int = 0,
        limit: int = 20,
        role_id: Optional[int] = None,
        search: Optional[str] = None,
        with_role: bool = False
    ) -> Tuple[List[dict], int]:
        """
        Get all user profiles with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            role_id: Filter by role ID
            search: Search by name or email (partial match)
            with_role: Include role information
        
        Returns:
            Tuple of (list of profiles, total count)
        """
        try:
            columns = USER_PROFILE_COLUMNS_WITH_ROLE if with_role else USER_PROFILE_COLUMNS
            
            query = self.supabase.table('user_profiles').select(columns, count='exact')
            
            if role_id is not None:
                query = query.eq('role_id', role_id)
            if search:
                # Search in both full_name and email
                query = query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            
            query = query.range(skip, skip + limit - 1)
            
            response = query.execute()
            total = response.count if response.count is not None else len(response.data)
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
