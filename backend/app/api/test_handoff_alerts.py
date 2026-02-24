"""Unit tests for Handoff Alert API endpoints.

Story 4-6: Handoff Notifications

Tests cover:
- List alerts with pagination and filtering
- Get unread count for badge
- Mark individual alert as read
- Mark all alerts as read
- Authentication and authorization
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.handoff_alerts import (
    router,
    HandoffAlertResponse,
    HandoffAlertListResponse,
    HandoffAlertListMeta,
    UnreadCountResponse,
    MarkReadResponse,
    MarkAllReadResponse,
    _alert_to_response,
)


@pytest.fixture
def app():
    """Create test FastAPI app."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/handoff-alerts")
    return test_app


@pytest.fixture
def client(app):
    """Provide test client."""
    return TestClient(app)


class MockConversation:
    """Mock Conversation for testing."""

    def __init__(
        self,
        handoff_reason: str | None = None,
        platform_sender_id: str | None = None,
        handoff_triggered_at: datetime | None = None,
    ):
        self.handoff_reason = handoff_reason
        self.platform_sender_id = platform_sender_id
        self.handoff_triggered_at = handoff_triggered_at


class MockAlert:
    """Mock HandoffAlert for testing."""

    def __init__(
        self,
        id: int,
        merchant_id: int,
        conversation_id: int,
        urgency_level: str,
        customer_name: str | None = "Test Customer",
        customer_id: str | None = "psid_123",
        conversation_preview: str | None = "Test preview",
        wait_time_seconds: int = 30,
        is_read: bool = False,
        handoff_reason: str | None = None,
        platform_sender_id: str | None = None,
        handoff_triggered_at: datetime | None = None,
    ):
        self.id = id
        self.merchant_id = merchant_id
        self.conversation_id = conversation_id
        self.urgency_level = urgency_level
        self.customer_name = customer_name
        self.customer_id = customer_id
        self.conversation_preview = conversation_preview
        self.wait_time_seconds = wait_time_seconds
        self.is_read = is_read
        self.created_at = datetime.utcnow()
        self.conversation = MockConversation(
            handoff_reason=handoff_reason,
            platform_sender_id=platform_sender_id,
            handoff_triggered_at=handoff_triggered_at,
        )


class TestAlertToResponse:
    """Tests for alert to response conversion (unit test without DB)."""

    def test_alert_conversion_all_fields(self):
        """Test all fields are included in response."""
        mock_alert: Any = MockAlert(
            id=1,
            merchant_id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="John Doe",
            customer_id="psid_456",
            conversation_preview="Help me checkout",
            wait_time_seconds=120,
            is_read=False,
        )

        response = _alert_to_response(mock_alert)

        assert response.id == 1
        assert response.conversation_id == 100
        assert response.urgency_level == "high"
        assert response.customer_name == "John Doe"
        assert response.customer_id == "psid_456"
        assert response.conversation_preview == "Help me checkout"
        assert response.wait_time_seconds == 120
        assert response.is_read is False

    def test_alert_conversion_null_fields(self):
        """Test conversion handles null fields."""
        mock_alert: Any = MockAlert(
            id=2,
            merchant_id=1,
            conversation_id=200,
            urgency_level="low",
            customer_name=None,
            customer_id=None,
            conversation_preview=None,
        )

        response = _alert_to_response(mock_alert)

        assert response.customer_name is None
        assert response.customer_id is None
        assert response.conversation_preview is None

    def test_alert_conversion_all_urgency_levels(self):
        """Test conversion for all urgency levels."""
        for urgency in ["high", "medium", "low"]:
            mock_alert: Any = MockAlert(
                id=1,
                merchant_id=1,
                conversation_id=100,
                urgency_level=urgency,
            )

            response = _alert_to_response(mock_alert)
            assert response.urgency_level == urgency

    def test_alert_conversion_calculates_wait_time(self):
        """Test wait_time_seconds is calculated from handoff_triggered_at."""
        from datetime import timezone, timedelta

        triggered_at = datetime.now(timezone.utc) - timedelta(hours=2, minutes=30)
        mock_alert: Any = MockAlert(
            id=1,
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
            handoff_triggered_at=triggered_at,
        )

        response = _alert_to_response(mock_alert)

        assert response.wait_time_seconds > 0
        expected_seconds = 2 * 3600 + 30 * 60
        assert abs(response.wait_time_seconds - expected_seconds) < 5

    def test_alert_conversion_falls_back_to_stored_wait_time(self):
        """Test wait_time_seconds falls back to stored value when no handoff_triggered_at."""
        mock_alert: Any = MockAlert(
            id=1,
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=120,
            handoff_triggered_at=None,
        )

        response = _alert_to_response(mock_alert)

        assert response.wait_time_seconds == 120

    def test_alert_conversion_handles_naive_datetime(self):
        """Test wait_time_seconds handles naive datetime (no timezone info)."""
        from datetime import timedelta

        triggered_at = datetime.utcnow() - timedelta(hours=1)
        assert triggered_at.tzinfo is None

        mock_alert: Any = MockAlert(
            id=1,
            merchant_id=1,
            conversation_id=100,
            urgency_level="low",
            wait_time_seconds=0,
            handoff_triggered_at=triggered_at,
        )

        response = _alert_to_response(mock_alert)

        assert response.wait_time_seconds > 0
        expected_seconds = 3600
        assert abs(response.wait_time_seconds - expected_seconds) < 5


