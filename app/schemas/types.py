"""
Custom Pydantic types for consistent data handling across schemas.

This module provides reusable type annotations that handle common
data conversion patterns, particularly for Supabase/PostgreSQL responses.
"""
from datetime import datetime
from typing import Annotated, Union
from pydantic import BeforeValidator
from enum import Enum


def parse_flexible_datetime(value: Union[str, datetime, None]) -> datetime | None:
    """
    Parse datetime from various input formats.
    
    Handles:
    - datetime objects (passed through)
    - ISO 8601 strings from PostgreSQL/Supabase (e.g., '2025-11-28T07:30:41.729031+00:00')
    - ISO strings with 'Z' suffix (converted to +00:00)
    - None values (passed through)
    
    Args:
        value: The value to parse
        
    Returns:
        datetime object or None
        
    Raises:
        ValueError: If value cannot be parsed as datetime
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Handle ISO format strings from Supabase/PostgreSQL
        # Replace 'Z' suffix with '+00:00' for proper parsing
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    raise ValueError(f"Cannot parse datetime from {type(value)}: {value}")


# Annotated type that accepts both datetime objects and ISO strings
# Use this instead of `datetime` in Pydantic models that receive data from Supabase
FlexibleDateTime = Annotated[datetime, BeforeValidator(parse_flexible_datetime)]


class GradeLevel(int, Enum):
    """
    Enum representing grade levels (1, 2, or 3).

    Values mirror the integer representation stored in the database.
    """
    ONE = 1
    TWO = 2
    THREE = 3


class RoleType(int, Enum):
    """
    Enum representing user roles across the application.

    Values match the integer representation used in the database.
    """
    ADMIN = 1
    TEACHER = 2
    STUDENT = 3
