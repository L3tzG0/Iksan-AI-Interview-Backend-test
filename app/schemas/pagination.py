"""
Generic pagination schemas for standardized paginated API responses.

This module provides reusable pagination patterns to ensure consistent
API responses across all list endpoints.
"""
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Standard pagination parameters.
    Can be used as a dependency or for validation.
    """
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response wrapper.
    
    Usage:
        class StudentListResponse(PaginatedResponse[StudentResponse]):
            pass
    
    Or directly:
        PaginatedResponse[StudentResponse](items=[...], total=100, skip=0, limit=20)
    """
    items: List[T]
    total: int = Field(description="Total number of records matching the query")
    skip: int = Field(description="Number of records skipped")
    limit: int = Field(description="Maximum records requested")
    has_more: bool = Field(description="Whether there are more records after this page")

    class Config:
        from_attributes = True


# Type aliases for common paginated responses
class PaginatedClasses(PaginatedResponse):
    """Paginated list of classes"""
    pass


class PaginatedSchools(PaginatedResponse):
    """Paginated list of schools"""
    pass


class PaginatedMajors(PaginatedResponse):
    """Paginated list of majors"""
    pass

class PaginatedUsers(PaginatedResponse):
    """Paginated list of user profiles"""
    pass


class PaginatedSessions(PaginatedResponse):
    """Paginated list of interview sessions"""
    pass


def create_paginated_response(
    items: List[T],
    total: int,
    skip: int,
    limit: int
) -> dict:
    """
    Helper function to create a paginated response dict.
    
    Args:
        items: List of items for current page
        total: Total count of all matching items
        skip: Number of items skipped
        limit: Maximum items per page
    
    Returns:
        dict: Paginated response data
    """
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(items) < total
    }
