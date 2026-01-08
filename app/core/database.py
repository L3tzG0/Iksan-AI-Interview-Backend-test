"""
Database module for SQLAlchemy async engine and session management.

This module provides:
- AsyncEngine creation with connection pooling
- AsyncSession factory for database operations
- get_db() dependency for FastAPI injection
- Base declarative class for ORM models

Usage:
    @router.get("/example")
    async def example_endpoint(
        db: Annotated[AsyncSession, Depends(get_db)]
    ):
        result = await db.execute(select(User))
        return result.scalars().all()
"""
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.core.config import settings


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    
    All models should inherit from this class to ensure they are
    registered with the metadata and can be used with Alembic migrations.
    """
    pass


# Global engine instance - initialized during app lifespan
_engine: AsyncEngine | None = None
_async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async SQLAlchemy engine.
    
    Uses connection pooling with settings from config for production use.
    For testing or single-use scenarios, NullPool can be used.
    
    Returns:
        AsyncEngine: The SQLAlchemy async engine instance
    
    Raises:
        ValueError: If DATABASE_URL is not configured
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    if not settings.DATABASE_URL:
        raise ValueError(
            "DATABASE_URL is not configured. Please set it in your .env file. "
            "Format: postgresql+asyncpg://user:password@host:port/database"
        )
    
    _engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,  # Verify connections before use
        echo=settings.DEBUG,  # Log SQL queries in debug mode
    )
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.
    
    The factory creates sessions with expire_on_commit=False to prevent
    lazy loading errors after commits in FastAPI request handlers.
    
    Returns:
        async_sessionmaker: Factory for creating AsyncSession instances
    """
    global _async_session_factory
    
    if _async_session_factory is not None:
        return _async_session_factory
    
    engine = get_engine()
    _async_session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,  # Prevents lazy loading errors after commit
        autoflush=False,  # Manual flush control for better performance
    )
    
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    
    Yields a session that auto-commits on success and auto-rollbacks
    on exception. The session is properly closed in the finally block.
    
    Yields:
        AsyncSession: Database session for the current request
    
    Example:
        @router.get("/users")
        async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions outside of FastAPI requests.
    
    Useful for background workers, scripts, and testing scenarios
    where FastAPI dependency injection is not available.
    
    Yields:
        AsyncSession: Database session with auto commit/rollback
    
    Example:
        async with get_db_context() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database connection during application startup.
    
    This function should be called in the FastAPI lifespan context
    to ensure the engine and session factory are ready before handling requests.
    """
    get_engine()
    get_session_factory()


async def close_db() -> None:
    """
    Close the database engine during application shutdown.
    
    Properly disposes of the connection pool and releases all connections.
    """
    global _engine, _async_session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
