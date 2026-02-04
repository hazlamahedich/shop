"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

import httpx
from httpx import ASGITransport
from fastapi import FastAPI


# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Set testing environment before any imports
os.environ["IS_TESTING"] = "true"
os.environ["DEBUG"] = "true"  # Allow development settings in tests
os.environ["SECRET_KEY"] = "dev-secret-key-for-testing"
os.environ["FACEBOOK_APP_ID"] = "test_app_id"
os.environ["FACEBOOK_REDIRECT_URI"] = "https://example.com/callback"
os.environ["FACEBOOK_APP_SECRET"] = "test_secret"
os.environ["FACEBOOK_WEBHOOK_VERIFY_TOKEN"] = "test_token"
os.environ["FACEBOOK_ENCRYPTION_KEY"] = "ZWZlbmV0LWdlbmVyYXRlZC1rZXktZm9yLXRlc3Rpbmc="  # Valid Fernet key (base64)
os.environ["SHOPIFY_API_SECRET"] = "test_shopify_secret_for_testing"  # Shopify webhook secret
os.environ["FACEBOOK_APP_SECRET"] = "test_facebook_app_secret"  # Facebook app secret for webhook verification
os.environ["FACEBOOK_WEBHOOK_VERIFY_TOKEN"] = "test_token"  # Facebook webhook verification token


# Import all models to ensure they're registered with Base.metadata
# This must happen before Base.metadata.create_all() is called
import app.models.merchant
import app.models.onboarding
import app.models.facebook_integration
import app.models.shopify_integration
import app.models.llm_configuration
import app.models.conversation
import app.models.message
import app.models.deployment_log
import app.models.webhook_verification_log


@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    """Ensure IS_TESTING and DEBUG are set for all tests."""
    monkeypatch.setenv("IS_TESTING", "true")
    monkeypatch.setenv("DEBUG", "true")


# Database connection string for testing - use environment variable or default
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://developer:developer@localhost:5432/shop_dev"
)

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Use NullPool for tests - no connection pooling needed
    future=True,
    connect_args={
        "prepared_statement_cache_size": 0,  # Disable statement cache to avoid OID issues when types are recreated
        "statement_cache_size": 0,
    },
)

# Create async session factory
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
)


@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for testing.

    This fixture creates a fresh async session for each test function.
    Tables are dropped and recreated before each test for complete isolation.
    """
    from app.core.database import Base

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
        # First, drop all custom enum types (they may block table drops)
        for enum_type in enum_types:
            await conn.execute(text(f"DROP TYPE IF EXISTS {enum_type} CASCADE;"))

        # Drop all tables using metadata (handles foreign keys correctly)
        await conn.run_sync(Base.metadata.drop_all)

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

    # Create session
    async with TestingSessionLocal() as session:
        yield session

    # Cleanup after test
    await session.close()


# Alias for backward compatibility with existing tests
db_session = async_session


@pytest.fixture(scope="function")
async def async_client(async_session):
    """Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to call the app directly without a server.
    Overrides get_db dependency to use the test's async_session.
    """
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


# Note: pytest-asyncio handles event loop management automatically
# No custom event_loop fixture needed
