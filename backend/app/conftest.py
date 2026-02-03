"""Pytest configuration for app-level tests.

Ensures environment variables are set before any imports.
"""

import os
import sys
from typing import AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Set critical environment variables before any imports
os.environ.setdefault("IS_TESTING", "true")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "dev-secret-key-for-testing")

# Shopify config
os.environ.setdefault("SHOPIFY_API_KEY", "test_api_key")
os.environ.setdefault("SHOPIFY_API_SECRET", "test_secret")
os.environ.setdefault("SHOPIFY_REDIRECT_URI", "https://example.com/api/integrations/shopify/callback")
os.environ.setdefault("SHOPIFY_ENCRYPTION_KEY", "ZWZlbmV0LWdlbmVyYXRlZC1rZXktZm9yLXRlc3Rpbmc=")

# Facebook config
os.environ.setdefault("FACEBOOK_APP_ID", "test_app_id")
os.environ.setdefault("FACEBOOK_REDIRECT_URI", "https://example.com/callback")
os.environ.setdefault("FACEBOOK_APP_SECRET", "test_secret")
os.environ.setdefault("FACEBOOK_WEBHOOK_VERIFY_TOKEN", "test_token")
os.environ.setdefault("FACEBOOK_ENCRYPTION_KEY", "ZWZlbmV0LWdlbmVyYXRlZC1rZXktZm9yLXRlc3Rpbmc=")

# Database config for tests
os.environ.setdefault("TEST_DATABASE_URL", "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev")


# Database fixtures for app-level tests - reuse from tests/conftest
@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator:
    """Create a database session for testing.

    Reuses the PostgreSQL test database for JSONB support.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.database import Base

    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev")

    # Create engine
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True,
    )

    # Create session factory
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
    )

    # Drop and recreate tables for clean state
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create and yield session
    async with TestingSessionLocal() as session:
        yield session

    # Cleanup
    await test_engine.dispose()


# Also provide async_session alias
@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator:
    """Alias for db_session for consistency."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.pool import NullPool
    from app.core.database import Base

    TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev")

    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
        future=True,
    )

    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    await test_engine.dispose()


@pytest.fixture(scope="function")
async def merchant(db_session: AsyncSession):
    """Create a test merchant for foreign key relationships.

    Args:
        db_session: Database session

    Returns:
        Merchant instance with id=1
    """
    from app.models.merchant import Merchant

    merchant = Merchant(
        id=1,
        merchant_key="test_merchant_key",
        platform="facebook"
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    return merchant


@pytest.fixture(scope="function")
async def async_client(async_session):
    """Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to call the app directly without a server.
    """
    import httpx
    from httpx import ASGITransport
    from app.main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
