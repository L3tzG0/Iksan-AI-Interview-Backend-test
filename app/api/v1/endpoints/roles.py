from typing import List, Annotated
from fastapi import APIRouter, Depends
from supabase import Client
from app.core.database import get_supabase
from app.schemas.role import RoleResponse, RoleCreate

router = APIRouter()

@router.get("/", response_model=List[RoleResponse])
def read_roles(
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Get all roles"""
    response = supabase.table('roles').select('*').execute()
    return response.data

@router.post("/", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Create a new role"""
    response = supabase.table('roles').insert(role_in.model_dump()).execute()
    return response.data[0] if response.data else None
