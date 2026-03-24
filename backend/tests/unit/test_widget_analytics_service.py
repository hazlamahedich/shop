"""Unit tests for Widget Analytics Service.

Story 9-10: Analytics & Performance Monitoring

Tests for GDPR cleanup, metrics calculation, and CSV export.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.analytics.widget_analytics_service import EVENT_TYPES, WidgetAnalyticsService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Create service instance with mock db."""
    return WidgetAnalyticsService(mock_db)


class TestIngestEvents:
    """Tests for event ingestion."""

    @pytest.mark.asyncio
    async def test_ingest_valid_events(self, service, mock_db):
        """Test ingesting valid events."""
        merchant_id = 1
        events = [
            {
                "type": "widget_open",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
            },
            {
                "type": "message_send",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
            },
            {
                "type": "quick_reply_click",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
            },
        ]

        mock_db.commit = AsyncMock()

        accepted = await service.ingest_events(merchant_id, events)

        assert accepted == 3
        mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_ingest_invalid_event_type(self, service, mock_db):
        """Test that invalid event types are rejected."""
        merchant_id = 1
        events = [
            {
                "type": "invalid_type",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
            },
            {
                "type": "widget_open",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
            },
        ]

        mock_db.commit = AsyncMock()

        accepted = await service.ingest_events(merchant_id, events)

        assert accepted == 1

    @pytest.mark.asyncio
    async def test_ingest_event_with_metadata(self, service, mock_db):
        """Test ingesting event with metadata."""
        merchant_id = 1
        events = [
            {
                "type": "widget_open",
                "timestamp": datetime.now(UTC).isoformat(),
                "session_id": "session-1",
                "metadata": {"load_time_ms": 150, "url": "https://example.com"},
            },
        ]

        mock_db.commit = AsyncMock()

        accepted = await service.ingest_events(merchant_id, events)

        assert accepted == 1


class TestGetMetrics:
    """Tests for metrics retrieval."""

    @pytest.mark.asyncio
    async def test_get_metrics_empty(self, service, mock_db):
        """Test get metrics with no events."""
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_metrics(merchant_id=1, days=30)

        assert result["merchant_id"] == 1
        assert result["period"]["days"] == 30
        assert result["metrics"]["open_rate"] == 0.0
        assert result["metrics"]["message_rate"] == 0.0
        assert result["metrics"]["quick_reply_rate"] == 0.0
        assert result["metrics"]["voice_input_rate"] == 0.0
        assert result["metrics"]["proactive_conversion_rate"] == 0.0
        assert result["metrics"]["carousel_engagement_rate"] == 0.0
        assert result["trends"]["open_rate_change"] == 0.0
        assert result["trends"]["message_rate_change"] == 0.0
        assert result["performance"]["avg_load_time_ms"] == 0.0
        assert result["performance"]["p95_load_time_ms"] == 0.0
        assert result["performance"]["bundle_size_kb"] == 0.0

    @pytest.mark.asyncio
    async def test_get_metrics_with_events(self, service, mock_db):
        """Test get metrics with events."""
        from app.models.widget_analytics_event import WidgetAnalyticsEvent

        now = datetime.now(UTC)
        events = [
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={},
            ),
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="message_send",
                timestamp=now,
                event_metadata={},
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = events
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_metrics(merchant_id=1, days=30)

        assert result["merchant_id"] == 1
        assert result["metrics"]["open_rate"] == 100.0
        assert result["metrics"]["message_rate"] == 100.0


class TestCalculateMetrics:
    """Tests for metrics calculation."""

    def test_calculate_metrics_empty(self, service):
        """Test metrics calculation with no events."""
        result = service._calculate_metrics([])

        assert result["open_rate"] == 0.0
        assert result["message_rate"] == 0.0

    def test_calculate_metrics_with_events(self, service):
        """Test metrics calculation with events."""
        from app.models.widget_analytics_event import WidgetAnalyticsEvent

        now = datetime.now(UTC)
        events = [
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={},
            ),
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="message_send",
                timestamp=now,
                event_metadata={},
            ),
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="quick_reply_click",
                timestamp=now,
                event_metadata={},
            ),
        ]

        result = service._calculate_metrics(events)

        assert result["open_rate"] == 100.0
        assert result["message_rate"] == 100.0
        assert result["quick_reply_rate"] == 100.0


