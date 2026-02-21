"""Tests for BudgetMiddleware.

Story 5-10 Task 20: Budget Alert Middleware

Tests budget checking before LLM calls.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.middleware.budget_middleware import (
    BudgetMiddleware,
)


@pytest.fixture
def middleware():
    """Create BudgetMiddleware instance."""
    return BudgetMiddleware()


@pytest.fixture
def mock_db():
    """Create mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_merchant_with_budget():
    """Create mock merchant with budget cap."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.config = {"budget_cap": 100.0}
    return merchant


@pytest.fixture
def mock_merchant_no_budget():
    """Create mock merchant without budget cap."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.config = {}
    return merchant


@pytest.fixture
def mock_merchant_zero_budget():
    """Create mock merchant with zero budget."""
    merchant = MagicMock(spec=Merchant)
    merchant.id = 1
    merchant.config = {"budget_cap": 0}
    return merchant


class TestCheckBudget:
    """Tests for check_budget method."""

    @pytest.mark.asyncio
    async def test_returns_ok_when_no_merchant(
        self,
        middleware,
        mock_db,
    ):
        """Should return OK when merchant not found."""
        with patch.object(middleware, "_get_merchant", return_value=None):
            is_ok, message = await middleware.check_budget(
                db=mock_db,
                merchant_id=999,
            )

        assert is_ok is True
        assert message is None

    @pytest.mark.asyncio
    async def test_returns_ok_when_no_budget_cap(
        self,
        middleware,
        mock_db,
        mock_merchant_no_budget,
    ):
        """Should return OK when no budget cap is set."""
        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_no_budget,
        ):
            is_ok, message = await middleware.check_budget(
                db=mock_db,
                merchant_id=1,
            )

        assert is_ok is True
        assert message is None

    @pytest.mark.asyncio
    async def test_returns_message_when_zero_budget(
        self,
        middleware,
        mock_db,
        mock_merchant_zero_budget,
    ):
        """Should return message when budget is zero."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(False, None))
        mock_budget_service.set_bot_paused_state = AsyncMock()

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_zero_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                is_ok, message = await middleware.check_budget(
                    db=mock_db,
                    merchant_id=1,
                )

        assert is_ok is False
        assert message is not None
        assert "configuring" in message.lower() or "chat" in message.lower()

    @pytest.mark.asyncio
    async def test_returns_message_when_paused(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should return message when bot is paused."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(True, "Budget exceeded"))

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                is_ok, message = await middleware.check_budget(
                    db=mock_db,
                    merchant_id=1,
                )

        assert is_ok is False
        assert message is not None

    @pytest.mark.asyncio
    async def test_returns_ok_when_under_budget(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should return OK when under budget."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(False, None))

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                with patch.object(
                    middleware.cost_service,
                    "get_monthly_spend",
                    return_value=50.0,
                ):
                    is_ok, message = await middleware.check_budget(
                        db=mock_db,
                        merchant_id=1,
                    )

        assert is_ok is True
        assert message is None

    @pytest.mark.asyncio
    async def test_returns_message_when_over_budget(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should return message when over budget."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(False, None))
        mock_budget_service.set_bot_paused_state = AsyncMock()

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                with patch.object(
                    middleware.cost_service,
                    "get_monthly_spend",
                    return_value=150.0,
                ):
                    is_ok, message = await middleware.check_budget(
                        db=mock_db,
                        merchant_id=1,
                    )

        assert is_ok is False
        assert message is not None
        assert "break" in message.lower() or "budget" in message.lower()


class TestGetBudgetStatus:
    """Tests for get_budget_status method."""

    @pytest.mark.asyncio
    async def test_status_no_merchant(
        self,
        middleware,
        mock_db,
    ):
        """Should return status without budget when no merchant."""
        with patch.object(middleware, "_get_merchant", return_value=None):
            status = await middleware.get_budget_status(
                db=mock_db,
                merchant_id=999,
            )

        assert status["has_budget"] is False
        assert status["is_paused"] is False

    @pytest.mark.asyncio
    async def test_status_no_budget_cap(
        self,
        middleware,
        mock_db,
        mock_merchant_no_budget,
    ):
        """Should return status without budget when no cap set."""
        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_no_budget,
        ):
            status = await middleware.get_budget_status(
                db=mock_db,
                merchant_id=1,
            )

        assert status["has_budget"] is False
        assert status["budget_cap"] is None

    @pytest.mark.asyncio
    async def test_status_with_budget(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should return status with budget information."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(False, None))

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                with patch.object(
                    middleware.cost_service,
                    "get_monthly_spend",
                    return_value=50.0,
                ):
                    status = await middleware.get_budget_status(
                        db=mock_db,
                        merchant_id=1,
                    )

        assert status["has_budget"] is True
        assert status["budget_cap"] == 100.0
        assert status["monthly_spend"] == 50.0
        assert status["remaining"] == 50.0
        assert status["is_paused"] is False

    @pytest.mark.asyncio
    async def test_status_when_paused(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should return paused status."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(True, "Budget exceeded"))

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                with patch.object(
                    middleware.cost_service,
                    "get_monthly_spend",
                    return_value=100.0,
                ):
                    status = await middleware.get_budget_status(
                        db=mock_db,
                        merchant_id=1,
                    )

        assert status["is_paused"] is True
        assert status["pause_reason"] == "Budget exceeded"

    @pytest.mark.asyncio
    async def test_status_calculates_percentage(
        self,
        middleware,
        mock_db,
        mock_merchant_with_budget,
    ):
        """Should calculate percentage used."""
        mock_budget_service = AsyncMock()
        mock_budget_service.get_bot_paused_state = AsyncMock(return_value=(False, None))

        with patch.object(
            middleware,
            "_get_merchant",
            return_value=mock_merchant_with_budget,
        ):
            with patch(
                "app.services.conversation.middleware.budget_middleware.BudgetAlertService",
                return_value=mock_budget_service,
            ):
                with patch.object(
                    middleware.cost_service,
                    "get_monthly_spend",
                    return_value=75.0,
                ):
                    status = await middleware.get_budget_status(
                        db=mock_db,
                        merchant_id=1,
                    )

        assert status["percentage_used"] == 75.0


class TestGetBudgetCap:
    """Tests for _get_budget_cap method."""

    def test_returns_none_when_no_config(self, middleware):
        """Should return None when merchant has no config."""
        merchant = MagicMock(spec=Merchant)
        merchant.config = None

        result = middleware._get_budget_cap(merchant)

        assert result is None

    def test_returns_none_when_no_budget_cap(self, middleware):
        """Should return None when config has no budget_cap."""
        merchant = MagicMock(spec=Merchant)
        merchant.config = {"other_setting": "value"}

        result = middleware._get_budget_cap(merchant)

        assert result is None

    def test_returns_decimal_when_budget_cap_set(self, middleware):
        """Should return Decimal when budget_cap is set."""
        merchant = MagicMock(spec=Merchant)
        merchant.config = {"budget_cap": 100.0}

        result = middleware._get_budget_cap(merchant)

        assert result == Decimal("100.0")

    def test_handles_integer_budget(self, middleware):
        """Should handle integer budget values."""
        merchant = MagicMock(spec=Merchant)
        merchant.config = {"budget_cap": 100}

        result = middleware._get_budget_cap(merchant)

        assert result == Decimal("100")
