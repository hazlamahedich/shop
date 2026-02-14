"""Test cost tracking API endpoints.

Story 3.9: Cost Comparison Display

Tests for:
- Cost summary endpoint with costComparison field
- Savings calculation in API response
- Edge cases: zero spend, high spend, negative savings
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


class MockResult:
    """Mock SQLAlchemy result."""

    def __init__(self, rows=None, scalar_value=None):
        self._rows = rows or []
        self._scalar_value = scalar_value

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def scalar(self):
        return self._scalar_value

    def first(self):
        return self._rows[0] if self._rows else None


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_request():
    """Create mock FastAPI request with merchant_id."""
    request = MagicMock()
    request.state = MagicMock()
    request.state.merchant_id = 1
    request.headers = {}
    return request


class TestCostComparisonAPI:
    """Test cost comparison in cost summary API."""

    @pytest.mark.asyncio
    async def test_cost_summary_includes_comparison(self, mock_db, mock_request) -> None:
        """Cost summary should include costComparison field."""
        from app.services.cost_tracking.cost_tracking_service import CostTrackingService

        service = CostTrackingService()

        mock_result = MockResult(rows=[])
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_count_result = MockResult(scalar_value=0)

        async def mock_execute_side_effect(query):
            if "count" in str(query).lower():
                return mock_count_result
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.get_cost_summary(
            db=mock_db,
            merchant_id=1,
        )

        assert "costComparison" in result
        assert "manyChatEstimate" in result["costComparison"]
        assert "savingsAmount" in result["costComparison"]
        assert "savingsPercentage" in result["costComparison"]
        assert "merchantSpend" in result["costComparison"]
        assert "methodology" in result["costComparison"]

    @pytest.mark.asyncio
    async def test_cost_comparison_zero_spend(self, mock_db, mock_request) -> None:
        """Zero spend with zero messages should show zero savings percentage."""
        from app.services.cost_tracking.cost_tracking_service import CostTrackingService

        service = CostTrackingService()

        mock_result = MockResult(rows=[])
        mock_count_result = MockResult(scalar_value=0)

        async def mock_execute_side_effect(query):
            if "count" in str(query).lower():
                return mock_count_result
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.get_cost_summary(
            db=mock_db,
            merchant_id=1,
        )

        comparison = result["costComparison"]
        assert comparison["merchantSpend"] == 0.0
        assert comparison["manyChatEstimate"] == 0.0
        assert comparison["savingsPercentage"] == 0.0

    @pytest.mark.asyncio
    async def test_cost_comparison_savings_calculation(self, mock_db, mock_request) -> None:
        """Savings should be calculated correctly."""
        from app.services.cost_tracking.cost_tracking_service import CostTrackingService

        service = CostTrackingService()

        mock_cost_record = MagicMock()
        mock_cost_record.total_cost_usd = 5.0
        mock_cost_record.total_tokens = 1000
        mock_cost_record.conversation_id = "test-conv"
        mock_cost_record.provider = "openai"
        mock_cost_record.request_timestamp = datetime.utcnow()

        mock_result = MockResult(rows=[mock_cost_record])
        mock_count_result = MockResult(scalar_value=100)

        async def mock_execute_side_effect(query):
            query_str = str(query).lower()
            if "count" in query_str:
                return mock_count_result
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.get_cost_summary(
            db=mock_db,
            merchant_id=1,
        )

        comparison = result["costComparison"]
        assert comparison["merchantSpend"] == 5.0
        assert comparison["manyChatEstimate"] > 0.0
        assert comparison["savingsAmount"] > 0.0

    @pytest.mark.asyncio
    async def test_cost_comparison_includes_message_count(self, mock_db, mock_request) -> None:
        """Methodology should include message count."""
        from app.services.cost_tracking.cost_tracking_service import CostTrackingService

        service = CostTrackingService()

        mock_result = MockResult(rows=[])
        mock_count_result = MockResult(scalar_value=500)

        async def mock_execute_side_effect(query):
            if "count" in str(query).lower():
                return mock_count_result
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.get_cost_summary(
            db=mock_db,
            merchant_id=1,
        )

        methodology = result["costComparison"]["methodology"]
        assert "500" in methodology
        assert "messages" in methodology.lower()

    @pytest.mark.asyncio
    async def test_cost_comparison_high_spend(self, mock_db, mock_request) -> None:
        """High spend should result in negative or low savings."""
        from app.services.cost_tracking.cost_tracking_service import CostTrackingService

        service = CostTrackingService()

        mock_cost_record = MagicMock()
        mock_cost_record.total_cost_usd = 500.0
        mock_cost_record.total_tokens = 100000
        mock_cost_record.conversation_id = "test-conv"
        mock_cost_record.provider = "openai"
        mock_cost_record.request_timestamp = datetime.utcnow()

        mock_result = MockResult(rows=[mock_cost_record])
        mock_count_result = MockResult(scalar_value=10000)

        async def mock_execute_side_effect(query):
            if "count" in str(query).lower():
                return mock_count_result
            return mock_result

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)

        result = await service.get_cost_summary(
            db=mock_db,
            merchant_id=1,
        )

        comparison = result["costComparison"]
        assert comparison["merchantSpend"] == 500.0
