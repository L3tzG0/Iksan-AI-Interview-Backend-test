"""
Email Domain Management Service

Handles CRUD operations for allowed email domains.
Refactored from Supabase AsyncClient to SQLAlchemy AsyncSession.
"""

import logging
from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.schemas.domain import (
    AllowedDomainCreate,
    AllowedDomainUpdate,
    AllowedDomainResponse,
)
from app.models.allowed_email_domain import AllowedEmailDomain
from app.repositories.domain_repository import DomainRepository

logger = logging.getLogger(__name__)


class DomainService:
    """Service for managing allowed email domains."""

    def __init__(self, db: AsyncSession):
        """
        Initialize service with SQLAlchemy session.
        
        Args:
            db: SQLAlchemy AsyncSession for database operations
        """
        self.db = db
        self.repo = DomainRepository(db)

    async def get_all_domains(
        self,
        include_inactive: bool = False,
        search: Optional[str] = None,
    ) -> List[AllowedDomainResponse]:
        """
        Get all allowed email domains.
        
        Args:
            include_inactive: If True, includes inactive domains
            search: Optional search term to filter by domain or organization name
        
        Returns:
            List of allowed domains
        """
        try:
            # Build query
            query = select(AllowedEmailDomain)
            
            if not include_inactive:
                query = query.where(AllowedEmailDomain.is_active == True)

            if search:
                sanitized_search = search.strip()
                if sanitized_search:
                    search_pattern = f"%{sanitized_search}%"
                    query = query.where(
                        or_(
                            AllowedEmailDomain.domain.ilike(search_pattern),
                            AllowedEmailDomain.organization_name.ilike(search_pattern)
                        )
                    )
            
            query = query.order_by(AllowedEmailDomain.domain)
            
            result = await self.db.execute(query)
            domains = result.scalars().all()
            
            return [
                AllowedDomainResponse(**self._to_dict(domain))
                for domain in domains
            ]
            
        except Exception as e:
            logger.error(f"Error fetching domains: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch allowed domains"
            )

    async def get_domain_by_id(self, domain_id: int) -> Optional[AllowedDomainResponse]:
        """
        Get a specific domain by ID.
        
        Args:
            domain_id: Domain ID
        
        Returns:
            Domain details or None if not found
        """
        try:
            domain = await self.repo.get_by_id(domain_id)
            
            if domain:
                return AllowedDomainResponse(**self._to_dict(domain))
            return None
            
        except Exception as e:
            logger.error(f"Error fetching domain {domain_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch domain"
            )

    async def get_domain_by_name(self, domain: str) -> Optional[AllowedDomainResponse]:
        """
        Get a specific domain by domain name.
        
        Args:
            domain: Domain name (e.g., "example.com")
        
        Returns:
            Domain details or None if not found
        """
        try:
            domain_obj = await self.repo.get_by_domain(domain.lower())
            
            if domain_obj:
                return AllowedDomainResponse(**self._to_dict(domain_obj))
            return None
            
        except Exception as e:
            logger.error(f"Error fetching domain {domain}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch domain"
            )

    async def create_domain(
        self,
        domain_data: AllowedDomainCreate,
        added_by: str,
    ) -> AllowedDomainResponse:
        """
        Create a new allowed domain.
        
        Args:
            domain_data: Domain creation data
            added_by: User ID of the admin adding the domain
        
        Returns:
            Created domain details
        """
        try:
            # Check if domain already exists
            existing = await self.get_domain_by_name(domain_data.domain)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Domain '{domain_data.domain}' already exists"
                )
            
            # Create domain using repository
            from uuid import UUID
            added_by_uuid = UUID(added_by) if added_by else None
            
            new_domain = await self.repo.add_domain(
                domain=domain_data.domain.lower(),
                organization_name=domain_data.organization_name,
                added_by=added_by_uuid,
                is_active=True,
            )
            
            # Commit the transaction
            await self.db.commit()
            await self.db.refresh(new_domain)
            
            logger.info(f"Created allowed domain: {domain_data.domain}")
            return AllowedDomainResponse(**self._to_dict(new_domain))
            
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create domain: {str(e)}"
            )

    async def update_domain(
        self,
        domain_id: int,
        domain_data: AllowedDomainUpdate,
    ) -> AllowedDomainResponse:
        """
        Update an existing domain.
        
        Args:
            domain_id: Domain ID
            domain_data: Update data
        
        Returns:
            Updated domain details
        """
        try:
            # Check if domain exists
            existing = await self.repo.get_by_id(domain_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Domain with ID {domain_id} not found"
                )
            
            # Build update data
            update_data = {}

            # Allow updating domain name (rename)
            if getattr(domain_data, "domain", None) is not None:
                new_domain = domain_data.domain.lower()
                # If the new domain is different, ensure it doesn't already exist
                if new_domain != existing.domain:
                    conflict = await self.repo.get_by_domain(new_domain)
                    if conflict:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Domain '{new_domain}' already exists"
                        )
                update_data["domain"] = new_domain

            if domain_data.organization_name is not None:
                update_data["organization_name"] = domain_data.organization_name
            if domain_data.is_active is not None:
                update_data["is_active"] = domain_data.is_active

            if not update_data:
                # No changes, return existing
                return AllowedDomainResponse(**self._to_dict(existing))

            # Update domain
            updated = await self.repo.update_by_id(domain_id, **update_data)
            await self.db.commit()
            await self.db.refresh(updated)
            
            logger.info(f"Updated domain ID {domain_id}")
            return AllowedDomainResponse(**self._to_dict(updated))
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update domain"
            )

    async def delete_domain(self, domain_id: int) -> bool:
        """
        Delete a domain (hard delete).
        
        Args:
            domain_id: Domain ID
        
        Returns:
            True if successful
        """
        try:
            # Check if domain exists
            existing = await self.repo.get_by_id(domain_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Domain with ID {domain_id} not found"
                )
            
            domain_name = existing.domain
            
            # Delete domain
            await self.repo.delete_by_id(domain_id)
            await self.db.commit()
            
            logger.info(f"Deleted domain ID {domain_id} ({domain_name})")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting domain: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete domain"
            )

    async def toggle_domain_status(
        self,
        domain_id: int,
        is_active: bool,
    ) -> AllowedDomainResponse:
        """
        Activate or deactivate a domain.
        
        Args:
            domain_id: Domain ID
            is_active: New active status
        
        Returns:
            Updated domain details
        """
        return await self.update_domain(
            domain_id,
            AllowedDomainUpdate(is_active=is_active)
        )

    async def is_domain_allowed(self, domain: str) -> bool:
        """
        Check if a domain name is allowed for registration.
        
        Args:
            domain: Domain name to check (lowercased preferred)
        
        Returns:
            True if domain is allowed, False otherwise
        """
        try:
            domain_name = domain.lower()
            domain_obj = await self.repo.get_by_domain(domain_name)
            return domain_obj is not None and domain_obj.is_active
        except Exception as e:
            logger.error(f"Error checking domain: {str(e)}")
            # Fail closed - don't allow if check fails
            return False

    def _to_dict(self, domain: AllowedEmailDomain) -> dict:
        """
        Convert AllowedEmailDomain model to dictionary.
        
        Args:
            domain: AllowedEmailDomain SQLAlchemy model instance
        
        Returns:
            dict: Dictionary representation
        """
        return {
            "id": domain.id,
            "domain": domain.domain,
            "organization_name": domain.organization_name,
            "is_active": domain.is_active,
            "added_by": str(domain.added_by) if domain.added_by else None,
            "created_at": domain.created_at.isoformat() if domain.created_at else None,
        }
