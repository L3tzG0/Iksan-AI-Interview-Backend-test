"""
AllowedEmailDomain model for email domain restrictions.

AllowedEmailDomains controls which email domains are permitted
for user registration, enabling organization-level access control.

Schema Reference:
- migrations/008_email_domain_restrictions.sql
- migrations/009_email_domain_org_name.sql (renames description to organization_name)
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import String, Boolean, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class AllowedEmailDomain(Base, TimestampMixin):
    """
    AllowedEmailDomain entity for email domain whitelisting.
    
    Attributes:
        id: Primary key (BIGSERIAL)
        domain: Email domain (e.g., 'example.com', 'students.internal')
        organization_name: Name of the organization this domain belongs to
        is_active: Whether this domain is currently allowed
        added_by: User who added this domain (optional)
        created_at: Timestamp when domain was added
        updated_at: Timestamp of last modification
    
    Note: The RPC function `is_email_domain_allowed()` queries this table
    to validate email addresses during registration.
    """
    __tablename__ = "allowed_email_domains"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    domain: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
        comment="Email domain (e.g., 'example.com')",
    )
    
    # Renamed from 'description' in migration 009
    organization_name: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Name of the organization this domain belongs to",
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        index=True,
    )
    
    # User who added this domain (optional FK, may be null)
    # Note: This referenced auth.users in original schema, but now references user_profiles
    # after migration 011. Setting to nullable to handle orphaned records.
    added_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Constraints and indexes
    __table_args__ = (
        # Domain format validation (lowercase, standard format)
        CheckConstraint(
            r"domain ~ '^[a-z0-9.-]+\.[a-z]{2,}$'",
            name="domain_format",
        ),
        Index("idx_allowed_email_domains_domain", "domain"),
        Index("idx_allowed_email_domains_active", "is_active", postgresql_where="is_active = true"),
    )
    
    def __repr__(self) -> str:
        return f"<AllowedEmailDomain(id={self.id}, domain='{self.domain}', is_active={self.is_active})>"
