"""
Domain Repository for email domain restriction operations.

This repository handles CRUD operations and specialized queries
for the AllowedEmailDomain model, including RPC function calls
for domain validation.
"""
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allowed_email_domain import AllowedEmailDomain
from app.repositories.base import BaseRepository


class DomainRepository(BaseRepository[AllowedEmailDomain]):
    """
    Repository for AllowedEmailDomain entity operations.
    
    Provides methods for email domain management and validation.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with session and AllowedEmailDomain model."""
        super().__init__(session, AllowedEmailDomain)
    
    async def is_email_allowed(self, email: str) -> bool:
        """
        Check if an email address is from an allowed domain.
        
        Calls the PostgreSQL RPC function `is_email_domain_allowed`
        for consistent validation logic.
        
        Args:
            email: The email address to validate
        
        Returns:
            True if the email domain is allowed, False otherwise
        """
        result = await self.session.execute(
            text("SELECT public.is_email_domain_allowed(:p_email) as is_allowed"),
            {"p_email": email}
        )
        row = result.fetchone()
        return bool(row.is_allowed) if row else False
    
    async def get_by_domain(self, domain: str) -> Optional[AllowedEmailDomain]:
        """
        Get domain entry by domain name.
        
        Args:
            domain: The domain name (e.g., 'example.com')
        
        Returns:
            AllowedEmailDomain if found, None otherwise
        """
        return await self.get_one_by(domain=domain.lower())
    
    async def get_active_domains(self) -> Sequence[AllowedEmailDomain]:
        """
        Get all active (allowed) domains.
        
        Returns:
            List of active AllowedEmailDomain entities
        """
        stmt = (
            select(AllowedEmailDomain)
            .where(AllowedEmailDomain.is_active == True)
            .order_by(AllowedEmailDomain.domain)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def add_domain(
        self,
        domain: str,
        description: Optional[str] = None,
        added_by: Optional[UUID] = None,
        is_active: bool = True,
    ) -> AllowedEmailDomain:
        """
        Add a new allowed email domain.
        
        Args:
            domain: The domain name (will be lowercased)
            description: Name of the organization
            added_by: UUID of the user adding the domain
            is_active: Whether the domain should be active
        
        Returns:
            The created AllowedEmailDomain entity
        
        Raises:
            ValueError: If domain format is invalid
        """
        import re
        
        # Validate domain format
        domain = domain.lower()
        if not re.match(r'^[a-z0-9.-]+\.[a-z]{2,}$', domain):
            raise ValueError(
                f"Invalid domain format: {domain}. "
                "Domain must be lowercase and follow standard format (e.g., example.com)"
            )
        
        return await self.create(
            domain=domain,
            description=description,
            added_by=added_by,
            is_active=is_active,
        )
    
    async def activate_domain(self, domain_id: int) -> Optional[AllowedEmailDomain]:
        """
        Activate a domain (allow registrations from it).
        
        Args:
            domain_id: The domain's primary key ID
        
        Returns:
            Updated AllowedEmailDomain, or None if not found
        """
        return await self.update_by_id(domain_id, is_active=True)
    
    async def deactivate_domain(self, domain_id: int) -> Optional[AllowedEmailDomain]:
        """
        Deactivate a domain (block registrations from it).
        
        Args:
            domain_id: The domain's primary key ID
        
        Returns:
            Updated AllowedEmailDomain, or None if not found
        """
        return await self.update_by_id(domain_id, is_active=False)
    
    async def update_description(
        self,
        domain_id: int,
        description: str,
    ) -> Optional[AllowedEmailDomain]:
        """
        Update the organization name for a domain.
        
        Args:
            domain_id: The domain's primary key ID
            description: New organization name
        
        Returns:
            Updated AllowedEmailDomain, or None if not found
        """
        return await self.update_by_id(domain_id, description=description)
    
    async def search_domains(
        self,
        query: str,
        include_inactive: bool = False,
        limit: int = 20,
    ) -> Sequence[AllowedEmailDomain]:
        """
        Search domains by name or organization.
        
        Args:
            query: Search query string
            include_inactive: Whether to include inactive domains
            limit: Maximum results to return
        
        Returns:
            List of matching AllowedEmailDomain entities
        """
        from sqlalchemy import or_
        
        conditions = [
            or_(
                AllowedEmailDomain.domain.ilike(f"%{query}%"),
                AllowedEmailDomain.description.ilike(f"%{query}%"),
            )
        ]
        if not include_inactive:
            conditions.append(AllowedEmailDomain.is_active == True)
        
        stmt = (
            select(AllowedEmailDomain)
            .where(*conditions)
            .order_by(AllowedEmailDomain.domain)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_domain_stats(self) -> dict:
        """
        Get statistics about email domains.
        
        Returns:
            Dict with total_domains, active_domains counts
        """
        from sqlalchemy import func
        
        total_stmt = select(func.count()).select_from(AllowedEmailDomain)
        active_stmt = (
            select(func.count())
            .select_from(AllowedEmailDomain)
            .where(AllowedEmailDomain.is_active == True)
        )
        
        total = (await self.session.execute(total_stmt)).scalar() or 0
        active = (await self.session.execute(active_stmt)).scalar() or 0
        
        return {
            "total_domains": total,
            "active_domains": active,
            "inactive_domains": total - active,
        }
