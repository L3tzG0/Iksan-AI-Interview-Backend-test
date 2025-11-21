from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve users.
    """
    response = supabase.table('users').select('*').range(skip, skip + limit - 1).execute()
    return response.data

@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Get a specific user by id.
    """
    response = supabase.table('users').select('*').eq('id', user_id).execute()
    if not response.data:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return response.data[0]

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """
    Update a user.
    """
    pass
