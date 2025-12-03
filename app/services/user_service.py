from typing import Optional, Tuple, List, Any
from supabase import AsyncClient
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

USER_FULL_CONTEXT_QUERY = """
    id, email, full_name, role_id, created_at, updated_at,
    roles(id, role_name),
    students!user_id(
        id, user_id, school_id, major_id, current_class_id, created_at, updated_at,
        schools(id, school_name),
        majors(id, major_name),
        classes(id, class_name, grade_level)
    ),
    teachers!user_id(
        id, user_id, created_at, updated_at,
        schools(id, school_name)
    )
"""


class UserProfileService:
    """
    Service for managing user profiles in public.user_profiles table.
    Note: User profiles are auto-created via database trigger when users register.
    This service is mainly for querying and updating existing profiles.
    
    All methods are async because the Supabase AsyncClient
    uses async HTTP calls. This ensures proper connection handling
    under concurrent load.
    """
    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def get_profile(self, user_id: UUID):
        """Get user profile by UUID from user_profiles table with explicit columns"""
        try:
            response = await self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_profile_with_role(self, user_id: UUID):
        """Get user profile with role information using relational select"""
        try:
            response = await self.supabase.table('user_profiles').select(
                USER_PROFILE_COLUMNS_WITH_ROLE
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_full_user_context(self, user_id: UUID):
        """
        Get complete user context including profile, role, and student/teacher details
        in optimized queries to avoid N+1 patterns.
        
        Returns a dict with profile, role, and optional student/teacher details.
        """
        try:
            response = await self.supabase.table('user_profiles').select(
                USER_FULL_CONTEXT_QUERY
            ).eq('id', str(user_id)).execute()

            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

            payload = response.data[0]
            profile = {
                key: value
                for key, value in payload.items()
                if key not in ("students", "teachers")
            }

            student_details = self._first_relationship_record(payload.get("students"))
            teacher_details = self._first_relationship_record(payload.get("teachers"))

            return {
                "profile": profile,
                "student_details": student_details,
                "teacher_details": teacher_details
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_student_details(self, user_id: UUID):
        """Get student details by user_id with related information in single query"""
        try:
            response = await self.supabase.table('students').select(
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

    async def get_teacher_details(self, user_id: UUID):
        """Get teacher details by user_id with explicit columns"""
        try:
            response = await self.supabase.table('teachers').select(
                "id, user_id, created_at, updated_at"
            ).eq('user_id', str(user_id)).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_profile_by_email(self, email: str):
        """Get user profile by email from user_profiles table with explicit columns"""
        try:
            response = await self.supabase.table('user_profiles').select(USER_PROFILE_COLUMNS).eq('email', email).execute()
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_profile(self, user_id: UUID, profile: UserProfileUpdate):
        """Update user profile information"""
        try:
            response = await self.supabase.table('user_profiles').update(
                profile.model_dump(exclude_unset=True)
            ).eq('id', str(user_id)).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @staticmethod
    def _first_relationship_record(relationship: Any) -> Optional[dict]:
        """Return the first related record regardless of Supabase response shape."""
        if not relationship:
            return None
        if isinstance(relationship, list):
            return relationship[0] if relationship else None
        return relationship
    
    async def get_all_profiles(
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
            
            # Build query with filters - count='exact' returns total count with data
            query = self.supabase.table('user_profiles').select(columns, count='exact')
            if role_id is not None:
                query = query.eq('role_id', role_id)
            if search:
                query = query.or_(f"full_name.ilike.%{search}%,email.ilike.%{search}%")
            
            # Single query with pagination - PostgreSQL returns total count with data
            response = await query.offset(skip).limit(limit).execute()
            total = response.count if response.count is not None else 0
            
            return response.data, total
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
