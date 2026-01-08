"""
API endpoints for managing allowed email domains.

Updated to use SQLAlchemy AsyncSession instead of Supabase.
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_role, RoleContext
from app.core.database import get_db
from app.services.domain_service import DomainService
from app.schemas.domain import (
    AllowedDomainCreate,
    AllowedDomainUpdate,
    AllowedDomainResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[AllowedDomainResponse],
    summary="Get all allowed email domains",
    description="Retrieve list of all allowed email domains. Optionally include inactive domains.",
)
async def get_all_domains(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: RoleContext = Depends(require_role(["admin"])),
    # include_inactive: bool = Query(
    #     default=False,
    #     description="Include inactive domains"
    # ),
    search: Optional[str] = Query(
        default=None,
        description="Search by domain or organization name"
    ),
):
    """
    Get all allowed email domains.
    
    **Permissions:** Admin only
    
    **Query Parameters:**
    - `include_inactive`: If true, includes inactive domains (default: false)
    - `search`: Optional search term to match domain or organization name (partial match)
    
    **Returns:**
    - List of allowed domains
    """
    domain_service = DomainService(db)
    return await domain_service.get_all_domains(
        # include_inactive=include_inactive,
        search=search,
    )


@router.post(
    "/",
    response_model=AllowedDomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new allowed domain",
    description="Add a new email domain to the allowed list for user registration.",
)
async def create_domain(
    domain_data: AllowedDomainCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    role_context: RoleContext = Depends(require_role(["admin"]))
):
    """
    Add a new allowed email domain.
    
    **Permissions:** Admin only
    
    **Request Body:**
    - `domain`: Domain name (e.g., "example.com")
    - `organization_name`: Optional organization name
    
    **Returns:**
    - Created domain details
    """
    domain_service = DomainService(db)
    return await domain_service.create_domain(
        domain_data=domain_data,
        added_by=str(role_context.user.id),
    )


@router.patch(
    "/{domain_id}",
    response_model=AllowedDomainResponse,
    summary="Update domain details (including domain name)",
    description="Update domain name, organization name or active status of an allowed domain.",
)
async def update_domain(
    domain_id: int,
    domain_data: AllowedDomainUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: RoleContext = Depends(require_role(["admin"]))
):
    """
    Update an existing domain (supports renaming the domain itself).
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Request Body:**
    - `domain`: New domain name (optional)
    - `organization_name`: Updated organization name (optional)
    - `is_active`: Active status (optional)
    
    **Returns:**
    - Updated domain details
    """
    domain_service = DomainService(db)
    return await domain_service.update_domain(
        domain_id=domain_id,
        domain_data=domain_data,
    )


@router.delete(
    "/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a domain",
    description="Permanently delete an allowed email domain.",
)
async def delete_domain(
    domain_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: RoleContext = Depends(require_role(["admin"]))
):
    """
    Delete a domain (hard delete).
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Warning:** This permanently removes the domain from the allowed list.
    Users with emails from this domain will no longer be able to register.
    """
    domain_service = DomainService(db)
    await domain_service.delete_domain(domain_id)
    return None


# commented out to simplify initial implementation
# @router.post(
#     "/{domain_id}/activate",
#     response_model=AllowedDomainResponse,
#     summary="Activate a domain",
#     description="Activate a previously deactivated domain.",
# )
# async def activate_domain(
#     domain_id: int,
#     db: Annotated[AsyncSession, Depends(get_db)],
#     _: RoleContext = Depends(require_role(["admin"]))
# ):
#     """
#     Activate a domain.
    
#     **Permissions:** Admin only
    
#     **Path Parameters:**
#     - `domain_id`: Domain ID
    
#     **Returns:**
#     - Updated domain details
#     """
#     domain_service = DomainService(db)
#     return await domain_service.toggle_domain_status(
#         domain_id=domain_id,
#         is_active=True,
#     )


# commented out to simplify initial implementation
# @router.post(
#     "/{domain_id}/deactivate",
#     response_model=AllowedDomainResponse,
#     summary="Deactivate a domain",
#     description="Deactivate a domain to temporarily block registrations from it.",
# )
# async def deactivate_domain(
#     domain_id: int,
#     db: Annotated[AsyncSession, Depends(get_db)],
#     _: RoleContext = Depends(require_role(["admin"]))
# ):
#     """
#     Deactivate a domain (soft delete).
    
#     **Permissions:** Admin only
    
#     **Path Parameters:**
#     - `domain_id`: Domain ID
    
#     **Returns:**
#     - Updated domain details
    
#     **Note:** This prevents new registrations from this domain but doesn't
#     affect existing users.
#     """
#     domain_service = DomainService(db)
#     return await domain_service.toggle_domain_status(
#         domain_id=domain_id,
#         is_active=False,
#     )


# commented out to simplify initial implementation
# @router.post(
#     "/check",
#     response_model=DomainCheckResponse,
#     summary="Check if email domain is allowed",
#     description="Check if an email address has an allowed domain. Useful for client-side validation.",
# )
# async def check_domain(
#     check_request: DomainCheckRequest,
#     db: Annotated[AsyncSession, Depends(get_db)],
# ):
#     """
#     Check if an email domain is allowed for registration.
    
#     **Permissions:** Public (no authentication required)
    
#     **Request Body:**
#     - `email`: Email address to check
    
#     **Returns:**
#     - Whether the domain is allowed
#     - Domain name
#     - Descriptive message
#     """
#     email = check_request.email
#     domain = email.split("@")[-1].lower()
#     domain_service = DomainService(db)
#     is_allowed = await domain_service.is_domain_allowed(domain)

#     return DomainCheckResponse(
#         email=email,
#         domain=domain,
#         is_allowed=is_allowed,
#         message=(
#             "This email domain is allowed for registration"
#             if is_allowed
#             else "This email domain is not allowed for registration"
#         ),
#     )
