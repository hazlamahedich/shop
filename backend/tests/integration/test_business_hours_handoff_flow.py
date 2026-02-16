"""Integration tests for Business Hours Handoff flow.

Story 4-12: Business Hours Handling

Tests the complete handoff flow with business hours:
- Offline handoff flow with business hours in message
- Online handoff flow (within business hours)
- Notification queuing and delivery at business hours
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.schemas.handoff import UrgencyLevel
from app.services.handoff.business_hours_handoff_service import (
    BusinessHoursHandoffService,
)
from app.services.handoff.notification_service import HandoffNotificationService


@pytest.fixture
def business_hours_config() -> dict:
    """Standard business hours config (9 AM - 5 PM PST, Mon-Fri)."""
    return {
        "timezone": "America/Los_Angeles",
        "hours": [
            {"day": "mon", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            {"day": "tue", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            {"day": "wed", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            {"day": "thu", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            {"day": "fri", "is_open": True, "open_time": "09:00", "close_time": "17:00"},
            {"day": "sat", "is_open": False},
            {"day": "sun", "is_open": False},
        ],
    }


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_merchant(business_hours_config):
    """Create a mock merchant with business hours config."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.email = "test@example.com"
    merchant.business_hours_config = business_hours_config
    return merchant


@pytest.fixture
def mock_conversation():
    """Create a mock conversation."""
    conversation = MagicMock(spec=Conversation)
    conversation.id = 1
    conversation.merchant_id = 1
    conversation.platform_sender_id = "test_psid"
    conversation.handoff_reason = "keyword"
    conversation.conversation_data = {}
    conversation.status = "handoff"
    conversation.handoff_status = "pending"
    return conversation


