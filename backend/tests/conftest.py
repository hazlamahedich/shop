"""Pytest configuration and shared fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest
import pytest_asyncio
import asyncio
from datetime import timedelta
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, ENUM

import httpx
from httpx import ASGITransport
from fastapi import FastAPI

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# ENVIRONMENT VARIABLES
# =============================================================================

# Set testing environment before any imports
os.environ["IS_TESTING"] = "true"
os.environ["DEBUG"] = "true"
os.environ["REDIS_URL"] = ""  # Disable Redis in tests
os.environ["SECRET_KEY"] = "dev-secret-key-for-testing"
os.environ["FACEBOOK_APP_ID"] = "test_app_id"
os.environ["FACEBOOK_REDIRECT_URI"] = "https://example.com/callback"
os.environ["FACEBOOK_APP_SECRET"] = "test_secret"
os.environ["FACEBOOK_WEBHOOK_VERIFY_TOKEN"] = "test_token"
os.environ["FACEBOOK_ENCRYPTION_KEY"] = (
    "ZWZlbmV0LWdlbmVyYXRlZC1rZXktZm9yLXRlc3Rpbmc="  # Valid Fernet key (base64)
)
os.environ["SHOPIFY_API_SECRET"] = "test_shopify_secret_for_testing"
os.environ["FACEBOOK_APP_SECRET"] = "test_facebook_app_secret"
os.environ["FACEBOOK_WEBHOOK_VERIFY_TOKEN"] = "test_token"

# Sprint Change 2026-02-13: Mock store for testing without real Shopify
os.environ["MOCK_STORE_ENABLED"] = "true"


# =============================================================================
# DATABASE ENGINE & FIXTURES
# =============================================================================

# Database connection string for testing - use environment variable or default
# IMPORTANT: Tests now use shop_test database (separate from shop_dev)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://developer:developer@localhost:5432/shop_test"
)

# =============================================================================
# SAFETY CHECK: Warn if running tests on development database
# =============================================================================

if "shop_dev" in TEST_DATABASE_URL:
    print("\n" + "=" * 80)
    print("⚠️  WARNING: RUNNING TESTS ON DEVELOPMENT DATABASE  ⚠️")
    print("=" * 80)
    print(f"Test database URL: {TEST_DATABASE_URL}")
    print("\nThis will DELETE ALL DATA in your development database!")
    print("Tests should use a separate test database (shop_test).")
    print("\nTo fix this:")
    print(
        "  export TEST_DATABASE_URL='postgresql+asyncpg://developer:developer@localhost:5432/shop_test'"
    )
    print("\nWaiting 5 seconds before continuing...")
    print("=" * 80 + "\n")
    import time

    time.sleep(5)

# Create async engine for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,  # Use NullPool for tests - no connection pooling needed
    future=True,
    connect_args={
        "prepared_statement_cache_size": 0,  # Disable statement cache to avoid OID issues
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


# =============================================================================
# MODELS IMPORT
# =============================================================================

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
import app.models.faq  # Story 1.11: FAQ model


# =============================================================================
# FIXTURE: Database Setup (Session Scope, Autouse)
# =============================================================================


async def _setup_enums():
    """Internal async helper to set up ENUM types."""
    from sqlalchemy import text

    async with test_engine.begin() as conn:
        enums = [
            ("merchant_status", "('pending', 'active', 'failed')"),
            ("personality_type", "('friendly', 'professional', 'enthusiastic')"),
            ("llm_provider", "('ollama', 'openai', 'anthropic', 'gemini', 'glm')"),
            ("facebook_status", "('pending', 'active', 'error')"),
            ("shopify_status", "('pending', 'active', 'error')"),
            ("conversation_status", "('with', 'handoff', 'closed')"),
            ("message_sender", "('customer', 'bot', 'merchant')"),
            ("message_type", "('text', 'attachment', 'postback')"),
            ("verification_platform", "('facebook', 'shopify')"),
            ("test_type", "('status_check', 'test_webhook', 'resubscribe')"),
            ("verification_status", "('pending', 'success', 'failed')"),
            (
                "datatier",
                "('voluntary', 'operational', 'anonymized')",
            ),  # Story 6-4: Data tier separation
            ("consent_type", "('conversation', 'marketing', 'analytics')"),  # Consent types
            ("deletion_trigger", "('manual', 'auto')"),  # Story 6-5: Deletion trigger type
            (
                "deletion_request_type",
                "('manual', 'gdpr_formal', 'ccpa_request')",
            ),  # Story 6-6: GDPR request type
        ]
        for enum_name, enum_values in enums:
            try:
                await conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM {enum_values};"))
            except Exception:
                pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up clean test database with fresh schema for entire test session.

    This fixture runs ONCE per test session (before any function-scoped fixtures).
    It handles:
    1. Setting environment variables (done above)
    2. Creating custom PostgreSQL ENUM types

    Using synchronous wrapper to avoid scope mismatch with pytest-asyncio.
    """
    asyncio.run(_setup_enums())


