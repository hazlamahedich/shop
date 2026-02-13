"""Pytest configuration for app-level tests.

Ensures environment variables are set before any imports.
"""

import os
from typing import AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Import ALL models to ensure they're registered with Base.metadata
# This must happen before Base.metadata.create_all() is called
import app.models.merchant
import app.models.tutorial
import app.models.onboarding
import app.models.facebook_integration
import app.models.shopify_integration
import app.models.llm_configuration
import app.models.conversation
import app.models.message
import app.models.deployment_log
import app.models.webhook_verification_log
import app.models.faq

# Create shared test engine for all fixtures to use
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker

_shared_test_engine = None
_shared_session_factory = None

def get_shared_test_engine():
    """Get or create shared test engine for app-level tests."""
    global _shared_test_engine
    if _shared_test_engine is None:
        TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev")
        _shared_test_engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            poolclass=NullPool,
            future=True,
            connect_args={
                "prepared_statement_cache_size": 0,
                "statement_cache_size": 0,
            },
        )
    return _shared_test_engine

def get_shared_session_factory():
    """Get or create shared session factory."""
    global _shared_session_factory
    if _shared_session_factory is None:
        from app.core.database import Base

        _shared_session_factory = async_sessionmaker(
            bind=get_shared_test_engine(),
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
            class_=AsyncSession,
        )
    return _shared_session_factory


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

# Sprint Change 2026-02-13: Mock store for testing without real Shopify
os.environ.setdefault("MOCK_STORE_ENABLED", "true")


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
async def _setup_app_database():
    """Setup and reset database for app-level tests."""
    from sqlalchemy import text

    engine = get_shared_test_engine()

    async with engine.begin() as conn:
        # Truncate tables to ensure clean state
        await conn.execute(text("TRUNCATE TABLE merchants CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE tutorials CASCADE;"))

        # Reset sequences
        await conn.execute(text("SELECT setval('merchants_id_seq', 1, false);"))
        await conn.execute(text("SELECT setval('tutorials_id_seq', 1, false);"))

        # Create foreign key constraints with CASCADE explicitly
        # (SQLAlchemy's ondelete doesn't always create the FK constraint)
        try:
            await conn.execute(text("""
                ALTER TABLE tutorials
                DROP CONSTRAINT IF EXISTS tutorials_merchant_id_fkey;
            """))
        except Exception:
            pass  # Ignore if doesn't exist

        try:
            await conn.execute(text("""
                ALTER TABLE tutorials
                ADD CONSTRAINT tutorials_merchant_id_fkey
                FOREIGN KEY (merchant_id)
                REFERENCES merchants(id)
                ON DELETE CASCADE;
            """))
        except Exception as e:
            print(f"FK constraint setup error: {e}")


@pytest.fixture(scope="function")
async def db_session(_setup_app_database) -> AsyncGenerator:
    """Create a database session for testing using shared engine.

    Reuses the PostgreSQL test database for JSONB support.
    """
    print("DEBUG: app/db_session fixture called")

    TestingSessionLocal = get_shared_session_factory()

    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator:
    """Alias for db_session for consistency using shared engine."""
    print("DEBUG: app/async_session fixture called")

    TestingSessionLocal = get_shared_session_factory()

    async with TestingSessionLocal() as session:
        yield session


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


# =============================================================================
# SPRINT CHANGE 2026-02-13: Store Provider Fixtures
# =============================================================================

@pytest.fixture(scope="function")
async def merchant_no_store(db_session: AsyncSession):
    """Create a test merchant WITHOUT an e-commerce store connected.

    Sprint Change 2026-02-13: For testing no-store scenarios.

    Args:
        db_session: Database session

    Returns:
        Merchant instance with store_provider='none'
    """
    from app.models.merchant import Merchant

    merchant = Merchant(
        id=10,
        merchant_key="test_merchant_no_store",
        platform="facebook",
        # Sprint Change 2026-02-13: Explicit no-store state
        store_provider="none",
        facebook_page_id="test_facebook_page_123",
    )

    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    return merchant


@pytest.fixture(scope="function")
async def merchant_with_shopify(db_session: AsyncSession):
    """Create a test merchant WITH Shopify store connected.

    Sprint Change 2026-02-13: For testing Shopify integration scenarios.

    Args:
        db_session: Database session

    Returns:
        Merchant instance with store_provider='shopify'
    """
    from app.models.merchant import Merchant

    merchant = Merchant(
        id=20,
        merchant_key="test_merchant_shopify",
        platform="facebook",
        # Sprint Change 2026-02-13: Shopify connected state
        store_provider="shopify",
        shopify_domain="test-store.myshopify.com",
        shopify_access_token="test_token_encrypted",
        facebook_page_id="test_facebook_page_456",
    )

    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    return merchant


@pytest.fixture(scope="function")
async def async_client(async_session):
    """Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to call the app directly without a server.
    Overrides get_db dependency to use the test's async_session.
    """
    import httpx
    from httpx import ASGITransport
    from app.main import app
    from app.core.database import get_db

    # Override get_db dependency to use test's async_session
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            yield client
    finally:
        # Clean up override
        app.dependency_overrides.clear()
