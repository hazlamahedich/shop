"""Unit tests for AggregatedAnalyticsService.

Story 6-4: Data Tier Separation
Task 7.5: Test analytics aggregation strips PII
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.order import Order
from app.models.llm_conversation_cost import LLMConversationCost
from app.services.analytics.aggregated_analytics_service import AggregatedAnalyticsService
from app.services.privacy.data_tier_service import DataTier


class TestAggregatedAnalyticsService:
    """Test suite for AggregatedAnalyticsService."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> AggregatedAnalyticsService:
        """Create service instance."""
        return AggregatedAnalyticsService(db_session)

    @pytest.mark.asyncio
    async def test_get_tier_distribution_returns_correct_counts(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test tier distribution returns correct counts by tier."""
        merchant_id = 1

        # Create conversations in different tiers
        conv1 = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user1",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        conv2 = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user2",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
        )
        db_session.add_all([conv1, conv2])
        await db_session.commit()

        result = await service.get_tier_distribution(merchant_id)

        assert "conversations" in result
        assert "messages" in result
        assert "orders" in result
        assert "summary" in result

        # Verify conversation tier counts
        assert result["conversations"]["voluntary"] == 1
        assert result["conversations"]["anonymized"] == 1
        assert result["conversations"]["operational"] == 0

    @pytest.mark.asyncio
    async def test_aggregate_conversation_stats_strips_pii(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test that conversation stats aggregation strips all PII.

        Story 6-4 Task 7.5: Verify no customer IDs, emails, or names in output.
        """
        merchant_id = 1

        # Create conversation with PII
        conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user-with-pii@example.com",  # PII
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Create messages
        msg = Message(
            conversation_id=conv.id,
            sender="customer",
            content="Test message",
            message_type="text",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(msg)
        await db_session.commit()

        result = await service.aggregate_conversation_stats(merchant_id, days=30)

        # Verify NO PII in result
        assert "user-with-pii@example.com" not in str(result)
        assert "platform_sender_id" not in str(result)
        assert "customer_email" not in str(result)
        assert "customer_phone" not in str(result)

        # Verify anonymized tier
        assert result["tier"] == DataTier.ANONYMIZED.value

        # Verify aggregated counts (no individual records)
        assert "total" in result["conversations"]
        assert "total" in result["messages"]
        assert isinstance(result["conversations"]["total"], int)
        assert isinstance(result["messages"]["total"], int)

    @pytest.mark.asyncio
    async def test_aggregate_conversation_stats_includes_costs(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test that cost tracking is included in aggregated stats."""
        merchant_id = 1

        # Create cost record
        cost = LLMConversationCost(
            merchant_id=merchant_id,
            conversation_id=1,
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            total_cost_usd=0.15,
            request_timestamp=datetime.now(timezone.utc),
        )
        db_session.add(cost)
        await db_session.commit()

        result = await service.aggregate_conversation_stats(merchant_id, days=30)

        # Verify cost is included (anonymized - no customer ID)
        assert "costs" in result
        assert "totalUsd" in result["costs"]
        assert result["costs"]["totalUsd"] == 0.15

        # Verify no customer association
        assert "conversation_id" not in str(result["costs"])

    @pytest.mark.asyncio
    async def test_get_anonymized_summary_combines_all_stats(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test that anonymized summary combines all statistics."""
        merchant_id = 1

        # Create test data
        conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user1",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        order = Order(
            merchant_id=merchant_id,
            order_number="ORD-123",
            platform_sender_id="user1",
            total=99.99,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(order)
        await db_session.commit()

        result = await service.get_anonymized_summary(merchant_id)

        # Verify all sections present
        assert "tierDistribution" in result
        assert "conversationStats" in result
        assert "orderStats" in result
        assert "generatedAt" in result
        assert "tier" in result

        # Verify tier
        assert result["tier"] == DataTier.ANONYMIZED.value

        # Verify order stats (anonymized - no customer data)
        assert "totalOrders" in result["orderStats"]
        assert "totalRevenue" in result["orderStats"]
        assert result["orderStats"]["totalOrders"] >= 1

        # Verify NO PII
        result_str = str(result)
        assert "user1" not in result_str  # No platform_sender_id
        assert "ORD-123" not in result_str  # No order numbers (could be PII)

    @pytest.mark.asyncio
    async def test_aggregate_conversation_stats_respects_date_range(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test that stats only include data within date range."""
        merchant_id = 1

        # Create recent conversation
        recent_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="recent_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.now(timezone.utc) - timedelta(days=15),
        )
        db_session.add(recent_conv)

        # Create old conversation (outside 30-day range)
        old_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="old_user",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )
        db_session.add(old_conv)
        await db_session.commit()

        result = await service.aggregate_conversation_stats(merchant_id, days=30)

        # Should only include recent conversation
        assert result["conversations"]["total"] == 1

        # Verify period in result
        assert "period" in result
        assert result["period"]["days"] == 30

    @pytest.mark.asyncio
    async def test_get_tier_distribution_empty_merchant(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test tier distribution with no data returns zeros."""
        merchant_id = 999  # Non-existent merchant

        result = await service.get_tier_distribution(merchant_id)

        # Should return zero counts, not error
        assert result["conversations"]["voluntary"] == 0
        assert result["conversations"]["operational"] == 0
        assert result["conversations"]["anonymized"] == 0
        assert result["summary"]["totalVoluntary"] == 0

    @pytest.mark.asyncio
    async def test_aggregate_conversation_stats_no_pii_in_intent_data(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test that intent metadata doesn't leak PII."""
        merchant_id = 1

        conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user-with-sensitive-data",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)
        await db_session.commit()

        # Message with metadata (intent data)
        msg = Message(
            conversation_id=conv.id,
            sender="bot",
            content="Response",
            message_type="text",
            data_tier=DataTier.VOLUNTARY,
            message_metadata={
                "intent": "product_search",
                "confidence": 0.95,
                "channel": "widget",
            },
        )
        db_session.add(msg)
        await db_session.commit()

        result = await service.aggregate_conversation_stats(merchant_id, days=30)

        # Verify no PII leaked through metadata
        result_str = str(result)
        assert "user-with-sensitive-data" not in result_str
        assert "platform_sender_id" not in result_str


class TestTierDistributionEdgeCases:
    """Edge case tests for tier distribution."""

    @pytest.fixture
    def service(self, db_session: AsyncSession) -> AggregatedAnalyticsService:
        """Create service instance."""
        return AggregatedAnalyticsService(db_session)

    @pytest.mark.asyncio
    async def test_tier_distribution_with_only_operational_data(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test distribution when only operational tier exists."""
        merchant_id = 1

        order = Order(
            merchant_id=merchant_id,
            order_number="ORD-001",
            platform_sender_id="user1",
            total=50.00,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(order)
        await db_session.commit()

        result = await service.get_tier_distribution(merchant_id)

        # Should show operational only
        assert result["orders"]["operational"] >= 1
        assert result["orders"]["voluntary"] == 0
        assert result["orders"]["anonymized"] == 0

        # Summary should reflect this
        assert result["summary"]["totalOperational"] >= 1
        assert result["summary"]["totalVoluntary"] == 0

    @pytest.mark.asyncio
    async def test_tier_distribution_with_mixed_tiers(
        self,
        service: AggregatedAnalyticsService,
        db_session: AsyncSession,
    ) -> None:
        """Test distribution with data in all three tiers."""
        merchant_id = 1

        # Voluntary: conversation
        conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user1",
            status="active",
            handoff_status="none",
            data_tier=DataTier.VOLUNTARY,
        )
        db_session.add(conv)

        # Operational: order
        order = Order(
            merchant_id=merchant_id,
            order_number="ORD-002",
            platform_sender_id="user2",
            total=75.00,
            is_test=False,
            data_tier=DataTier.OPERATIONAL,
        )
        db_session.add(order)

        # Anonymized: conversation (after opt-out)
        anon_conv = Conversation(
            merchant_id=merchant_id,
            platform="widget",
            platform_sender_id="user3",
            status="active",
            handoff_status="none",
            data_tier=DataTier.ANONYMIZED,
        )
        db_session.add(anon_conv)

        await db_session.commit()

        result = await service.get_tier_distribution(merchant_id)

        # All tiers should have data
        assert result["conversations"]["voluntary"] >= 1
        assert result["conversations"]["anonymized"] >= 1
        assert result["orders"]["operational"] >= 1

        # Summary should sum all
        assert result["summary"]["totalVoluntary"] >= 1
        assert result["summary"]["totalOperational"] >= 1
        assert result["summary"]["totalAnonymized"] >= 1