# =============================================================================
# FIXTURE: Database Reset Helper (Function Scope)
# =============================================================================


async def _reset_database():
    """Internal helper to reset database tables and sequences.

    This is called by async_session before each test.
    """
    from sqlalchemy import text

    async with test_engine.begin() as conn:
        # Check if deletion_audit_log table exists before truncating
        result = await conn.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'deletion_audit_log')"
            )
        )
        if result.scalar():
            await conn.execute(text("TRUNCATE TABLE deletion_audit_log CASCADE;"))

        # Truncate tables in correct order (child tables first, then parents)
        await conn.execute(text("TRUNCATE TABLE conversations CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE messages CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE orders CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE merchants CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE tutorials CASCADE;"))

        # Reset sequences
        await conn.execute(text("SELECT setval('merchants_id_seq', 1, false);"))
        await conn.execute(text("SELECT setval('tutorials_id_seq', 1, false);"))
        print(f"DEBUG: Database reset completed")


# =============================================================================
# FIXTURE: Async Session (Function Scope)
# =============================================================================


@pytest.fixture(scope="function")
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for testing with auto-reset.

    This fixture:
    1. Resets database before each test
    2. Creates a fresh async session
    3. Yields session for use
    4. Closes session after test

    The database reset happens automatically before each test.
    """
    # Reset database BEFORE creating session
    await _reset_database()

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        await session.close()


# Alias for backward compatibility with existing tests
db_session = async_session


# =============================================================================
# FIXTURE: Test Merchant (Function Scope)
# =============================================================================


@pytest.fixture(scope="function")
async def test_merchant(async_session: AsyncSession):
    """Create a test merchant for integration tests.

    Returns:
        Merchant instance with test data
    """
    from app.models.merchant import Merchant

    merchant = Merchant(
        merchant_key="test-merchant-key",
        platform="messenger",
        email="test@example.com",
        status="active",
    )
    async_session.add(merchant)
    await async_session.commit()
    await async_session.refresh(merchant)
    return merchant.id  # Return merchant_id (int) for test compatibility


# =============================================================================
# FIXTURE: Async HTTP Client (Function Scope)
# =============================================================================


@pytest.fixture(scope="function")
async def async_client(async_session):
    """Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to call the app directly without a server.
    Reuses the async_session fixture when both are used in tests.
    """
    from app.main import app
    from app.core.database import get_db

    # Override get_db dependency to use the test's async_session
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


# Alias for backward compatibility
@pytest.fixture(scope="function")
async def client(async_session):
    """Alias for async_client for backward compatibility.

    Many existing test files use 'client' instead of 'async_client'.
    This fixture provides backward compatibility.
    """
    from app.main import app
    from app.core.database import get_db

    # Override get_db dependency to use the test's async_session
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as http_client:
            yield http_client
    finally:
        # Clean up override
        app.dependency_overrides.clear()


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================


def auth_headers(merchant_id: int) -> dict[str, str]:
    """Generate authentication headers with JWT token for testing.

    Creates a valid JWT token for the given merchant_id and returns
    headers with Bearer token in Authorization header.

    Story 4-12: Auth middleware supports Bearer token for API tests.

    Args:
        merchant_id: Merchant ID to create token for

    Returns:
        Dict with Authorization header containing Bearer token
    """
    from app.core.auth import create_jwt
    import uuid

    # Create JWT token with unique session ID
    session_id = str(uuid.uuid4())
    token = create_jwt(merchant_id=merchant_id, session_id=session_id)

    # Return headers with Bearer token (Story 4-12: middleware supports this)
    return {"Authorization": f"Bearer {token}"}
