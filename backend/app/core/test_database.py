"""Tests for database connection and session management."""

import pytest

from app.core.database import engine, async_session, get_db, Base


class TestDatabase:
    """Test database configuration and sessions."""

    @pytest.mark.asyncio
    async def test_engine_exists(self):
        """Test that database engine is created."""
        assert engine is not None

    @pytest.mark.asyncio
    async def test_session_factory_exists(self):
        """Test that async session factory is created."""
        assert async_session is not None

    @pytest.mark.asyncio
    async def test_get_db_generator(self):
        """Test that get_db returns a generator."""
        db_gen = get_db()
        assert hasattr(db_gen, "__aiter__")

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Test creating a database session."""
        async with async_session() as session:
            assert session is not None
            # Session should be usable for queries
            # (actual queries will fail without real database)

    def test_base_exists(self):
        """Test that Base class exists for ORM models."""
        assert Base is not None
        assert hasattr(Base, "metadata")

    @pytest.mark.asyncio
    async def test_session_is_async(self):
        """Test that session is truly async."""
        async with async_session() as session:
            # Check session has async methods
            assert hasattr(session, "execute")
            assert hasattr(session, "commit")
            assert hasattr(session, "rollback")


class TestDatabaseIntegration:
    """Integration tests that require database."""

    @pytest.mark.asyncio
    async def test_connection_pool_configured(self):
        """Test that connection pool is configured."""
        assert engine.pool is not None
        assert engine.pool.size() == 10  # Default pool size

    @pytest.mark.asyncio
    async def test_session_expiration_config(self):
        """Test that session expiration is disabled."""
        async with async_session() as session:
            # expire_on_commit should be False for async
            assert session.expire_on_commit is False
