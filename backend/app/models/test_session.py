"""Unit tests for Session ORM model.

Tests cover:
- Session creation with expiration
- Session validation (not revoked, not expired)
- Session revocation
- Session ID generation
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session


class TestSessionModel:
    """Tests for Session model basic functionality."""

    def test_session_create_returns_instance(self):
        """Creating session should return Session instance."""
        session = Session.create(
            merchant_id=1, token_hash="hash123", hours=24
        )
        assert isinstance(session, Session)
        assert session.merchant_id == 1
        assert session.token_hash == "hash123"

    def test_session_default_values(self):
        """Session should have correct default values."""
        session = Session.create(merchant_id=1, token_hash="hash123")
        assert session.revoked is False
        assert session.created_at is not None
        assert session.expires_at is not None

    def test_session_expiration_time(self):
        """Session expiration should be 24 hours from creation."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)

        time_diff = session.expires_at - session.created_at
        expected_diff = timedelta(hours=24)

        assert time_diff == expected_diff

    def test_session_custom_expiration(self):
        """Custom expiration hours should be respected."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=12)

        time_diff = session.expires_at - session.created_at
        expected_diff = timedelta(hours=12)

        assert time_diff == expected_diff

    def test_session_repr(self):
        """Session repr should contain key info."""
        session = Session.create(merchant_id=42, token_hash="hash123")
        repr_str = repr(session)

        assert "Session" in repr_str
        assert "42" in repr_str
        assert "revoked=False" in repr_str


class TestSessionValidation:
    """Tests for session validation logic."""

    def test_is_valid_new_session(self):
        """New session should be valid."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)
        assert session.is_valid() is True

    def test_is_valid_revoked_session(self):
        """Revoked session should be invalid."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)
        session.revoke()
        assert session.is_valid() is False

    def test_is_valid_expired_session(self):
        """Expired session should be invalid."""
        session = Session.create(
            merchant_id=1, token_hash="hash123", hours=24
        )
        # Set expiration to past
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert session.is_valid() is False

    def test_is_valid_revoked_and_expired(self):
        """Revoked and expired session should be invalid."""
        session = Session.create(
            merchant_id=1, token_hash="hash123", hours=24
        )
        session.revoke()
        session.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert session.is_valid() is False


class TestSessionRevocation:
    """Tests for session revocation (AC 3)."""

    def test_revoke_sets_revoked_true(self):
        """Revoking session should set revoked flag to True."""
        session = Session.create(merchant_id=1, token_hash="hash123")
        session.revoke()
        assert session.revoked is True

    def test_revoke_multiple_times(self):
        """Revoking multiple times should remain revoked."""
        session = Session.create(merchant_id=1, token_hash="hash123")
        session.revoke()
        session.revoke()
        session.revoke()
        assert session.revoked is True


class TestSessionIdGeneration:
    """Tests for session ID generation."""

    def test_generate_session_id_returns_string(self):
        """Generating session ID should return string."""
        session_id = Session.generate_session_id()
        assert isinstance(session_id, str)

    def test_generate_session_id_unique(self):
        """Each generated session ID should be unique."""
        id1 = Session.generate_session_id()
        id2 = Session.generate_session_id()
        assert id1 != id2

    def test_generate_session_id_format(self):
        """Session ID should be UUID format."""
        session_id = Session.generate_session_id()
        # UUID format: 8-4-4-4-12 hex digits
        parts = session_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12


class TestSessionDatabase:
    """Tests for Session database operations."""

    @pytest.mark.asyncio
    async def test_session_saved_to_database(self, db_session: AsyncSession):
        """Session should be saved to database."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        assert session.id is not None

    @pytest.mark.asyncio
    async def test_session_retrieved_by_id(self, db_session: AsyncSession):
        """Session should be retrievable by ID."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        result = await db_session.execute(
            select(Session).where(Session.id == session.id)
        )
        retrieved = result.scalars().first()

        assert retrieved is not None
        assert retrieved.merchant_id == 1
        assert retrieved.token_hash == "hash123"

    @pytest.mark.asyncio
    async def test_session_retrieved_by_merchant_id(
        self, db_session: AsyncSession
    ):
        """Sessions should be retrievable by merchant_id (index test)."""
        session1 = Session.create(merchant_id=1, token_hash="hash1", hours=24)
        session2 = Session.create(merchant_id=1, token_hash="hash2", hours=24)

        db_session.add_all([session1, session2])
        await db_session.commit()

        result = await db_session.execute(
            select(Session).where(Session.merchant_id == 1)
        )
        sessions = result.scalars().all()

        assert len(sessions) == 2

    @pytest.mark.asyncio
    async def test_session_retrieved_by_token_hash(
        self, db_session: AsyncSession
    ):
        """Session should be retrievable by token_hash (index test)."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        result = await db_session.execute(
            select(Session).where(Session.token_hash == "hash123")
        )
        retrieved = result.scalars().first()

        assert retrieved is not None
        assert retrieved.id == session.id

    @pytest.mark.asyncio
    async def test_session_revocation_persists(self, db_session: AsyncSession):
        """Session revocation should persist to database."""
        session = Session.create(merchant_id=1, token_hash="hash123", hours=24)

        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)

        session.revoke()
        await db_session.commit()
        await db_session.refresh(session)

        assert session.revoked is True

        # Verify via query
        result = await db_session.execute(
            select(Session).where(Session.id == session.id)
        )
        retrieved = result.scalars().first()
        assert retrieved.revoked is True
