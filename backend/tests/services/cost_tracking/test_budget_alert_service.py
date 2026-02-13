"""Test budget alert service including bot pause/resume.

Story 3.8: Budget Alert Notifications

Tests for:
- Alert creation at 80% and 100% thresholds
- No duplicate alerts in same billing period
- Alert marked as read
- Merchant isolation
- Bot pause/resume logic
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.cost_tracking.budget_alert_service import BudgetAlertService
from app.models.budget_alert import BudgetAlert
from app.models.merchant import Merchant


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key: str) -> str | None:
        return self.data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self.data[key] = value
        return True


class MockResult:
    """Mock SQLAlchemy result with scalars().first() chain."""

    def __init__(self, first_value=None):
        self._first_value = first_value

    def scalars(self):
        return self

    def first(self):
        return self._first_value


@pytest.fixture
def mock_db():
    """Create mock database session with configurable execute result."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db._mock_first_value = None

    async def mock_execute(query):
        return MockResult(db._mock_first_value)

    db.execute = AsyncMock(side_effect=mock_execute)

    def set_merchant(merchant):
        db._mock_first_value = merchant

    db.set_mock_merchant = set_merchant
    return db


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    return MockRedis()


@pytest.fixture
def budget_alert_service(mock_db, mock_redis):
    """Create budget alert service with mocks."""
    return BudgetAlertService(db=mock_db, redis_client=mock_redis)


class TestBotPauseResume:
    """Test bot pause/resume functionality."""

    async def test_get_bot_paused_state_from_redis(
        self,
        budget_alert_service,
        mock_redis,
    ) -> None:
        """Test getting paused state from Redis cache."""
        mock_redis.data["merchant:1:bot_paused"] = "true"

        is_paused, reason = await budget_alert_service.get_bot_paused_state(1)

        assert is_paused is True

    async def test_get_bot_active_state_from_redis(
        self,
        budget_alert_service,
        mock_redis,
    ) -> None:
        """Test getting active state from Redis cache."""
        mock_redis.data["merchant:1:bot_paused"] = "false"

        is_paused, reason = await budget_alert_service.get_bot_paused_state(1)

        assert is_paused is False

    async def test_set_bot_paused_state_dual_write(
        self,
        budget_alert_service,
        mock_db,
        mock_redis,
    ) -> None:
        """Test setting paused state with dual-write."""
        mock_merchant = MagicMock()
        mock_merchant.config = {}
        mock_db.set_mock_merchant(mock_merchant)

        result = await budget_alert_service.set_bot_paused_state(
            merchant_id=1,
            paused=True,
            reason="Budget exceeded",
        )

        assert result is True
        assert mock_redis.data["merchant:1:bot_paused"] == "true"
        assert mock_merchant.config["is_bot_paused"] is True
        assert mock_merchant.config["pause_reason"] == "Budget exceeded"

    async def test_set_bot_resumed_state_clears_pause(
        self,
        budget_alert_service,
        mock_db,
        mock_redis,
    ) -> None:
        """Test resuming bot clears pause state."""
        mock_merchant = MagicMock()
        mock_merchant.config = {"is_bot_paused": True, "pause_reason": "Budget exceeded"}
        mock_db.set_mock_merchant(mock_merchant)

        result = await budget_alert_service.set_bot_paused_state(
            merchant_id=1,
            paused=False,
            reason=None,
        )

        assert result is True
        assert mock_redis.data["merchant:1:bot_paused"] == "false"

    async def test_resume_bot_success(
        self,
        budget_alert_service,
        mock_db,
        mock_redis,
    ) -> None:
        """Test resuming bot via resume_bot method."""
        mock_redis.data["merchant:1:bot_paused"] = "true"
        mock_merchant = MagicMock()
        mock_merchant.config = {"is_bot_paused": True}
        mock_db.set_mock_merchant(mock_merchant)

        success, message = await budget_alert_service.resume_bot(1)

        assert success is True
        assert "successfully" in message.lower()

    async def test_resume_bot_already_active(
        self,
        budget_alert_service,
        mock_redis,
    ) -> None:
        """Test resuming bot when already active."""
        mock_redis.data["merchant:1:bot_paused"] = "false"

        success, message = await budget_alert_service.resume_bot(1)

        assert success is True
        assert "already active" in message.lower()


