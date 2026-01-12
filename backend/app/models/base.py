"""
Base model utilities and mixins for SQLAlchemy models.

This module provides:
- TimestampMixin: Adds created_at and updated_at columns
- Common type definitions and annotations

All timestamps are stored with timezone information (TIMESTAMPTZ in PostgreSQL).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamp columns.
    
    - created_at: Set automatically on insert, immutable
    - updated_at: Set automatically on insert, updated on every modification
    
    These columns match the schema defined in migrations/001_initial_schema.sql
    and use database-level defaults for consistency.
    
    Usage:
        class MyModel(Base, TimestampMixin):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """
    
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
