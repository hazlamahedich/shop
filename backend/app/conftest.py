"""Pytest configuration for app-level tests.

Ensures environment variables are set before any imports.
"""

import os
import sys
from typing import AsyncGenerator
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

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
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        },
    )

    # Create session factory
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
    )

    # List of custom enum types
    enum_types = [
        "message_sender",
        "message_type",
        "conversation_status",
        "shopify_status",
        "facebook_status",
        "llm_provider",
        "merchant_status",
        "verification_platform",
        "test_type",
        "verification_status",
    ]

    # Clean up and recreate schema in a single transaction
    async with test_engine.begin() as conn:
        # Drop tables manually in reverse dependency order (children before parents)
        # Using DROP TABLE ... CASCADE to handle foreign key constraints
        for table in [
            "webhook_verification_logs",
            "messages",
            "llm_configurations",
            "facebook_integrations",
            "shopify_integrations",
            "deployment_logs",
            "onboarding_checklists",
            "conversations",
            "merchants",
        ]:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        # Now drop all custom enum types (they may block table drops)
        for enum_type in enum_types:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;"))

        # Recreate enum types (required before creating tables)
        # merchant_status enum
        await conn.execute(text("""
            CREATE TYPE merchant_status AS ENUM (
                'pending', 'active', 'failed'
            );
        """))

        # llm_provider enum
        await conn.execute(text("""
            CREATE TYPE llm_provider AS ENUM (
                'ollama', 'openai', 'anthropic', 'gemini', 'glm'
            );
        """))

        # facebook_status enum
        await conn.execute(text("""
            CREATE TYPE facebook_status AS ENUM (
                'pending', 'active', 'error'
            );
        """))

        # shopify_status enum
        await conn.execute(text("""
            CREATE TYPE shopify_status AS ENUM (
                'pending', 'active', 'error'
            );
        """))

        # conversation_status enum
        await conn.execute(text("""
            CREATE TYPE conversation_status AS ENUM (
                'active', 'handoff', 'closed'
            );
        """))

        # message_sender enum
        await conn.execute(text("""
            CREATE TYPE message_sender AS ENUM (
                'customer', 'bot'
            );
        """))

        # message_type enum
        await conn.execute(text("""
            CREATE TYPE message_type AS ENUM (
                'text', 'attachment', 'postback'
            );
        """))

        # verification_platform enum
        await conn.execute(text("""
            CREATE TYPE verification_platform AS ENUM (
                'facebook', 'shopify'
            );
        """))

        # test_type enum
        await conn.execute(text("""
            CREATE TYPE test_type AS ENUM (
                'status_check', 'test_webhook', 'resubscribe'
            );
        """))

        # verification_status enum
        await conn.execute(text("""
            CREATE TYPE verification_status AS ENUM (
                'pending', 'success', 'failed'
            );
        """))

        # Create all tables fresh
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
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        },
    )

    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
        class_=AsyncSession,
    )

    # List of custom enum types
    enum_types = [
        "message_sender",
        "message_type",
        "conversation_status",
        "shopify_status",
        "facebook_status",
        "llm_provider",
        "merchant_status",
        "verification_platform",
        "test_type",
        "verification_status",
    ]

    # Clean up and recreate schema in a single transaction
    async with test_engine.begin() as conn:
        # Drop tables manually in reverse dependency order (children before parents)
        # Using DROP TABLE ... CASCADE to handle foreign key constraints
        for table in [
            "webhook_verification_logs",
            "messages",
            "llm_configurations",
            "facebook_integrations",
            "shopify_integrations",
            "deployment_logs",
            "onboarding_checklists",
            "conversations",
            "merchants",
        ]:
            await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))

        # Now drop all custom enum types (they may block table drops)
        for enum_type in enum_types:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;"))

        # Recreate enum types (required before creating tables)
        # merchant_status enum
        await conn.execute(text("""
            CREATE TYPE merchant_status AS ENUM (
                'pending', 'active', 'failed'
            );
        """))

        # llm_provider enum
        await conn.execute(text("""
            CREATE TYPE llm_provider AS ENUM (
                'ollama', 'openai', 'anthropic', 'gemini', 'glm'
            );
        """))

        # facebook_status enum
        await conn.execute(text("""
            CREATE TYPE facebook_status AS ENUM (
                'pending', 'active', 'error'
            );
        """))

        # shopify_status enum
        await conn.execute(text("""
            CREATE TYPE shopify_status AS ENUM (
                'pending', 'active', 'error'
            );
        """))

        # conversation_status enum
        await conn.execute(text("""
            CREATE TYPE conversation_status AS ENUM (
                'active', 'handoff', 'closed'
            );
        """))

        # message_sender enum
        await conn.execute(text("""
            CREATE TYPE message_sender AS ENUM (
                'customer', 'bot'
            );
        """))

        # message_type enum
        await conn.execute(text("""
            CREATE TYPE message_type AS ENUM (
                'text', 'attachment', 'postback'
            );
        """))

        # verification_platform enum
        await conn.execute(text("""
            CREATE TYPE verification_platform AS ENUM (
                'facebook', 'shopify'
            );
        """))

        # test_type enum
        await conn.execute(text("""
            CREATE TYPE test_type AS ENUM (
                'status_check', 'test_webhook', 'resubscribe'
            );
        """))

        # verification_status enum
        await conn.execute(text("""
            CREATE TYPE verification_status AS ENUM (
                'pending', 'success', 'failed'
            );
        """))

        # Create all tables fresh
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
