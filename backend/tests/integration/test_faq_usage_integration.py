"""API integration tests for FAQ Usage endpoint (Story 10-10)."""

import pytest
from httpx import AsyncClient,from sqlalchemy.ext.asyncio import AsyncSession,from app.core.database import get_db
from app.models.faq import Faq
from app.models.faq_interaction_log import FAQInteractionLog


@pytest.mark.asyncio
class TestFaqUsageIntegration:
    """Integration tests for FAQ Usage API with database."""

    @pytest.fixture
    async def db_session():
        """Create a database session for testing."""
        async for session in get_db():
            yield session

    @pytest.fixture
    async def sample_faqs(db_session: AsyncSession):
        """Create sample FAQs for testing."""
        faqs = [
            Faq(
                id=1,
                merchant_id=1,
                question="What are your hours?",
                answer="We are open 9-5.",
                keywords=["hours", "open", "time"],
                icon="clock",
            ),
            Faq(
                id=2,
                merchant_id=1,
                question="How do I return items?",
                answer="You can return within 30 days.",
                keywords=["return", "refund"],
                icon="package",
            ),
            Faq(
                id=3,
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
        return faqs

    @pytest.fixture
    async def sample_interaction_logs(db_session: AsyncSession, sample_faqs):
        """Create sample interaction logs for testing."""
        logs = [
            FAQInteractionLog(faq_id=1, action="click", created_at="2026-03-01 10:00:00"),
            FAQInteractionLog(faq_id=1, action="click", created_at="2026-03-02 11:00:00"),
            FAQInteractionLog(faq_id=1, action="click", created_at="2026-03-03 12:00:00"),
            FAQInteractionLog(faq_id=2, action="click", created_at="2026-03-01 10:00:00"),
            FAQInteractionLog(faq_id=2, action="click", created_at="2026-03-02 11:00:00"),
        ]
        for log in logs:
            db_session.add(log)
        await db_session.commit()
        return logs

    @pytest.mark.asyncio
    async def test_get_faq_usage_with_data(db_session: AsyncSession, sample_interaction_logs):
        """Test that FAQ usage returns correct data from database."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
                headers={"X-Merchant-Id": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "faqs" in data
            assert "summary" in data

    @pytest.mark.asyncio
    async def test_get_faq_usage_empty_database(db_session: AsyncSession):
        """Test that empty database returns empty state."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
                headers={"X-Merchant-Id": "999"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["faqs"] == []
            assert data["summary"]["totalClicks"] == 0

    @pytest.mark.asyncio
    async def test_csv_export_with_data(db_session: AsyncSession, sample_interaction_logs):
        """Test that CSV export returns correct data."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage/export",
                params={"days": 30},
                headers={"X-Merchant-Id": "1"},
            )

            assert response.status_code == 200
            assert "text/csv" in response.headers["content-type"]
            content = response.text
            assert "FAQ Question" in content
            assert "Clicks" in content

    @pytest.mark.asyncio
    async def test_faq_usage_merchant_isolation(db_session: AsyncSession, sample_faqs):
        """Test that merchants can only see their own FAQ data."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/analytics/faq-usage",
                    params={"days": 30},
                    headers={"X-Merchant-Id": "2"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["faqs"] == [] or all(faq["id"] not in [f["id"] for f in sample_faqs] for faq in data["faqs"])

    @pytest.mark.asyncio
    async def test_faq_usage_click_count_accuracy(db_session: AsyncSession, sample_interaction_logs):
        """Test that click counts are accurate."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30},
                headers={"X-Merchant-Id": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            faq_1 = next((f for f in data["faqs"] if f["id"] == 1), None)
            if faq_1:
                assert faq_1["clickCount"] == 3

    @pytest.mark.asyncio
    async def test_faq_usage_period_filter(db_session: AsyncSession, sample_interaction_logs):
        """Test that period filter works correctly."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            for days in [7, 14, 30]:
                response = await client.get(
                    "/api/v1/analytics/faq-usage",
                    params={"days": days},
                    headers={"X-Merchant-Id": "1"},
                )

                assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_faq_usage_marks_unused(db_session: AsyncSession, sample_faqs):
        """Test that FAQs with no clicks are marked as unused."""
        async with AsyncClient(app="testserver", base_url="http://test") as client:
            response = await client.get(
                "/api/v1/analytics/faq-usage",
                params={"days": 30, "include_unused": True},
                headers={"X-Merchant-Id": "1"},
            )

            assert response.status_code == 200
            data = response.json()
            unused_faqs = [f for f in data["faqs"] if f.get("isUnused")]
            for faq in unused_faqs:
                assert faq["clickCount"] == 0
