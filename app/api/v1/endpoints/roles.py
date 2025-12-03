from typing import List, Annotated
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.role import RoleResponse, RoleCreate
from app.schemas.pagination import PaginatedResponse, create_paginated_response

router = APIRouter()

# Explicit columns to select (avoiding SELECT *)
ROLE_COLUMNS = "id, role_name"


@router.get("/", response_model=PaginatedResponse[RoleResponse])
async def read_roles(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return")
):
    """
    Get all roles with pagination.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Max records to return (default: 20, max: 100)
    """
    # First get count with limit(0) to avoid 416 error when skip > total
    count_query = supabase.table('roles').select(ROLE_COLUMNS, count='exact').limit(0)
    count_response = await count_query.execute()
    total = count_response.count if count_response.count is not None else 0
    
    # If skip is beyond total, return empty result
    if skip >= total:
        return create_paginated_response(items=[], total=total, skip=skip, limit=limit)
    
    # Fetch actual data
    query = supabase.table('roles').select(ROLE_COLUMNS, count='exact')
    response = await query.offset(skip).limit(limit).execute()
    return create_paginated_response(items=response.data, total=total, skip=skip, limit=limit)

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_in: RoleCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)]
):
    """Create a new role"""
    response = await supabase.table('roles').insert(role_in.model_dump()).execute()
    return response.data[0] if response.data else None
