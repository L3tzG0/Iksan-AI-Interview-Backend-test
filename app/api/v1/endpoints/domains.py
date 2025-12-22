"""API endpoints for managing allowed email domains."""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from app.api.dependencies import require_role, RoleContext
from app.core.database import get_supabase
from app.services.domain_service import DomainService
from app.schemas.domain import (
    AllowedDomainCreate,
    AllowedDomainUpdate,
    AllowedDomainResponse,
    DomainCheckRequest,
    DomainCheckResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=List[AllowedDomainResponse],
    summary="Get all allowed email domains",
    description="Retrieve list of all allowed email domains. Optionally include inactive domains.",
)
async def get_all_domains(
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    _: RoleContext = Depends(require_role(["admin"])),
    include_inactive: bool = False,
):
    """
    Get all allowed email domains.
    
    **Permissions:** Admin only
    
    **Query Parameters:**
    - `include_inactive`: If true, includes inactive domains (default: false)
    
    **Returns:**
    - List of allowed domains
    """
    domain_service = DomainService(supabase)
    return await domain_service.get_all_domains(include_inactive=include_inactive)

# commented out to simplify initial implementation
# @router.get(
#     "/{domain_id}",
#     response_model=AllowedDomainResponse,
#     summary="Get domain by ID",
#     description="Retrieve a specific allowed email domain by its ID.",
# )
# async def get_domain(
#     domain_id: int,
#     supabase: Annotated[AsyncClient, Depends(get_supabase)],
#     _: RoleContext = Depends(require_role(["admin"]))
# ):
#     """
#     Get a specific domain by ID.
    
#     **Permissions:** Admin only
    
#     **Path Parameters:**
#     - `domain_id`: Domain ID
    
#     **Returns:**
#     - Domain details
#     """
#     domain_service = DomainService(supabase)
#     domain = await domain_service.get_domain_by_id(domain_id)
#     if not domain:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Domain with ID {domain_id} not found"
#         )
#     return domain


@router.post(
    "/",
    response_model=AllowedDomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new allowed domain",
    description="Add a new email domain to the allowed list for user registration.",
)
async def create_domain(
    domain_data: AllowedDomainCreate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    role_context: RoleContext = Depends(require_role(["admin"]))
):
    """
    Add a new allowed email domain.
    
    **Permissions:** Admin only
    
    **Request Body:**
    - `domain`: Domain name (e.g., "example.com")
    - `description`: Optional description
    
    **Returns:**
    - Created domain details
    """
    domain_service = DomainService(supabase)
    return await domain_service.create_domain(
        domain_data=domain_data,
        added_by=str(role_context.user.id),
    )

@router.patch(
    "/{domain_id}",
    response_model=AllowedDomainResponse,
    summary="Update domain details",
    description="Update description or active status of an allowed domain.",
)
async def update_domain(
    domain_id: int,
    domain_data: AllowedDomainUpdate,
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
    _: RoleContext = Depends(require_role(["admin"]))
):
    """
    Update an existing domain.
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Request Body:**
    - `description`: Updated description (optional)
    - `is_active`: Active status (optional)
    
    **Returns:**
    - Updated domain details
    """
    domain_service = DomainService(supabase)
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
    supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
    domain_service = DomainService(supabase)
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
#     supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
#     domain_service = DomainService(supabase)
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
#     supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
#     domain_service = DomainService(supabase)
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
#     supabase: Annotated[AsyncClient, Depends(get_supabase)],
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
#     domain_service = DomainService(supabase)
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
