"""Database connection and session management.

Provides async SQLAlchemy integration with PostgreSQL.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Global variables for lazy initialization
_engine: AsyncEngine | None = None
_async_session: async_sessionmaker[AsyncSession] | None = None


def _ensure_initialized() -> None:
    """Ensure database engine and session factory are initialized."""
    global _engine, _async_session
    if _engine is None:
        _engine = create_async_engine(
            settings()["DATABASE_URL"],
            echo=settings()["DATABASE_ECHO"],
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        _async_session = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


# Module-level accessor that ensures initialization
class _EngineAccessor:
    """Accessor for engine that ensures lazy initialization."""

    def __getattr__(self, name: str):
        _ensure_initialized()
        return getattr(_engine, name)  # type: ignore


class _SessionAccessor:
    """Accessor for session factory that ensures lazy initialization."""

    def __call__(self):  # type: ignore
        _ensure_initialized()
        return _async_session

    def __getattr__(self, name: str):
        _ensure_initialized()
        return getattr(_async_session, name)  # type: ignore


# Create accessor instances
engine = _EngineAccessor()  # type: ignore
async_session = _SessionAccessor()  # type: ignore


def get_engine() -> AsyncEngine:
    """Get the database engine (ensures initialization).

    Returns:
        Async engine instance
    """
    _ensure_initialized()
    return _engine  # type: ignore


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the session factory (ensures initialization).

    Returns:
        Async session factory
    """
    _ensure_initialized()
    return _async_session  # type: ignore


async def get_db() -> AsyncSession:
    """Get database session for dependency injection.

    Yields:
        Async database session

    Example:
        ```python
        @app.get("/users/{user_id}")
        async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        ```
    """
    _ensure_initialized()
    async with _async_session() as session:  # type: ignore
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database connection.

    Creates all tables. In production, use Alembic migrations instead.
    """
    _ensure_initialized()
    async with _engine.begin() as conn:  # type: ignore
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    _ensure_initialized()
    await _engine.dispose()  # type: ignore


async def get_db_context() -> AsyncSession:
    """Get database session for background jobs.

    This is a context manager version for use in background tasks
    that need to manage their own database sessions.

    Yields:
        Async database session
    """
    _ensure_initialized()
    async with _async_session() as session:  # type: ignore
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
