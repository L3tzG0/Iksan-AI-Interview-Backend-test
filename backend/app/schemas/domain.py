"""
Schemas for allowed email domain management
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re


class AllowedDomainBase(BaseModel):
    """Base schema for allowed email domain"""
    domain: str = Field(..., description="Email domain (e.g., example.com)")
    description: Optional[str] = Field(
        None,
        description="Organization name associated with the domain",
    )

    @validator("domain")
    def validate_domain(cls, v):
        """Validate domain format"""
        if not v:
            raise ValueError("Domain cannot be empty")
        
        # Convert to lowercase
        v = v.lower().strip()
        
        # Basic domain validation
        domain_pattern = r"^[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(domain_pattern, v):
            raise ValueError(
                "Invalid domain format. Domain must be lowercase and follow standard format (e.g., example.com)"
            )
        
        return v


class AllowedDomainCreate(AllowedDomainBase):
    """Schema for creating a new allowed domain"""
    pass


class AllowedDomainUpdate(BaseModel):
    """Schema for updating an allowed domain

    `domain` is optional here to support renames. Validate the domain format
    the same way as on create (lowercase, trimmed, basic format check).
    """
    domain: Optional[str] = Field(None, description="Updated domain name")
    description: Optional[str] = Field(
        None,
        description="Updated organization name",
    )
    is_active: Optional[bool] = Field(None, description="Active status")

    @validator("domain")
    def validate_domain(cls, v):
        """Validate domain format when provided"""
        if v is None:
            return v
        v = v.lower().strip()
        domain_pattern = r"^[a-z0-9.-]+\.[a-z]{2,}$"
        if not re.match(domain_pattern, v):
            raise ValueError(
                "Invalid domain format. Domain must be lowercase and follow standard format (e.g., example.com)"
            )
        return v


class AllowedDomainResponse(AllowedDomainBase):
    """Schema for allowed domain response"""
    id: int
    is_active: bool
    added_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DomainCheckRequest(BaseModel):
    """Schema for checking if an email domain is allowed"""
    email: str = Field(..., description="Email address to check")

    @validator("email")
    def validate_email(cls, v):
        """Basic email validation"""
        if not v or "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class DomainCheckResponse(BaseModel):
    """Schema for domain check response"""
    email: str
    domain: str
    is_allowed: bool
    message: str
