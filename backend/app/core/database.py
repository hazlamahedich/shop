"""Database connection and session management.

Provides async SQLAlchemy integration with PostgreSQL.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# Create async engine
engine = create_async_engine(
    settings()["DATABASE_URL"],
    echo=settings()["DATABASE_ECHO"],
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


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
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize database connection.

    Creates all tables. In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
