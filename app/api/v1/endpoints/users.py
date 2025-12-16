from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from supabase import AsyncClient
from app.api.dependencies import require_role, RoleContext
from app.core.database import get_supabase
from app.schemas.pagination import PaginatedResponse, create_paginated_response
from app.schemas.types import RoleName
from app.schemas.user import UserListItemResponse
from app.services.user_service import UserProfileService

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[UserListItemResponse])
async def read_user_profiles(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum records to return"),
    role: Optional[RoleName] = Query(default=None, description="Filter by role name"),
    search: Optional[str] = Query(default=None, description="Search by name or email"),
    role_context: RoleContext = Depends(require_role(["admin", "teacher"]))
):
    """Retrieve users with pagination and role-aware filtering.

    Requires admin or teacher role to access this endpoint.

    Access Control:

    - Admins: Can see all users with all roles
    - Teachers: Scoped to students in their own school

    Query Parameters support filtering by role and searching by name or email.
    
    Student records include associated student ID and passwords.

    Returns:
        PaginatedResponse[UserListItemResponse]: Paginated list of user profiles with total count.
    """
    service = UserProfileService(supabase)
    profiles, total = await service.list_users(
        skip=skip,
        limit=limit,
        role=role.value if role else None,
        search=search,
        viewer_role=role_context.role_name,
        viewer_user_id=role_context.user.id,
    )
    return create_paginated_response(items=profiles, total=total, skip=skip, limit=limit)