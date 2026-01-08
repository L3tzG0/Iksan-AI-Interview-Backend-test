"""
JWT Token utilities for programmatic use.

This module provides utilities to parse and analyze JWT tokens,
supporting both backend service tokens and end-user tokens.

Example usage:
    from app.utils.jwt_utils import parse_jwt_token, TokenInfo
    
    token_info = parse_jwt_token(token_string)
    print(token_info.user_id)
    print(token_info.email)
    print(token_info.is_expired)
"""

import json
import base64
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class TokenInfo:
    """Container for parsed JWT token information."""
    
    # Standard JWT claims
    user_id: Optional[str]
    email: Optional[str]
    email_verified: bool
    issued_at: Optional[datetime]
    expires_at: Optional[datetime]
    not_before: Optional[datetime]
    issuer: Optional[str]
    audience: Optional[str]
    
    # Token-specific metadata
    role: Optional[str]
    app_metadata: Optional[Dict[str, Any]]
    user_metadata: Optional[Dict[str, Any]]
    
    # Metadata
    is_expired: bool
    raw_payload: Dict[str, Any]
    
    def __repr__(self) -> str:
        return (
            f"TokenInfo(user_id={self.user_id}, email={self.email}, "
            f"role={self.role}, expired={self.is_expired})"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'user_id': self.user_id,
            'email': self.email,
            'email_verified': self.email_verified,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'not_before': self.not_before.isoformat() if self.not_before else None,
            'issuer': self.issuer,
            'audience': self.audience,
            'role': self.role,
            'app_metadata': self.app_metadata,
            'user_metadata': self.user_metadata,
            'is_expired': self.is_expired,
        }


class JWTDecodeError(Exception):
    """Exception raised when JWT decoding fails."""
    pass


class JWTExpiredError(Exception):
    """Exception raised when JWT token is expired."""
    pass


def decode_base64url(data: str) -> str:
    """
    Decode base64url encoded string.
    
    Args:
        data: Base64url encoded string
        
    Returns:
        Decoded string
        
    Raises:
        JWTDecodeError: If decoding fails
    """
    try:
        # Add padding if necessary
        padding = 4 - len(data) % 4
        if padding != 4:
            data += '=' * padding
        
        return base64.urlsafe_b64decode(data).decode('utf-8')
    except Exception as e:
        raise JWTDecodeError(f"Failed to decode base64url: {str(e)}")


def parse_jwt_token(token: str) -> TokenInfo:
    """
    Parse a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenInfo object with parsed claims
        
    Raises:
        JWTDecodeError: If token format is invalid or cannot be decoded
        JWTExpiredError: If token is expired
        
    Example:
        try:
            token_info = parse_jwt_token(access_token)
            print(f"User: {token_info.email}")
            print(f"Expired: {token_info.is_expired}")
        except JWTDecodeError as e:
            print(f"Invalid token: {e}")
        except JWTExpiredError as e:
            print(f"Token expired: {e}")
    """
    try:
        # Parse JWT structure
        parts = token.split('.')
        
        if len(parts) != 3:
            raise JWTDecodeError(
                f"Invalid JWT format. Expected 3 parts, got {len(parts)}"
            )
        
        header_part, payload_part, signature_part = parts
        
        # Decode header (for information only)
        try:
            header_json = decode_base64url(header_part)
            header = json.loads(header_json)
        except (JWTDecodeError, json.JSONDecodeError) as e:
            raise JWTDecodeError(f"Failed to decode header: {str(e)}")
        
        # Decode payload
        try:
            payload_json = decode_base64url(payload_part)
            payload = json.loads(payload_json)
        except (JWTDecodeError, json.JSONDecodeError) as e:
            raise JWTDecodeError(f"Failed to decode payload: {str(e)}")
        
        # Convert timestamps
        def ts_to_datetime(timestamp: Optional[int]) -> Optional[datetime]:
            if timestamp is None:
                return None
            try:
                return datetime.utcfromtimestamp(timestamp)
            except (ValueError, OSError):
                return None
        
        issued_at = ts_to_datetime(payload.get('iat'))
        expires_at = ts_to_datetime(payload.get('exp'))
        not_before = ts_to_datetime(payload.get('nbf'))
        
        # Check expiration
        is_expired = False
        if expires_at and datetime.utcnow() > expires_at:
            is_expired = True
        
        # Create TokenInfo
        token_info = TokenInfo(
            user_id=payload.get('sub'),
            email=payload.get('email'),
            email_verified=payload.get('email_verified', False),
            issued_at=issued_at,
            expires_at=expires_at,
            not_before=not_before,
            issuer=payload.get('iss'),
            audience=payload.get('aud'),
            role=payload.get('role'),
            app_metadata=payload.get('app_metadata'),
            user_metadata=payload.get('user_metadata'),
            is_expired=is_expired,
            raw_payload=payload,
        )
        
        return token_info
        
    except JWTDecodeError:
        raise
    except Exception as e:
        raise JWTDecodeError(f"Unexpected error parsing token: {str(e)}")


def extract_user_id(token: str) -> str:
    """
    Extract user ID (subject) from token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID
        
    Raises:
        JWTDecodeError: If token cannot be decoded
    """
    token_info = parse_jwt_token(token)
    if not token_info.user_id:
        raise JWTDecodeError("Token does not contain a subject (user_id)")
    return token_info.user_id


def extract_email(token: str) -> str:
    """
    Extract email from token.
    
    Args:
        token: JWT token string
        
    Returns:
        Email address
        
    Raises:
        JWTDecodeError: If token cannot be decoded
    """
    token_info = parse_jwt_token(token)
    if not token_info.email:
        raise JWTDecodeError("Token does not contain an email")
    return token_info.email


def get_custom_claims(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract custom user metadata claims from token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary of custom claims or None
        
    Raises:
        JWTDecodeError: If token cannot be decoded
    """
    token_info = parse_jwt_token(token)
    return token_info.user_metadata


def validate_token_not_expired(token: str) -> bool:
    """
    Check if token is still valid (not expired).
    
    Args:
        token: JWT token string
        
    Returns:
        True if token is valid, False if expired
        
    Raises:
        JWTDecodeError: If token cannot be decoded
    """
    token_info = parse_jwt_token(token)
    return not token_info.is_expired
