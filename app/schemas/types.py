"""
Custom Pydantic types for consistent data handling across schemas.

This module provides reusable type annotations that handle common
data conversion patterns, particularly for Supabase/PostgreSQL responses.
"""
from datetime import datetime
from typing import Annotated, Union
from pydantic import BeforeValidator


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
