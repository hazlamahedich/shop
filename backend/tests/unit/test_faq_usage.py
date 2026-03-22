"""Unit tests for FAQ usage service (Story 10-10)."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService


class TestGetFaqUsage:
    """Test get_faq_usage method."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock database."""
        return AggregatedAnalyticsService(mock_db)

    def _create_mock_row(self, faq_id, question, click_count, followup_count, is_unused=False):
        """Helper to create a mock database row."""
        row = MagicMock()
        row.id = faq_id
        row.question = question
        row.click_count = click_count
        row.followup_count = followup_count
        row.is_unused = is_unused if is_unused else (click_count == 0)
        return row

    @pytest.mark.asyncio
    async def test_get_faq_usage_returns_data(self, service, mock_db):
        """Test that get_faq_usage returns FAQ usage data."""
        current_rows = [
            self._create_mock_row(1, "What are your hours?", 42, 6),
            self._create_mock_row(2, "How do I return items?", 28, 2),
        ]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result is not None
        assert "faqs" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_get_faq_usage_empty_state(self, service, mock_db):
        """Test that empty state is handled correctly."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result["faqs"] == []
        assert result["summary"]["totalClicks"] == 0

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_period_comparison(self, service, mock_db):
        """Test that period comparison is calculated correctly."""
        current_rows = [self._create_mock_row(1, "Popular FAQ", 50, 5)]
        prev_rows = [self._create_mock_row(1, "Popular FAQ", 40, 4)]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = prev_rows
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert len(result["faqs"]) == 1
        assert result["faqs"][0]["change"]["clickChange"] == 25.0

    @pytest.mark.asyncio
    async def test_get_faq_usage_calculates_conversion_rate(self, service, mock_db):
        """Test that conversion rate is calculated correctly."""
        current_rows = [self._create_mock_row(1, "FAQ 1", 100, 10)]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result["faqs"][0]["conversionRate"] == 10.0

    def test_get_faq_usage_marks_unused_faqs(self, service, mock_db):
        """Test that FAQs with 0 clicks are marked as unused."""
        current_rows = [self._create_mock_row(1, "Unused FAQ", 0, 0)]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []

        result = await service.get_faq_usage(merchant_id=1, days=30, include_unused=True)

        assert result["faqs"][0]["isUnused"] is True

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_custom_days(self, service, mock_db):
        """Test that custom days parameter is respected."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        for days in [7, 14, 30]:
            result = await service.get_faq_usage(merchant_id=1, days=days)
            assert result is not None

    @pytest.mark.asyncio
    async def test_get_faq_usage_includes_change_data(self, service, mock_db):
        """Test that change data is included when available."""
        current_rows = [self._create_mock_row(1, "FAQ with change", 50, 5)]
        prev_rows = [self._create_mock_row(1, "FAQ with change", 40, 4)]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = prev_rows
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result is not None
        assert "change" in result["faqs"][0]
        assert "clickChange" in result["faqs"][0]["change"]

    @pytest.mark.asyncio
    async def test_get_faq_usage_sorts_by_click_count(self, service, mock_db):
        """Test that FAQs are sorted by click count descending."""
        current_rows = [
            self._create_mock_row(1, "Popular FAQ", 100, 10),
            self._create_mock_row(2, "Less Popular", 50, 5),
        ]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        click_counts = [faq["clickCount"] for faq in result["faqs"]]
        assert click_counts == sorted(click_counts, reverse=True)

    @pytest.mark.asyncio
    async def test_get_faq_usage_summary_calculation(self, service, mock_db):
        """Test that summary statistics are calculated correctly."""
        current_rows = [
            self._create_mock_row(1, "FAQ 1", 100, 10),
            self._create_mock_row(2, "FAQ 2", 50, 5),
            self._create_mock_row(3, "Unused", 0, 0),
        ]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result["summary"]["totalClicks"] == 150
        assert result["summary"]["unusedCount"] == 1


class TestFaqUsageEdgeCases:
    """Test edge cases for FAQ usage."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock database."""
        return AggregatedAnalyticsService(mock_db)

    @pytest.mark.asyncio
    async def test_get_faq_usage_handles_database_error(self, service, mock_db):

    @pytest.mark.asyncio
    async def test_get_faq_usage_handles_database_error(self, service, mock_db):
        """Test that database errors are handled gracefully."""
        mock_db.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await service.get_faq_usage(merchant_id=1, days=30)

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_zero_conversion_rate(self, service, mock_db):
        """Test handling of zero conversion rate."""
        current_rows = [
            MagicMock(id=1, question="No conversions", click_count=100, followup_count=0)
        ]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result["faqs"][0]["conversionRate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_large_click_counts(self, service, mock_db):
        """Test handling of large click counts."""
        current_rows = [
            MagicMock(id=1, question="Popular", click_count=1000000, followup_count=50000)
        ]
        mock_current_result = MagicMock()
        mock_current_result.all.return_value = current_rows
        mock_prev_result = MagicMock()
        mock_prev_result.all.return_value = []
        mock_db.execute.side_effect = [mock_current_result, mock_prev_result]

        result = await service.get_faq_usage(merchant_id=1, days=30)

        assert result["faqs"][0]["clickCount"] == 1000000
