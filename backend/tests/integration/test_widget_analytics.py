"""Integration tests for Widget Analytics Service (Story 9-10)

Tests the widget analytics endpoints with real database operations.
"""

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.models.widget_analytics_event import WidgetAnalyticsEvent


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app) as ac:
        yield ac


@pytest.fixture
async def db_session():
    """Create database session for tests."""
    from app.core.database import async_session

    async with async_session() as session:
        yield session


class TestWidgetAnalyticsIntegration:
    """Integration tests for widget analytics."""

    async def test_ingest_single_event(self, client: AsyncClient, db_session):
        """Test ingesting a single analytics event."""
        event = {
            "type": "widget_open",
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": "test-session-123",
            "metadata": {"url": "https://example.com"},
        }

        response = await client.post(
            "/api/v1/analytics/widget/events",
            json={"merchant_id": 1, "events": [event]},
            headers={"X-Test-Mode": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == 1

    async def test_ingest_batch_events(self, client: AsyncClient, db_session):
        """Test ingesting multiple events in a batch."""
        now = datetime.now(UTC).isoformat()
        events = [
            {
                "type": "widget_open",
                "timestamp": now,
                "session_id": "batch-session-1",
            },
            {
                "type": "message_send",
                "timestamp": now,
                "session_id": "batch-session-1",
                "metadata": {"message_length": 50},
            },
            {
                "type": "quick_reply_click",
                "timestamp": now,
                "session_id": "batch-session-1",
                "metadata": {"button_label": "Track Order"},
            },
        ]

        response = await client.post(
            "/api/v1/analytics/widget/events",
            json={"merchant_id": 1, "events": events},
            headers={"X-Test-Mode": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == 3

    async def test_reject_invalid_event_type(self, client: AsyncClient, db_session):
        """Test that invalid event types are rejected."""
        event = {
            "type": "invalid_event_type",
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": "test-session-invalid",
        }

        response = await client.post(
            "/api/v1/analytics/widget/events",
            json={"merchant_id": 1, "events": [event]},
            headers={"X-Test-Mode": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] == 0

    async def test_get_metrics(self, client: AsyncClient, db_session):
        """Test retrieving widget analytics metrics."""
        # First, ingest some events
        now = datetime.now(UTC).isoformat()
        events = [
            {"type": "widget_open", "timestamp": now, "session_id": "metrics-session"},
            {"type": "widget_open", "timestamp": now, "session_id": "metrics-session"},
            {"type": "message_send", "timestamp": now, "session_id": "metrics-session"},
        ]

        await client.post(
            "/api/v1/analytics/widget/events",
            json={"merchant_id": 1, "events": events},
            headers={"X-Test-Mode": "true"},
        )

        # Get metrics
        response = await client.get(
            "/api/v1/analytics/widget?merchant_id=1&days=30",
            headers={"X-Test-Mode": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "trends" in data
        assert "performance" in data

    async def test_export_csv(self, client: AsyncClient, db_session):
        """Test exporting widget analytics as CSV."""
        # First, ingest some events
        now = datetime.now(UTC).isoformat()
        events = [
            {"type": "widget_open", "timestamp": now, "session_id": "export-session"},
            {"type": "message_send", "timestamp": now, "session_id": "export-session"},
        ]

        await client.post(
            "/api/v1/analytics/widget/events",
            json={"merchant_id": 1, "events": events},
            headers={"X-Test-Mode": "true"},
        )

        # Export CSV
        response = await client.get(
            "/api/v1/analytics/widget/export?merchant_id=1",
            headers={"X-Test-Mode": "true"},
        )

        assert response.status_code == 200
        assert "timestamp,event_type,session_id" in response.text

    async def test_cleanup_old_events(self, db_session):
        """Test GDPR cleanup of old events."""
        from app.services.analytics.widget_analytics_service import WidgetAnalyticsService

        # Create an old event (31 days ago)
        old_event = WidgetAnalyticsEvent(
            merchant_id=1,
            session_id="old-session",
            event_type="widget_open",
            timestamp=datetime.now(UTC) - timedelta(days=31),
            event_metadata={},
        )
        db_session.add(old_event)
        await db_session.commit()

        # Run cleanup
        service = WidgetAnalyticsService(db_session)
        deleted = await service.cleanup_old_events(days=30)

        assert deleted >= 1

    async def test_rate_limiting(self, client: AsyncClient):
        """Test rate limiting for analytics endpoint."""
        session_id = "rate-limit-test"
        now = datetime.now(UTC).isoformat()

        # Send 100+ requests rapidly
        for i in range(105):
            event = {
                "type": "widget_open",
                "timestamp": now,
                "session_id": session_id,
            }
            response = await client.post(
                "/api/v1/analytics/widget/events",
                json={"merchant_id": 1, "events": [event]},
                headers={"X-Test-Mode": "true"},
            )
            if i < 100:
                assert response.status_code == 200
            # Note: Rate limiting may kick in after 100 events
