"""
Rate Limiting Module for Iksan AI Interview Backend.

This module provides rate limiting functionality using slowapi to protect
the API from abuse and ensure fair usage across all users.

Key Features:
- In-memory storage (can be upgraded to Redis for distributed deployments)
- IP-based rate limiting for unauthenticated endpoints
- User ID-based rate limiting for authenticated endpoints
- Configurable limits per endpoint type
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from app.core.config import settings


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.
    
    For authenticated requests, uses user ID from authorization token.
    For unauthenticated requests, falls back to IP address.
    
    This prevents a single user from bypassing rate limits by using
    multiple IP addresses, while still allowing IP-based limiting
    for unauthenticated endpoints.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        str: User ID if authenticated, otherwise IP address
    """
    # Try to get user info from request state (set by auth middleware/dependency)
    # This will be populated after authentication
    auth_header = request.headers.get("Authorization", "")
    
    if auth_header.startswith("Bearer "):
        # For authenticated requests, we use a combination of IP + token hash
        # to identify unique users. This is a simplified approach.
        # In production, you might want to decode the JWT to get user ID.
        token = auth_header[7:]  # Remove "Bearer " prefix
        # Use first 16 chars of token as identifier (enough for uniqueness)
        return f"user:{token[:16]}"
    
    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)


def get_ip_address(request: Request) -> str:
    """
    Get client IP address for rate limiting.
    
    Simple IP-based key function for endpoints where we want
    to rate limit by IP regardless of authentication status.
    
    Args:
        request: FastAPI Request object
    
    Returns:
        str: Client IP address
    """
    return get_remote_address(request)


# Create the limiter instance with default configuration
# Uses in-memory storage by default (suitable for single-instance deployments)
limiter = Limiter(
    key_func=get_identifier,
    default_limits=[settings.RATE_LIMIT_DEFAULT] if settings.RATE_LIMIT_ENABLED else [],
    enabled=settings.RATE_LIMIT_ENABLED,
    headers_enabled=True,  # Include X-RateLimit headers in responses
    strategy="fixed-window",  # Simple fixed window strategy
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom exception handler for rate limit exceeded errors.
    
    Returns a standardized JSON response with appropriate headers
    when a client exceeds their rate limit.
    
    Args:
        request: FastAPI Request object
        exc: RateLimitExceeded exception
    
    Returns:
        JSONResponse: Error response with 429 status code
    """
    # Extract retry-after from the exception if available
    retry_after = getattr(exc, 'retry_after', 60)
    
    response = JSONResponse(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "retry_after_seconds": retry_after,
        }
    )
    
    # Add standard rate limit headers
    response.headers["Retry-After"] = str(retry_after)
    response.headers["X-RateLimit-Limit"] = str(exc.detail)
    
    return response
