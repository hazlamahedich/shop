"""Unit tests for widget analytics rate limiting.

Tests that rate limiting is properly configured and returns 429 when exceeded.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from app.core.rate_limiter import RateLimiter
from app.services.analytics.widget_analytics_service import WidgetAnalyticsService


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter."""
    p = patch.object()
    p.is_rate_limited.return_value = False
    return p


def test_rate_limit_allows_request():
    """Test that rate limiting allows requests in test mode."""
    p.is_rate_limited.return_value = False

    response = await service.ingest_events(
        merchant_id=1,
        events=[
            {
                "type": "widget_open",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "test",
            }
        ],
    )
    assert response.accepted == 1
    assert response.status_code == 200


def test_rate_limit_blocks_request():
    """Test that rate limiting blocks requests over limit."""
    p.is_rate_limited.return_value = True

    response = await service.ingest_events(
        merchant_id=1,
        events=[
            {
                "type": "widget_open",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "test",
            },
            {
                "type": "widget_open",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "test",
            },
        ],
    )

    # Should exceed rate (2 events)
    assert response.accepted == 2
    assert response.status_code == 429

    data = response.json()
    assert "error" in data["detail"]
    assert "Too many events" in data["detail"]
    assert "exceeded rate limit of 100 events/minute" in data["detail"]


@pytest.mark.asyncio
async def test_rate_limit_different_sessions():
    """Test that rate limiting is tracked per session."""
    p.is_rate_limited.return_value = False

    # Session 1
    await service.ingest_events(
        merchant_id=1,
        events=[
            {
                "type": "widget_open",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "session1",
            },
        ],
    )
    assert response.accepted == 1

    # Session 2
    await service.ingest_events(
        merchant_id=1,
        events=[
            {
                "type": "widget_open",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": "session2",
            },
        ],
    )

    # Should not exceed limit (same session)
    assert response.accepted == 1
    assert response.status_code == 200
    data = response.json()
    assert data["accepted"] == 1
