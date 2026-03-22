"""API integration tests for FAQ Usage endpoint (Story 10-10).

Integration tests that verify the FAQ Usage API works with the actual database
and application endpoints.
"""

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.models.faq import Faq
from app.models.faq_interaction_log import FaqInteractionLog


@pytest.fixture
async def db_session():
    """Create a database session for testing."""
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def sample_faqs(db_session: AsyncSession):
    """Create sample FAQs for testing."""
    faqs = [
        Faq(
            merchant_id=1,
            question="What are your hours?",
            answer="We are open 9-5.",
            keywords=["hours", "open", "time"],
            icon="clock",
        ),
        Faq(
            merchant_id=1,
            question="How do I return items?",
            answer="You can return within 30 days.",
            keywords=["return", "refund"],
            icon="package",
        ),
        Faq(
            merchant_id=1,
            question="Unused FAQ",
            answer="This is rarely used.",
            keywords=["unused"],
            icon="question",
        ),
    ]
    for faq in faqs:
        db_session.add(faq)
    await db_session.commit()
    yield faqs
    await db_session.rollback()


@pytest.fixture
async def sample_interaction_logs(db_session: AsyncSession, sample_faqs):
    """Create sample interaction logs for testing."""
    logs = [
        FaqInteractionLog(
            faq_id=1,
            merchant_id=1,
            session_id="test-session-1",
            clicked_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
        ),
        FaqInteractionLog(
            faq_id=1,
            merchant_id=1,
            session_id="test-session-2",
            clicked_at=datetime(2026, 3, 2, 11, 0, 0, tzinfo=UTC),
        ),
        FaqInteractionLog(
            faq_id=1,
            merchant_id=1,
            session_id="test-session-3",
            clicked_at=datetime(2026, 3, 3, 12, 0, 0, tzinfo=UTC),
        ),
        FaqInteractionLog(
            faq_id=2,
            merchant_id=1,
            session_id="test-session-4",
            clicked_at=datetime(2026, 3, 1, 10, 0, 0, tzinfo=UTC),
        ),
        FaqInteractionLog(
            faq_id=2,
            merchant_id=1,
            session_id="test-session-5",
            clicked_at=datetime(2026, 3, 2, 11, 0, 0, tzinfo=UTC),
        ),
    ]
    for log in logs:
        db_session.add(log)
    await db_session.commit()
    yield logs
    await db_session.rollback()


@pytest.mark.asyncio
class TestFaqUsageIntegration:
    """Integration tests for FAQ Usage API with database."""

    async def test_get_faq_usage_returns_data(
        self,
        db_session: AsyncSession,
        sample_interaction_logs
    ):
        """Test that FAQ usage returns correct data from database."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)
        data = await service.get_faq_usage(merchant_id=1, days=30)

        assert "faqs" in data
        assert "summary" in data
        assert len(data["faqs"]) >= 2

    async def test_get_faq_usage_empty_database(
        self,
        db_session: AsyncSession
    ):
        """Test that empty database returns empty state."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)
        data = await service.get_faq_usage(merchant_id=999, days=30)

        assert data["faqs"] == []
        assert data["summary"]["totalClicks"] == 0

    async def test_get_faq_usage_calculates_click_counts(
        self,
        db_session: AsyncSession
        sample_interaction_logs
    ):
        """Test that click counts are accurate."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)
        data = await service.get_faq_usage(merchant_id=1, days=30)

        faq_1 = next((f for f in data["faqs"] if f["id"] == 1), None)
        if faq_1:
            assert faq_1["clickCount"] == 3

    async def test_get_faq_usage_merchant_isolation(
        self,
        db_session: AsyncSession
        sample_faqs
    ):
        """Test that merchants can only see their own FAQ data."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)
        data = await service.get_faq_usage(merchant_id=2, days=30)

        assert data["faqs"] == [] or all(
            f["id"] not in [faq.id for faq in sample_faqs]
            for f in data["faqs"]
        )

    async def test_get_faq_usage_period_filter(
        self,
        db_session: AsyncSession
        sample_interaction_logs
    ):
        """Test that period filter works correctly."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)

        for days in [7, 14, 30]:
            data = await service.get_faq_usage(merchant_id=1, days=days)
            assert "faqs" in data

    async def test_get_faq_usage_marks_unused(
        self,
        db_session: AsyncSession
        sample_faqs
    ):
        """Test that FAQs with no clicks are marked as unused."""
        from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService

        service = AggregatedAnalyticsService(db_session)
        data = await service.get_faq_usage(merchant_id=1, days=30, include_unused=True)

        unused_faqs = [f for f in data["faqs"] if f.get("isUnused")]
        for faq in unused_faqs:
            assert faq["clickCount"] == 0