class TestAlertCreation:
    """Test alert creation functionality."""

    async def test_create_alert_at_80_percent(
        self,
        budget_alert_service,
        mock_db,
    ) -> None:
        """Test alert created at 80% threshold."""
        mock_merchant = MagicMock()
        mock_merchant.config = {}
        mock_db.set_mock_merchant(mock_merchant)

        alert = await budget_alert_service.create_alert_if_needed(
            merchant_id=1,
            threshold=80,
            budget_cap=Decimal("100.00"),
        )

        assert alert is not None
        assert alert.threshold == 80

    async def test_create_alert_at_100_percent(
        self,
        budget_alert_service,
        mock_db,
    ) -> None:
        """Test alert created at 100% threshold."""
        mock_merchant = MagicMock()
        mock_merchant.config = {}
        mock_db.set_mock_merchant(mock_merchant)

        alert = await budget_alert_service.create_alert_if_needed(
            merchant_id=1,
            threshold=100,
            budget_cap=Decimal("100.00"),
        )

        assert alert is not None
        assert alert.threshold == 100

    async def test_no_duplicate_alerts_same_month(
        self,
        budget_alert_service,
        mock_db,
    ) -> None:
        """Test no duplicate alerts in same billing period."""
        current_month = datetime.utcnow().strftime("%Y-%m")
        mock_merchant = MagicMock()
        mock_merchant.config = {
            "last_alert_threshold": 80,
            "last_alert_month": current_month,
        }
        mock_db.set_mock_merchant(mock_merchant)

        alert = await budget_alert_service.create_alert_if_needed(
            merchant_id=1,
            threshold=80,
            budget_cap=Decimal("100.00"),
        )

        assert alert is None

    async def test_alert_created_different_month(
        self,
        budget_alert_service,
        mock_db,
    ) -> None:
        """Test alert created in different month."""
        mock_merchant = MagicMock()
        mock_merchant.config = {
            "last_alert_threshold": 80,
            "last_alert_month": "2025-01",
        }
        mock_db.set_mock_merchant(mock_merchant)

        alert = await budget_alert_service.create_alert_if_needed(
            merchant_id=1,
            threshold=80,
            budget_cap=Decimal("100.00"),
        )

        assert alert is not None


class TestCheckAndHandleBudgetState:
    """Test check_and_handle_budget_state method."""

    async def test_null_budget_returns_ok(
        self,
        budget_alert_service,
    ) -> None:
        """Test null budget returns ok with no message."""
        status, message = await budget_alert_service.check_and_handle_budget_state(
            merchant_id=1,
            monthly_spend=Decimal("999.99"),
            budget_cap=None,
        )

        assert status == "ok"
        assert message is None

    async def test_zero_budget_returns_exceeded_with_message(
        self,
        budget_alert_service,
        mock_db,
        mock_redis,
    ) -> None:
        """Test $0 budget returns exceeded with message."""
        mock_merchant = MagicMock()
        mock_merchant.config = {}
        mock_db.set_mock_merchant(mock_merchant)

        status, message = await budget_alert_service.check_and_handle_budget_state(
            merchant_id=1,
            monthly_spend=Decimal("0.00"),
            budget_cap=Decimal("0"),
        )

        assert status == "exceeded"
        assert message == BudgetAlertService.ZERO_BUDGET_MESSAGE

    async def test_exceeded_sets_pause_state(
        self,
        budget_alert_service,
        mock_db,
        mock_redis,
    ) -> None:
        """Test exceeded status sets pause state."""
        mock_merchant = MagicMock()
        mock_merchant.config = {}
        mock_db.set_mock_merchant(mock_merchant)

        status, message = await budget_alert_service.check_and_handle_budget_state(
            merchant_id=1,
            monthly_spend=Decimal("100.00"),
            budget_cap=Decimal("100.00"),
        )

        assert status == "exceeded"
        assert message == BudgetAlertService.PAUSED_BOT_MESSAGE
