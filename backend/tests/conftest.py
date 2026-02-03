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

    # Drop all tables to ensure clean slate
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Create enum types first (required before creating tables)
    async with test_engine.begin() as conn:
        # Create llm_provider enum
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE llm_provider AS ENUM (
                    'ollama', 'openai', 'anthropic', 'gemini', 'glm'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        # Create llm_status enum
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE llm_status AS ENUM (
                    'pending', 'active', 'error'
                );
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

    # Create tables fresh
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestingSessionLocal() as session:
        yield session

    # No cleanup after test - next test will drop/recreate


# Alias for backward compatibility with existing tests
db_session = async_session


@pytest.fixture(scope="function")
async def async_client(async_session):
    """Create an async HTTP client for testing FastAPI endpoints.

    Uses ASGITransport to call the app directly without a server.
    """
    from app.main import app

    async with httpx.AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


# Note: pytest-asyncio handles event loop management automatically
# No custom event_loop fixture needed
