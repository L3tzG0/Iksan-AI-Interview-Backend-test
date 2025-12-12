from typing import Annotated
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.core.database import get_supabase
from app.schemas.role import RoleResponse
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.utils.pagination import paginate_query

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
    def build_query():
        return supabase.table('roles').select(ROLE_COLUMNS, count='exact')

    items, total = await paginate_query(build_query, skip, limit)
    return create_paginated_response(items=items, total=total, skip=skip, limit=limit)