"""
Email Domain Management Service

Handles CRUD operations for allowed email domains.
"""

import logging
from typing import List, Optional
from datetime import datetime
from supabase import AsyncClient
from fastapi import HTTPException, status

from app.schemas.domain import (
    AllowedDomainCreate,
    AllowedDomainUpdate,
    AllowedDomainResponse,
)

logger = logging.getLogger(__name__)


class DomainService:
    """Service for managing allowed email domains."""

    def __init__(self, supabase: AsyncClient):
        self.supabase = supabase

    async def get_all_domains(
        self,
        include_inactive: bool = False,
    ) -> List[AllowedDomainResponse]:
        """
        Get all allowed email domains.
        
        Args:
            include_inactive: If True, includes inactive domains
        
        Returns:
            List of allowed domains
        """
        try:
            query = self.supabase.table("allowed_email_domains").select("*")
            
            if not include_inactive:
                query = query.eq("is_active", True)
            
            query = query.order("domain", desc=False)
            
            response = await query.execute()
            
            return [
                AllowedDomainResponse(**domain)
                for domain in response.data
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
            response = await self.supabase.table("allowed_email_domains").select("*").eq("id", domain_id).maybe_single().execute()
            
            if response.data:
                return AllowedDomainResponse(**response.data)
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
            response = await (
                self.supabase.table("allowed_email_domains")
                .select("*")
                .eq("domain", domain.lower())
                .maybe_single()
                .execute()
            )
            
            if response.data:
                return AllowedDomainResponse(**response.data)
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
            
            # Insert domain
            insert_data = {
                "domain": domain_data.domain.lower(),
                "description": domain_data.description,
                "is_active": True,
                "added_by": added_by,
            }
            
            response = await (
                self.supabase.table("allowed_email_domains")
                .insert(insert_data)
                .execute()
            )
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create domain"
                )
            
            logger.info(f"Created allowed domain: {domain_data.domain}")
            return AllowedDomainResponse(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
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
            existing = await self.get_domain_by_id(domain_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Domain with ID {domain_id} not found"
                )
            
            # Build update data
            update_data = {}
            if domain_data.description is not None:
                update_data["description"] = domain_data.description
            if domain_data.is_active is not None:
                update_data["is_active"] = domain_data.is_active
            
            if not update_data:
                # No changes
                return existing
            
            # Update domain
            response = await (
                self.supabase.table("allowed_email_domains")
                .update(update_data)
                .eq("id", domain_id)
                .execute()
            )
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update domain"
                )
            
            logger.info(f"Updated domain ID {domain_id}")
            return AllowedDomainResponse(**response.data[0])
            
        except HTTPException:
            raise
        except Exception as e:
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
            existing = await self.get_domain_by_id(domain_id)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Domain with ID {domain_id} not found"
                )
            
            # Delete domain
            await (
                self.supabase.table("allowed_email_domains")
                .delete()
                .eq("id", domain_id)
                .execute()
            )
            
            logger.info(f"Deleted domain ID {domain_id} ({existing.domain})")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
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
            response = await (
                self.supabase.table("allowed_email_domains")
                .select("id")
                .eq("domain", domain_name)
                .eq("is_active", True)
                .maybe_single()
                .execute()
            )
            return response.data is not None
        except Exception as e:
            logger.error(f"Error checking domain: {str(e)}")
            # Fail closed - don't allow if check fails
            return False
