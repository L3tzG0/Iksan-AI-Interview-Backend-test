"""
Authenticated User Model

Provides a normalized user model for authentication that is provider-agnostic.
This replaces the Supabase User object with our own internal representation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from app.core.jwt import TokenPayload


@dataclass
class AuthenticatedUser:
    """
    Normalized authenticated user representation.
    
    This is the standard user object returned by the authentication system,
    independent of any specific auth provider.
    """
    id: UUID
    email: str
    full_name: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Additional metadata that can be populated from user_profiles or JWT claims
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_student(self) -> bool:
        """Check if user has student role."""
        return self.role_name == "student" or self.role_id == 3
    
    @property
    def is_teacher(self) -> bool:
        """Check if user has teacher role."""
        return self.role_name == "teacher" or self.role_id == 2
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role_name == "admin" or self.role_id == 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "role_id": self.role_id,
            "role_name": self.role_name,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_user_profile(cls, profile: Dict[str, Any]) -> "AuthenticatedUser":
        """
        Create AuthenticatedUser from a user_profiles database record.
        
        Args:
            profile: Dictionary from user_profiles table with optional role join
            
        Returns:
            AuthenticatedUser instance
        """
        role_data = profile.get("roles", {}) or {}
        
        return cls(
            id=UUID(profile["id"]) if isinstance(profile["id"], str) else profile["id"],
            email=profile.get("email", ""),
            full_name=profile.get("full_name"),
            role_id=profile.get("role_id"),
            role_name=role_data.get("role_name") if isinstance(role_data, dict) else None,
            email_verified=True,  # We manage our own users, consider them verified
            created_at=profile.get("created_at"),
            updated_at=profile.get("updated_at"),
            metadata={}
        )
    
    @classmethod
    def from_jwt_payload(cls, payload: "TokenPayload") -> "AuthenticatedUser":
        """
        Create AuthenticatedUser from JWT token payload.
        
        Args:
            payload: TokenPayload from JWT verification
            
        Returns:
            AuthenticatedUser instance
        """
        from app.core.jwt import TokenPayload  # Import here to avoid circular dependency
        
        return cls(
            id=UUID(payload.sub),
            email=payload.email,
            role_id=payload.role_id,
            role_name=payload.role_name,
            email_verified=True,
            metadata={}
        )