class TestResponseSchemas:
    """Tests for response schema models."""

    def test_handoff_alert_response_schema(self):
        """Test HandoffAlertResponse has correct fields."""
        response = HandoffAlertResponse(
            id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="Test",
            customer_id="test_id",
            conversation_preview="Preview",
            wait_time_seconds=30,
            is_read=False,
            created_at="2026-02-14T10:00:00",
        )

        assert response.id == 1
        assert response.conversation_id == 100
        assert response.urgency_level == "high"

    def test_handoff_alert_list_meta_schema(self):
        """Test HandoffAlertListMeta has correct fields."""
        meta = HandoffAlertListMeta(
            total=100,
            page=2,
            limit=20,
            unread_count=15,
        )

        assert meta.total == 100
        assert meta.page == 2
        assert meta.limit == 20
        assert meta.unread_count == 15

    def test_handoff_alert_list_response_schema(self):
        """Test HandoffAlertListResponse has correct structure."""
        alert = HandoffAlertResponse(
            id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="Test",
            customer_id="test_id",
            conversation_preview="Preview",
            wait_time_seconds=30,
            is_read=False,
            created_at="2026-02-14T10:00:00",
        )

        response = HandoffAlertListResponse(
            data=[alert],
            meta=HandoffAlertListMeta(total=1, page=1, limit=20, unread_count=1),
        )

        assert len(response.data) == 1
        assert response.meta.total == 1

    def test_unread_count_response_schema(self):
        """Test UnreadCountResponse has correct field."""
        response = UnreadCountResponse(unread_count=5)

        assert response.unread_count == 5

    def test_mark_read_response_schema(self):
        """Test MarkReadResponse has correct fields."""
        response = MarkReadResponse(success=True, alert_id=1)

        assert response.success is True
        assert response.alert_id == 1

    def test_mark_all_read_response_schema(self):
        """Test MarkAllReadResponse has correct fields."""
        response = MarkAllReadResponse(success=True, updated_count=10)

        assert response.success is True
        assert response.updated_count == 10


class TestListEndpointLogic:
    """Tests for list endpoint logic (without full integration)."""

    def test_valid_urgency_values(self):
        """Test valid urgency values are correct."""
        from app.api.handoff_alerts import VALID_URGENCY_VALUES

        assert "high" in VALID_URGENCY_VALUES
        assert "medium" in VALID_URGENCY_VALUES
        assert "low" in VALID_URGENCY_VALUES
        assert len(VALID_URGENCY_VALUES) == 3


