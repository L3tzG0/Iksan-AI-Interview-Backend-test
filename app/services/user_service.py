from supabase import Client
from fastapi import HTTPException, status
from app.schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def get_user(self, user_id: str):
        """Get user by ID from users table"""
        try:
            response = self.supabase.table('users').select('*').eq('id', user_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def get_user_by_email(self, email: str):
        """Get user by email from users table"""
        try:
            response = self.supabase.table('users').select('*').eq('email', email).execute()
            if not response.data:
                return None
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def create_user(self, user: UserCreate):
        """Create a new user in users table"""
        try:
            response = self.supabase.table('users').insert(user.model_dump()).execute()
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def update_user(self, user_id: str, user: UserUpdate):
        """Update user information"""
        try:
            response = self.supabase.table('users').update(user.model_dump(exclude_unset=True)).eq('id', user_id).execute()
            if not response.data:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return response.data[0]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