class TestBusinessHoursHandoffIntegration:
    """Integration tests for business hours handoff flow."""

    @pytest.mark.asyncio
    async def test_offline_handoff_message_includes_business_hours(
        self,
        business_hours_config: dict,
    ) -> None:
        """Handoff message should include business hours when offline."""
        service = BusinessHoursHandoffService()

        saturday_10am_pst_utc = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)
        message = service.build_handoff_message(business_hours_config, saturday_10am_pst_utc)

        assert "offline" in message.lower()
        assert "business hours" in message.lower()
        assert "Expected response:" in message

    @pytest.mark.asyncio
    async def test_online_handoff_message_standard(
        self,
        business_hours_config: dict,
    ) -> None:
        """Handoff message should be standard when within business hours."""
        service = BusinessHoursHandoffService()

        wednesday_10am_pst_utc = datetime(2026, 2, 18, 18, 0, 0, tzinfo=timezone.utc)
        message = service.build_handoff_message(business_hours_config, wednesday_10am_pst_utc)

        assert "offline" not in message.lower()
        assert "12 hours" in message

    @pytest.mark.asyncio
    async def test_no_business_hours_config_uses_standard_message(self) -> None:
        """No business hours config should use standard message."""
        service = BusinessHoursHandoffService()
        message = service.build_handoff_message(None)

        assert "12 hours" in message
        assert "offline" not in message.lower()

    @pytest.mark.asyncio
    async def test_notification_queued_when_offline(
        self,
        mock_db_session: AsyncMock,
        mock_merchant: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """Notifications should be queued when outside business hours."""
        from app.services.handoff.notification_service import HandoffNotificationService

        saturday_10am_utc = datetime(2026, 2, 21, 18, 0, 0, tzinfo=timezone.utc)

        service = HandoffNotificationService(db=mock_db_session, redis=None)

        queued = await service._queue_notification_for_business_hours(
            conversation=mock_conversation,
            urgency=UrgencyLevel.MEDIUM,
            business_hours_config=mock_merchant.business_hours_config,
        )

        assert queued is True
        assert (
            mock_conversation.conversation_data.get("offline_handoff_notification_queued") is True
        )

    @pytest.mark.asyncio
    async def test_notification_sent_immediately_when_online(
        self,
        mock_db_session: AsyncMock,
        mock_merchant: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """Notifications should be sent immediately when within business hours."""
        service = HandoffNotificationService(db=mock_db_session, redis=None)

        with patch(
            "app.services.business_hours.business_hours_service.is_within_business_hours",
            return_value=True,
        ):
            result = await service.send_notifications_with_queue(
                merchant=mock_merchant,
                conversation=mock_conversation,
                urgency=UrgencyLevel.MEDIUM,
                notification_content={
                    "customer_name": "Test Customer",
                    "customer_id": "test_psid",
                },
            )

        assert result["queued"] is False
        assert result["dashboard"] is True

    @pytest.mark.asyncio
    async def test_queue_idempotency_no_duplicates(
        self,
        mock_db_session: AsyncMock,
        mock_merchant: MagicMock,
        mock_conversation: MagicMock,
    ) -> None:
        """Should not queue duplicate notifications."""
        mock_conversation.conversation_data = {"offline_handoff_notification_queued": True}

        service = HandoffNotificationService(db=mock_db_session, redis=None)

        with patch(
            "app.services.business_hours.business_hours_service.is_within_business_hours",
            return_value=False,
        ):
            queued = await service._queue_notification_for_business_hours(
                conversation=mock_conversation,
                urgency=UrgencyLevel.MEDIUM,
                business_hours_config=mock_merchant.business_hours_config,
            )

        assert queued is False


class TestExpectedResponseTimeScenarios:
    """Test various expected response time scenarios."""

    def test_response_time_less_than_one_hour(self) -> None:
        """Response time < 1 hour should show 'less than 1 hour'."""
        service = BusinessHoursHandoffService()

        from_time = datetime(2026, 2, 18, 16, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 16, 30, 0, tzinfo=timezone.utc)

        result = service.format_expected_response_time(from_time, next_hour)
        assert result == "less than 1 hour"

    def test_response_time_about_x_hours(self) -> None:
        """Response time 1-6 hours should show 'about X hours'."""
        service = BusinessHoursHandoffService()

        from_time = datetime(2026, 2, 18, 14, 0, 0, tzinfo=timezone.utc)
        next_hour = datetime(2026, 2, 18, 17, 0, 0, tzinfo=timezone.utc)

        result = service.format_expected_response_time(from_time, next_hour)
        assert result == "about 3 hours"

    def test_response_time_varied_scenarios(self) -> None:
        """Test various response time scenarios match expectations."""
        service = BusinessHoursHandoffService()

        test_cases = [
            (0.5, "less than 1 hour"),
            (1.0, "about 1 hour"),
            (2.5, "about 2 hours"),
            (5.0, "about 5 hours"),
        ]

        for hours, expected_prefix in test_cases:
            from_time = datetime(2026, 2, 18, 10, 0, 0, tzinfo=timezone.utc)
            next_hour = datetime(
                2026, 2, 18, 10 + int(hours), int((hours % 1) * 60), 0, tzinfo=timezone.utc
            )
            result = service.format_expected_response_time(from_time, next_hour)
            assert expected_prefix in result, (
                f"Expected '{expected_prefix}' in '{result}' for {hours} hours"
            )


class TestMerchantWithoutBusinessHours:
    """Test handling of merchants without business hours config."""

    def test_no_config_always_available(self) -> None:
        """Merchant without config should always be available."""
        service = BusinessHoursHandoffService()

        message = service.build_handoff_message(None)
        assert "offline" not in message.lower()

    def test_empty_config_always_available(self) -> None:
        """Merchant with empty config should always be available."""
        service = BusinessHoursHandoffService()

        message = service.build_handoff_message({"timezone": "UTC", "hours": []})
        assert "offline" not in message.lower()

    @pytest.mark.asyncio
    async def test_notification_not_queued_without_config(
        self,
        mock_db_session: AsyncMock,
    ) -> None:
        """Notifications should not be queued without business hours config."""
        merchant = MagicMock(spec=Merchant)
        merchant.id = 1
        merchant.business_hours_config = None

        conversation = MagicMock(spec=Conversation)
        conversation.id = 1
        conversation.merchant_id = 1
        conversation.conversation_data = {}

        service = HandoffNotificationService(db=mock_db_session, redis=None)

        result = await service.send_notifications_with_queue(
            merchant=merchant,
            conversation=conversation,
            urgency=UrgencyLevel.MEDIUM,
            notification_content={
                "customer_name": "Test",
                "customer_id": "test_id",
            },
        )

        assert result["queued"] is False