class TestCalcTrends:
    """Tests for trend calculation."""

    def test_calc_trends_positive(self, service):
        """Test trend calculation with positive change."""
        current = {"open_rate": 50.0, "message_rate": 30.0}
        previous = {"open_rate": 40.0, "message_rate": 20.0}

        result = service._calc_trends(current, previous)

        assert result["open_rate_change"] == 25.0
        assert result["message_rate_change"] == 50.0

    def test_calc_trends_negative(self, service):
        """Test trend calculation with negative change."""
        current = {"open_rate": 30.0, "message_rate": 20.0}
        previous = {"open_rate": 60.0, "message_rate": 40.0}

        result = service._calc_trends(current, previous)

        assert result["open_rate_change"] == -50.0
        assert result["message_rate_change"] == -50.0

    def test_calc_trends_no_previous(self, service):
        """Test trend calculation with no previous data."""
        current = {"open_rate": 50.0, "message_rate": 30.0}
        previous = {"open_rate": 0.0, "message_rate": 0.0}

        result = service._calc_trends(current, previous)

        assert result["open_rate_change"] == 0.0
        assert result["message_rate_change"] == 0.0


class TestCleanupOldEvents:
    """Tests for GDPR cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self, service, mock_db):
        """Test GDPR cleanup functionality."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("id1",), ("id2",), ("id3",)]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        deleted = await service.cleanup_old_events(days=30)

        assert deleted == 3
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


class TestExportCsv:
    """Tests for CSV export."""

    @pytest.mark.asyncio
    async def test_export_csv_empty(self, service, mock_db):
        """Test CSV export with no events."""
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        csv_output = await service.export_csv(merchant_id=1)

        assert "timestamp" in csv_output
        assert "event_type" in csv_output
        assert "session_id" in csv_output
        assert "metadata" in csv_output

    @pytest.mark.asyncio
    async def test_export_csv_with_events(self, service, mock_db):
        """Test CSV export with events."""
        from app.models.widget_analytics_event import WidgetAnalyticsEvent

        now = datetime.now(UTC)
        events = [
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={"test": True},
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = events
        mock_db.execute = AsyncMock(return_value=mock_result)

        csv_output = await service.export_csv(merchant_id=1)

        assert "timestamp" in csv_output
        assert "widget_open" in csv_output
        assert "session-1" in csv_output

    @pytest.mark.asyncio
    async def test_export_csv_with_filters(self, service, mock_db):
        """Test CSV export with date filters."""
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        start_date = (datetime.now(UTC) - timedelta(days=7)).isoformat()
        end_date = datetime.now(UTC).isoformat()

        csv_output = await service.export_csv(
            merchant_id=1,
            start_date=start_date,
            end_date=end_date,
            event_type="widget_open",
        )

        assert "timestamp" in csv_output
        mock_db.execute.assert_called_once()


class TestPerformanceMetrics:
    """Tests for performance metric calculations."""

    def test_calc_avg_load_time_empty(self, service):
        """Test average load time with no events."""
        result = service._calc_avg_load_time([])
        assert result == 0.0

    def test_calc_avg_load_time_with_data(self, service):
        """Test average load time calculation."""
        from app.models.widget_analytics_event import WidgetAnalyticsEvent

        now = datetime.now(UTC)
        events = [
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={"load_time_ms": 100},
            ),
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={"load_time_ms": 200},
            ),
        ]

        result = service._calc_avg_load_time(events)
        assert result == 150.0

    def test_calc_p95_load_time_empty(self, service):
        """Test p95 load time with no events."""
        result = service._calc_p95_load_time([])
        assert result == 0.0

    def test_calc_p95_load_time_with_data(self, service):
        """Test p95 load time calculation."""
        from app.models.widget_analytics_event import WidgetAnalyticsEvent

        now = datetime.now(UTC)
        events = [
            WidgetAnalyticsEvent(
                merchant_id=1,
                session_id="session-1",
                event_type="widget_open",
                timestamp=now,
                event_metadata={"load_time_ms": i * 10},
            )
            for i in range(20)
        ]

        result = service._calc_p95_load_time(events)
        assert result > 0


class TestEventTypes:
    """Tests for event type validation."""

    def test_event_types_defined(self):
        """Test that all required event types are defined."""
        assert "widget_open" in EVENT_TYPES
        assert "message_send" in EVENT_TYPES
        assert "quick_reply_click" in EVENT_TYPES
        assert "voice_input" in EVENT_TYPES
        assert "proactive_trigger" in EVENT_TYPES
        assert "carousel_engagement" in EVENT_TYPES
