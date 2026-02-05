"""Tests for SessionService.

Tests session persistence, activity tracking, returning shopper
detection, and voluntary data clearing.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import redis

from app.services.consent import ConsentService, ConsentStatus
from app.services.session.session_service import SessionService


@pytest.fixture
def mock_redis() -> redis.Redis:
    """Create mock Redis client for testing."""
    client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
    yield client
    # Cleanup test data
    client.flushdb()


@pytest.mark.asyncio
async def test_activity_tracking(mock_redis: redis.Redis) -> None:
    """Test activity timestamp tracking."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_activity"

    await service.update_activity(psid)

    last_activity = await service.get_last_activity(psid)
    assert last_activity is not None
    # Should be within last 5 seconds
    assert (datetime.now(timezone.utc) - last_activity).total_seconds() < 5


@pytest.mark.asyncio
async def test_returning_shopper_detection(mock_redis: redis.Redis) -> None:
    """Test detection of returning shoppers."""
    service = SessionService(redis_client=mock_redis)

    # New shopper - no cart or consent
    is_returning = await service.is_returning_shopper("new_psid")
    assert is_returning is False

    # Add cart and consent
    psid = "test_psid_returning"
    await service.consent_service.record_consent(psid, consent_granted=True)
    # Mock cart exists
    service.redis.setex(f"cart:{psid}", 86400, '{"items": [], "subtotal": 0}')

    # Now is returning
    is_returning = await service.is_returning_shopper(psid)
    assert is_returning is True


@pytest.mark.asyncio
async def test_get_cart_item_count(mock_redis: redis.Redis) -> None:
    """Test getting cart item count."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_count"

    # No cart - count is 0
    count = await service.get_cart_item_count(psid)
    assert count == 0

    # Create cart with items
    import json
    cart_data = {
        "items": [
            {"variant_id": "var1", "quantity": 2},
            {"variant_id": "var2", "quantity": 1}
        ],
        "subtotal": 100
    }
    service.redis.setex(f"cart:{psid}", 86400, json.dumps(cart_data))

    # Count returns number of items (not quantity)
    count = await service.get_cart_item_count(psid)
    assert count == 2


@pytest.mark.asyncio
async def test_session_clear_voluntary_only(mock_redis: redis.Redis) -> None:
    """Test that clear_session only clears voluntary data."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_clear"

    # Setup: Cart, consent, activity
    await service.consent_service.record_consent(psid, consent_granted=True)
    service.redis.setex(f"cart:{psid}", 86400, '{"items": []}')
    await service.update_activity(psid)

    # Mock operational data (order refs) - this should NOT be cleared
    service.redis.set(f"order_ref:{psid}", "order_123")

    # Clear session
    await service.clear_session(psid)

    # Voluntary data cleared
    assert service.redis.exists(f"cart:{psid}") == 0
    assert await service.consent_service.get_consent(psid) == ConsentStatus.PENDING
    assert await service.get_last_activity(psid) is None

    # Operational data preserved
    assert service.redis.exists(f"order_ref:{psid}") == 1
    assert service.redis.get(f"order_ref:{psid}") == "order_123"


@pytest.mark.asyncio
async def test_returning_shopper_without_consent(mock_redis: redis.Redis) -> None:
    """Test returning shopper without consent is not detected."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_no_consent"

    # Add cart but no consent
    service.redis.setex(f"cart:{psid}", 86400, '{"items": []}')

    # Not returning (no consent)
    is_returning = await service.is_returning_shopper(psid)
    assert is_returning is False


@pytest.mark.asyncio
async def test_returning_shopper_without_cart(mock_redis: redis.Redis) -> None:
    """Test returning shopper without cart is not detected."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_no_cart"

    # Add consent but no cart
    await service.consent_service.record_consent(psid, consent_granted=True)

    # Not returning (no cart)
    is_returning = await service.is_returning_shopper(psid)
    assert is_returning is False


@pytest.mark.asyncio
async def test_session_clear_clears_context(mock_redis: redis.Redis) -> None:
    """Test that clear_session also clears conversation context."""
    service = SessionService(redis_client=mock_redis)
    psid = "test_psid_context"

    # Setup context
    service.redis.set(f"context:{psid}", '{"last_intent": "product_search"}')

    # Clear session
    await service.clear_session(psid)

    # Context should be cleared
    assert service.redis.exists(f"context:{psid}") == 0


@pytest.mark.asyncio
async def test_activity_ttl_hours_constant(mock_redis: redis.Redis) -> None:
    """Test activity TTL constant is set correctly."""
    assert SessionService.ACTIVITY_TTL_HOURS == 24


@pytest.mark.asyncio
async def test_multiple_shoppers_activity(mock_redis: redis.Redis) -> None:
    """Test activity tracking for multiple shoppers."""
    service = SessionService(redis_client=mock_redis)

    # Update activity for multiple shoppers
    await service.update_activity("user1")
    await service.update_activity("user2")
    await service.update_activity("user3")

    # Each should have their own activity tracked
    assert await service.get_last_activity("user1") is not None
    assert await service.get_last_activity("user2") is not None
    assert await service.get_last_activity("user3") is not None
