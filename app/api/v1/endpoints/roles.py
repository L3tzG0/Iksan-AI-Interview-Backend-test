from typing import List, Annotated
from fastapi import APIRouter, Depends, Query
from supabase import Client
from app.core.database import get_supabase
from app.schemas.role import RoleResponse, RoleCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
ROLE_COLUMNS = "id, role_name"


@router.get("/", response_model=PaginatedResponse[RoleResponse])
def read_roles(
    supabase: Annotated[Client, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return")
):
    """
    Get all roles with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    """
    query = supabase.table('roles').select(ROLE_COLUMNS, count='exact')
    query = query.range(skip, skip + limit - 1)
    response = query.execute()
    
    total = response.count if response.count is not None else len(response.data)
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    supabase: Annotated[Client, Depends(get_supabase)]
):
    """Create a new role"""
    response = supabase.table('roles').insert(role_in.model_dump()).execute()
    return response.data[0] if response.data else None
