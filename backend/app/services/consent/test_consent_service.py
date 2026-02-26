"""Tests for ConsentService.

Tests consent tracking, opt-in/opt-out flow, and revocation
following TDD principles.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.consent.consent_service import ConsentService, ConsentStatus


@pytest.fixture
def mock_redis() -> Generator[MagicMock, Any, Any]:
    """Create mock Redis client for testing."""
    storage: dict[str, str] = {}

    client = MagicMock()

    async def mock_get(key: str) -> str | None:
        return storage.get(key)

    async def mock_setex(key: str, ttl: int, value: str) -> bool:
        storage[key] = value
        return True

    async def mock_delete(key: str) -> int:
        if key in storage:
            del storage[key]
            return 1
        return 0

    client.get = mock_get
    client.setex = mock_setex
    client.delete = mock_delete
    yield client


@pytest.mark.asyncio
async def test_consent_opt_in(mock_redis: MagicMock) -> None:
    """Test user opts in to cart persistence."""
    service = ConsentService(redis_client=mock_redis)
    psid = "test_psid_opt_in"

    # Record consent
    result = await service.record_consent(psid, consent_granted=True)

    assert result["status"] == ConsentStatus.OPTED_IN
    assert "timestamp" in result
    assert result["psid"] == psid

    # Verify can persist
    can_persist = await service.can_persist_cart(psid)
    assert can_persist is True

    # Verify get_consent returns correct status
    status = await service.get_consent(psid)
    assert status == ConsentStatus.OPTED_IN


@pytest.mark.asyncio
async def test_consent_opt_out(mock_redis: MagicMock) -> None:
    """Test user opts out of cart persistence."""
    service = ConsentService(redis_client=mock_redis)
    psid = "test_psid_opt_out"

    # Record consent
    result = await service.record_consent(psid, consent_granted=False)

    assert result["status"] == ConsentStatus.OPTED_OUT
    assert "timestamp" in result

    # Verify cannot persist
    can_persist = await service.can_persist_cart(psid)
    assert can_persist is False

    # Verify get_consent returns correct status
    status = await service.get_consent(psid)
    assert status == ConsentStatus.OPTED_OUT


@pytest.mark.asyncio
async def test_consent_pending_initially(mock_redis: MagicMock) -> None:
    """Test consent is pending for new users."""
    service = ConsentService(redis_client=mock_redis)

    # New user has no consent
    status = await service.get_consent("new_psid")
    assert status == ConsentStatus.PENDING

    # Cannot persist without consent
    can_persist = await service.can_persist_cart("new_psid")
    assert can_persist is False


@pytest.mark.asyncio
async def test_consent_revoke(mock_redis: MagicMock) -> None:
    """Test consent revocation."""
    service = ConsentService(redis_client=mock_redis)
    psid = "test_psid_revoke"

    # Opt in first
    await service.record_consent(psid, consent_granted=True)
    assert await service.can_persist_cart(psid) is True

    # Revoke consent
    await service.revoke_consent(psid)

    # Verify consent is pending again
    status = await service.get_consent(psid)
    assert status == ConsentStatus.PENDING

    # Cannot persist after revocation
    can_persist = await service.can_persist_cart(psid)
    assert can_persist is False


@pytest.mark.asyncio
async def test_consent_timestamp_is_valid_iso(mock_redis: MagicMock) -> None:
    """Test consent timestamp is valid ISO format."""
    service = ConsentService(redis_client=mock_redis)
    psid = "test_psid_timestamp"

    result = await service.record_consent(psid, consent_granted=True)

    # Verify timestamp is valid ISO format
    timestamp = datetime.fromisoformat(result["timestamp"])
    now = datetime.now(timezone.utc)
    # Should be within last 5 seconds
    assert (now - timestamp).total_seconds() < 5


@pytest.mark.asyncio
async def test_consent_ttl_days_constant(mock_redis: MagicMock) -> None:
    """Test consent TTL constant is set correctly."""
    assert ConsentService.CONSENT_TTL_DAYS == 30


@pytest.mark.asyncio
async def test_consent_overwrite(mock_redis: MagicMock) -> None:
    """Test consent can be overwritten (opt-out to opt-in)."""
    service = ConsentService(redis_client=mock_redis)
    psid = "test_psid_overwrite"

    # First opt out
    result1 = await service.record_consent(psid, consent_granted=False)
    assert result1["status"] == ConsentStatus.OPTED_OUT

    # Then opt in
    result2 = await service.record_consent(psid, consent_granted=True)
    assert result2["status"] == ConsentStatus.OPTED_IN

    # Verify final state is opted in
    status = await service.get_consent(psid)
    assert status == ConsentStatus.OPTED_IN


@pytest.mark.asyncio
async def test_multiple_users_consent(mock_redis: MagicMock) -> None:
    """Test consent tracking works for multiple users."""
    service = ConsentService(redis_client=mock_redis)

    # User 1 opts in
    await service.record_consent("user1", consent_granted=True)
    assert await service.can_persist_cart("user1") is True

    # User 2 opts out
    await service.record_consent("user2", consent_granted=False)
    assert await service.can_persist_cart("user2") is False

    # User 3 pending
    assert await service.get_consent("user3") == ConsentStatus.PENDING
    assert await service.can_persist_cart("user3") is False