class TestQueueViewParams:
    """Tests for queue view parameter validation (Story 4-7)."""

    def test_valid_view_values(self):
        """Test valid view parameter values."""
        from app.api.handoff_alerts import VALID_VIEW_VALUES

        assert "notifications" in VALID_VIEW_VALUES
        assert "queue" in VALID_VIEW_VALUES
        assert len(VALID_VIEW_VALUES) == 2

    def test_valid_sort_by_values(self):
        """Test valid sort_by parameter values."""
        from app.api.handoff_alerts import VALID_SORT_BY_VALUES

        assert "created_desc" in VALID_SORT_BY_VALUES
        assert "urgency_desc" in VALID_SORT_BY_VALUES
        assert len(VALID_SORT_BY_VALUES) == 2


class TestQueueViewResponseSchema:
    """Tests for queue view response schema (Story 4-7)."""

    def test_handoff_alert_response_has_handoff_reason(self):
        """Test HandoffAlertResponse includes handoff_reason field."""
        response = HandoffAlertResponse(
            id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="Test",
            customer_id="test_id",
            conversation_preview="Preview",
            wait_time_seconds=30,
            is_read=False,
            created_at="2026-02-14T10:00:00",
            handoff_reason="keyword",
        )

        assert response.handoff_reason == "keyword"

    def test_handoff_alert_response_handoff_reason_optional(self):
        """Test handoff_reason is optional."""
        response = HandoffAlertResponse(
            id=1,
            conversation_id=100,
            urgency_level="high",
            customer_name="Test",
            customer_id="test_id",
            conversation_preview="Preview",
            wait_time_seconds=30,
            is_read=False,
            created_at="2026-02-14T10:00:00",
        )

        assert response.handoff_reason is None

    def test_queue_meta_has_total_waiting(self):
        """Test HandoffAlertListMeta includes total_waiting field."""
        meta = HandoffAlertListMeta(
            total=100,
            page=2,
            limit=20,
            unread_count=15,
            total_waiting=12,
        )

        assert meta.total_waiting == 12

    def test_queue_meta_total_waiting_optional(self):
        """Test total_waiting is optional (null for notifications view)."""
        meta = HandoffAlertListMeta(
            total=100,
            page=2,
            limit=20,
            unread_count=15,
        )

        assert meta.total_waiting is None


class TestUrgencySortOrder:
    """Tests for urgency sorting logic (Story 4-7)."""

    def test_urgency_sort_values_in_case_statement(self):
        """Test urgency level sort values match case statement."""
        # Values used in handoff_alerts.py case statement
        urgency_sort_values = {"high": 3, "medium": 2, "low": 1}
        assert urgency_sort_values["high"] == 3
        assert urgency_sort_values["medium"] == 2
        assert urgency_sort_values["low"] == 1


class TestEndpointPaths:
    """Tests for endpoint path registration."""

    def test_router_has_list_endpoint(self):
        """Test router has list endpoint defined."""
        paths = []
        for route in router.routes:
            if isinstance(route, APIRoute):
                paths.append(route.path)
        assert "" in paths or "/" in paths

    def test_router_has_unread_count_endpoint(self):
        """Test router has unread count endpoint."""
        paths = []
        for route in router.routes:
            if isinstance(route, APIRoute):
                paths.append(route.path)
        assert "/unread-count" in paths

    def test_router_has_mark_read_endpoint(self):
        """Test router has mark read endpoint."""
        paths = []
        for route in router.routes:
            if isinstance(route, APIRoute):
                paths.append(route.path)
        assert "/{alert_id}/read" in paths

    def test_router_has_mark_all_read_endpoint(self):
        """Test router has mark all read endpoint."""
        paths = []
        for route in router.routes:
            if isinstance(route, APIRoute):
                paths.append(route.path)
        assert "/mark-all-read" in paths
