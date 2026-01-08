"""
Custom JWT Token Management

This module provides JWT signing and verification for the custom authentication
system with self-managed JWTs.

Features:
- JWT creation with configurable expiry
- Secure signature verification using HS256
- Refresh token support
- Token claims validation
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from app.core.config import settings


class TokenType(str, Enum):
    """Token type enumeration."""
    ACCESS = "access"
    REFRESH = "refresh"


@dataclass
class TokenPayload:
    """Decoded JWT token payload."""
    sub: str  # User ID (UUID string)
    email: str
    role_id: Optional[int]
    role_name: Optional[str]
    token_type: TokenType
    exp: datetime
    iat: datetime
    jti: Optional[str] = None  # JWT ID for token revocation
    
    @property
    def user_id(self) -> str:
        """Alias for sub (subject) claim."""
        return self.sub
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.exp


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 0  # Access token expiry in seconds


class JWTError(Exception):
    """Base JWT error."""
    pass


class JWTExpiredError(JWTError):
    """Token has expired."""
    pass


class JWTInvalidError(JWTError):
    """Token is invalid (bad signature, malformed, etc.)."""
    pass


class JWTManager:
    """
    JWT Token Manager for creating and validating tokens.
    
    Uses HS256 algorithm with a shared secret key.
    Configurable access and refresh token expiry times.
    """
    
    ALGORITHM = "HS256"
    
    def __init__(
        self,
        secret_key: str,
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7,
        issuer: str = "iksan-ai-interview",
        audience: str = "iksan-ai-interview-api"
    ):
        """
        Initialize JWT Manager.
        
        Args:
            secret_key: Secret key for signing tokens
            access_token_expire_minutes: Access token validity in minutes
            refresh_token_expire_days: Refresh token validity in days
            issuer: Token issuer claim
            audience: Token audience claim
        """
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.issuer = issuer
        self.audience = audience
    
    def create_access_token(
        self,
        user_id: str,
        email: str,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new access token.
        
        Args:
            user_id: User UUID string
            email: User email
            role_id: User role ID
            role_name: User role name
            additional_claims: Optional additional claims to include
            
        Returns:
            Encoded JWT access token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "email": email,
            "role_id": role_id,
            "role_name": role_name,
            "token_type": TokenType.ACCESS.value,
            "iat": now,
            "exp": expire,
            "iss": self.issuer,
            "aud": self.audience,
            "jti": secrets.token_urlsafe(16)
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def create_refresh_token(
        self,
        user_id: str,
        email: str
    ) -> str:
        """
        Create a new refresh token.
        
        Args:
            user_id: User UUID string
            email: User email
            
        Returns:
            Encoded JWT refresh token
        """
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "email": email,
            "token_type": TokenType.REFRESH.value,
            "iat": now,
            "exp": expire,
            "iss": self.issuer,
            "aud": self.audience,
            "jti": secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def create_token_pair(
        self,
        user_id: str,
        email: str,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> TokenPair:
        """
        Create both access and refresh tokens.
        
        Args:
            user_id: User UUID string
            email: User email
            role_id: User role ID
            role_name: User role name
            additional_claims: Optional additional claims for access token
            
        Returns:
            TokenPair with access and refresh tokens
        """
        access_token = self.create_access_token(
            user_id=user_id,
            email=email,
            role_id=role_id,
            role_name=role_name,
            additional_claims=additional_claims
        )
        
        refresh_token = self.create_refresh_token(
            user_id=user_id,
            email=email
        )
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def verify_token(
        self,
        token: str,
        expected_type: Optional[TokenType] = None
    ) -> TokenPayload:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            expected_type: Optional expected token type (access/refresh)
            
        Returns:
            TokenPayload with decoded claims
            
        Raises:
            JWTExpiredError: If token has expired
            JWTInvalidError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # Validate token type if specified
            token_type_str = payload.get("token_type")
            if expected_type and token_type_str != expected_type.value:
                raise JWTInvalidError(
                    f"Invalid token type. Expected {expected_type.value}, got {token_type_str}"
                )
            
            return TokenPayload(
                sub=payload["sub"],
                email=payload.get("email", ""),
                role_id=payload.get("role_id"),
                role_name=payload.get("role_name"),
                token_type=TokenType(payload.get("token_type", TokenType.ACCESS.value)),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload.get("jti")
            )
            
        except ExpiredSignatureError:
            raise JWTExpiredError("Token has expired")
        except InvalidTokenError as e:
            raise JWTInvalidError(f"Invalid token: {str(e)}")
    
    def verify_access_token(self, token: str) -> TokenPayload:
        """Verify an access token."""
        return self.verify_token(token, expected_type=TokenType.ACCESS)
    
    def verify_refresh_token(self, token: str) -> TokenPayload:
        """Verify a refresh token."""
        return self.verify_token(token, expected_type=TokenType.REFRESH)
    
    def refresh_tokens(
        self,
        refresh_token: str,
        role_id: Optional[int] = None,
        role_name: Optional[str] = None
    ) -> TokenPair:
        """
        Generate new token pair from a valid refresh token.
        
        Args:
            refresh_token: Valid refresh token
            role_id: Current role ID (fetched from DB)
            role_name: Current role name (fetched from DB)
            
        Returns:
            New TokenPair
            
        Raises:
            JWTExpiredError: If refresh token has expired
            JWTInvalidError: If refresh token is invalid
        """
        payload = self.verify_refresh_token(refresh_token)
        
        return self.create_token_pair(
            user_id=payload.sub,
            email=payload.email,
            role_id=role_id,
            role_name=role_name
        )


# Global JWT manager instance - initialized from settings
def get_jwt_manager() -> JWTManager:
    """Get the global JWT manager instance."""
    return JWTManager(
        secret_key=settings.JWT_SECRET_KEY,
        access_token_expire_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
        refresh_token_expire_days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE
    )
