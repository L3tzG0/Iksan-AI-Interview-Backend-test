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

    # -------------------- Internal helpers --------------------
    def _normalize_domain(self, domain: str) -> str:
        """Normalize domain strings for consistent comparisons (lowercase + strip)."""
        return domain.lower().strip()

    def _to_allowed_domain_response(self, record: dict) -> AllowedDomainResponse:
        """Convert a DB record dict to AllowedDomainResponse."""
        return AllowedDomainResponse(**record)

    async def _get_domain_by_name(self, domain: str, active_only: bool = False) -> Optional[AllowedDomainResponse]:
        """Internal helper to fetch a domain by name. Returns AllowedDomainResponse or None."""
        domain_name = self._normalize_domain(domain)
        query = self.supabase.table("allowed_email_domains").select("*").eq("domain", domain_name)
        if active_only:
            query = query.eq("is_active", True)
        # Use maybe_single() to get a dict or None for single-row queries.
        response = await query.maybe_single().execute()
        if response.data:
            return self._to_allowed_domain_response(response.data)
        return None

    async def _get_domain_by_id(self, domain_id: int) -> Optional[AllowedDomainResponse]:
        """Internal helper to fetch a domain by id. Returns AllowedDomainResponse or None."""
        response = await (
            self.supabase.table("allowed_email_domains")
            .select("*")
            .eq("id", domain_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return self._to_allowed_domain_response(response.data)
        return None

    def _ensure_mutation_response(self, response, error_detail: str):
        """Ensure mutation response contains data, otherwise raise 500 HTTPException."""
        if not getattr(response, "data", None):
            logger.error(f"Mutation failed or returned no data: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
        # return the first record (consistent with Supabase behaviour)
        return response.data[0]

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
            return await self._get_domain_by_id(domain_id)
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
            return await self._get_domain_by_name(domain)
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
            # Normalize and check if domain already exists
            normalized = self._normalize_domain(domain_data.domain)
            existing = await self._get_domain_by_name(normalized)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Domain '{normalized}' already exists"
                )
            
            # Insert domain
            insert_data = {
                "domain": normalized,
                "description": domain_data.description,
                "is_active": True,
                "added_by": added_by,
            }
            
            response = await (
                self.supabase.table("allowed_email_domains")
                .insert(insert_data)
                .execute()
            )
            
            record = self._ensure_mutation_response(response, "Failed to create domain")
            
            logger.info(f"Created allowed domain: {normalized}")
            return self._to_allowed_domain_response(record)
            
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

            # Allow updating domain name (rename)
            if getattr(domain_data, "domain", None) is not None:
                new_domain = self._normalize_domain(domain_data.domain)
                # If the new domain is different, ensure it doesn't already exist
                if new_domain != (existing.domain or "").lower():
                    conflict = await self._get_domain_by_name(new_domain)
                    if conflict:
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=f"Domain '{new_domain}' already exists"
                        )
                update_data["domain"] = new_domain

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
            
            record = self._ensure_mutation_response(response, "Failed to update domain")
            
            logger.info(f"Updated domain ID {domain_id}")
            return self._to_allowed_domain_response(record)
            
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
            domain_name = self._normalize_domain(domain)
            domain_obj = await self._get_domain_by_name(domain_name, active_only=True)
            return domain_obj is not None
        except Exception as e:
            logger.error(f"Error checking domain: {str(e)}")
            # Fail closed - don't allow if check fails
            return False
