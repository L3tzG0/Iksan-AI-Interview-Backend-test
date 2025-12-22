"""
API endpoints for managing allowed email domains.

These endpoints allow administrators to:
- View all allowed domains
- Add new domains
- Update domain details
- Activate/deactivate domains
- Delete domains
- Check if a domain is allowed
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import AsyncClient

from app.api.dependencies import get_supabase_client, get_current_user
from app.services.domain_service import DomainService
from app.schemas.domain import (
    AllowedDomainCreate,
    AllowedDomainUpdate,
    AllowedDomainResponse,
    DomainCheckRequest,
    DomainCheckResponse,
)
from app.schemas.user import UserResponse

router = APIRouter()


def get_domain_service(
    supabase: AsyncClient = Depends(get_supabase_client),
) -> DomainService:
    """Dependency to get domain service"""
    return DomainService(supabase)


async def require_admin_user(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    """Dependency to ensure user is an admin"""
    if current_user.role_id != 1:  # Assuming role_id 1 is admin
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage email domains"
        )
    return current_user


@router.get(
    "/domains",
    response_model=List[AllowedDomainResponse],
    summary="Get all allowed email domains",
    description="Retrieve list of all allowed email domains. Optionally include inactive domains.",
)
async def get_all_domains(
    include_inactive: bool = False,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Get all allowed email domains.
    
    **Permissions:** Admin only
    
    **Query Parameters:**
    - `include_inactive`: If true, includes inactive domains (default: false)
    
    **Returns:**
    - List of allowed domains
    """
    return await domain_service.get_all_domains(include_inactive=include_inactive)


@router.get(
    "/domains/{domain_id}",
    response_model=AllowedDomainResponse,
    summary="Get domain by ID",
    description="Retrieve a specific allowed email domain by its ID.",
)
async def get_domain(
    domain_id: int,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Get a specific domain by ID.
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Returns:**
    - Domain details
    """
    domain = await domain_service.get_domain_by_id(domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Domain with ID {domain_id} not found"
        )
    return domain


@router.post(
    "/domains",
    response_model=AllowedDomainResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new allowed domain",
    description="Add a new email domain to the allowed list for user registration.",
)
async def create_domain(
    domain_data: AllowedDomainCreate,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Add a new allowed email domain.
    
    **Permissions:** Admin only
    
    **Request Body:**
    - `domain`: Domain name (e.g., "example.com")
    - `description`: Optional description
    
    **Returns:**
    - Created domain details
    
    **Example:**
    ```json
    {
        "domain": "university.edu",
        "description": "University email domain"
    }
    ```
    """
    return await domain_service.create_domain(
        domain_data=domain_data,
        added_by=str(current_user.id),
    )


@router.patch(
    "/domains/{domain_id}",
    response_model=AllowedDomainResponse,
    summary="Update domain details",
    description="Update description or active status of an allowed domain.",
)
async def update_domain(
    domain_id: int,
    domain_data: AllowedDomainUpdate,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
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
    
    **Example:**
    ```json
    {
        "description": "Updated description",
        "is_active": false
    }
    ```
    """
    return await domain_service.update_domain(
        domain_id=domain_id,
        domain_data=domain_data,
    )


@router.delete(
    "/domains/{domain_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a domain",
    description="Permanently delete an allowed email domain.",
)
async def delete_domain(
    domain_id: int,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Delete a domain (hard delete).
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Warning:** This permanently removes the domain from the allowed list.
    Users with emails from this domain will no longer be able to register.
    """
    await domain_service.delete_domain(domain_id)
    return None


@router.post(
    "/domains/{domain_id}/activate",
    response_model=AllowedDomainResponse,
    summary="Activate a domain",
    description="Activate a previously deactivated domain.",
)
async def activate_domain(
    domain_id: int,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Activate a domain.
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Returns:**
    - Updated domain details
    """
    return await domain_service.toggle_domain_status(
        domain_id=domain_id,
        is_active=True,
    )


@router.post(
    "/domains/{domain_id}/deactivate",
    response_model=AllowedDomainResponse,
    summary="Deactivate a domain",
    description="Deactivate a domain to temporarily block registrations from it.",
)
async def deactivate_domain(
    domain_id: int,
    domain_service: DomainService = Depends(get_domain_service),
    current_user: UserResponse = Depends(require_admin_user),
):
    """
    Deactivate a domain (soft delete).
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - `domain_id`: Domain ID
    
    **Returns:**
    - Updated domain details
    
    **Note:** This prevents new registrations from this domain but doesn't
    affect existing users.
    """
    return await domain_service.toggle_domain_status(
        domain_id=domain_id,
        is_active=False,
    )


@router.post(
    "/domains/check",
    response_model=DomainCheckResponse,
    summary="Check if email domain is allowed",
    description="Check if an email address has an allowed domain. Useful for client-side validation.",
)
async def check_domain(
    check_request: DomainCheckRequest,
    domain_service: DomainService = Depends(get_domain_service),
):
    """
    Check if an email domain is allowed for registration.
    
    **Permissions:** Public (no authentication required)
    
    **Request Body:**
    - `email`: Email address to check
    
    **Returns:**
    - Whether the domain is allowed
    - Domain name
    - Descriptive message
    
    **Example:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    **Response:**
    ```json
    {
        "email": "user@example.com",
        "domain": "example.com",
        "is_allowed": true,
        "message": "This email domain is allowed for registration"
    }
    ```
    """
    email = check_request.email
    domain = email.split("@")[-1].lower()
    is_allowed = await domain_service.is_domain_allowed(email)
    
    return DomainCheckResponse(
        email=email,
        domain=domain,
        is_allowed=is_allowed,
        message=(
            "This email domain is allowed for registration"
            if is_allowed
            else "This email domain is not allowed for registration"
        ),
    )
