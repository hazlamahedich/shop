"""Unit tests for ConversationFlowAnalyticsService.

Story 11.12b: Conversation Flow Analytics Dashboard

Tests all 6 analytics methods with real database (integration-style unit tests
since these methods query the DB directly via SQLAlchemy).

Uses fixtures: async_session, test_merchant, test_conversation, seed_conversation_turns.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.conversation_context import ConversationTurn
from app.services.analytics.conversation_flow_analytics_service import (
    ConversationFlowAnalyticsService,
)

# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────


async def _create_conversation_with_turns(
    async_session: AsyncSession,
    merchant_id: int,
    *,
    handoff_status: str = "none",
    conv_status: str = "active",
    turns_data: list[dict] | None = None,
    platform_sender_id: str | None = None,
) -> tuple[Conversation, list[ConversationTurn]]:
    """Create a conversation and associated turns, flush + commit."""
    sender = platform_sender_id or f"conv-{merchant_id}-{datetime.now(UTC).timestamp()}"
    conv = Conversation(
        merchant_id=merchant_id,
        platform="messenger",
        platform_sender_id=sender,
        status=conv_status,
        handoff_status=handoff_status,
    )
    async_session.add(conv)
    await async_session.flush()

    if turns_data is None:
        turns_data = []

    turns: list[ConversationTurn] = []
    for td in turns_data:
        defaults = {
            "conversation_id": conv.id,
            "turn_number": td["turn_number"],
            "user_message": td.get("user_message", f"User message {td['turn_number']}"),
            "bot_response": td.get("bot_response", f"Bot response {td['turn_number']}"),
            "intent_detected": td.get("intent_detected"),
            "sentiment": td.get("sentiment"),
            "context_snapshot": td.get("context_snapshot"),
        }
        turn = ConversationTurn(**defaults)
        async_session.add(turn)
        turns.append(turn)

    await async_session.flush()
    await async_session.commit()
    return conv, turns


def _default_turn(
    turn_number: int,
    *,
    intent: str | None = None,
    sentiment: str | None = None,
    mode: str = "ecommerce",
    has_context_reference: bool = True,
    processing_time_ms: int = 100,
    clarification_state: str = "IDLE",
    clarification_attempt_count: int = 0,
) -> dict:
    """Build a single turn data dict for _create_conversation_with_turns."""
    return {
        "turn_number": turn_number,
        "intent_detected": intent or ("product_search" if turn_number % 2 == 0 else "greeting"),
        "sentiment": sentiment,
        "context_snapshot": {
            "confidence": 0.9,
            "processing_time_ms": processing_time_ms,
            "has_context_reference": has_context_reference,
            "mode": mode,
            "clarification_state": clarification_state,
            "clarification_attempt_count": clarification_attempt_count,
        },
    }


# ────────────────────────────────────────────────────────────────────
# Test: get_conversation_length_distribution (AC1)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-01")
class TestConversationLengthDistribution:
    """AC1: Conversation length distribution."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        """No turns for merchant → has_data=False with message."""
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_conversation_length_distribution(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_data_returns_metrics(self, async_session, test_merchant):
        """Turns exist → returns avg_turns, p90, distribution, by_mode, daily_trend."""
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            turns_data=[_default_turn(i, mode="ecommerce") for i in range(1, 5)],
        )
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            turns_data=[_default_turn(i, mode="general") for i in range(1, 3)],
            platform_sender_id="conv-general-1",
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_conversation_length_distribution(test_merchant, days=7)

        assert result["has_data"] is True
        data = result["data"]
        assert data["total_conversations"] == 2
        assert data["avg_turns"] > 0
        assert data["p90_turns"] > 0
        assert len(data["length_distribution"]) > 0
        assert len(data["by_mode"]) == 2
        assert data["daily_trend"] is not None

    async def test_merchant_isolation(self, async_session, test_merchant):
        """Only sees own merchant's data."""
        from app.models.merchant import Merchant

        other_merchant = Merchant(
            merchant_key="other-merchant-key",
            platform="messenger",
            email="other@example.com",
            status="active",
        )
        async_session.add(other_merchant)
        await async_session.flush()
        await async_session.commit()

        await _create_conversation_with_turns(
            async_session,
            other_merchant.id,
            turns_data=[_default_turn(i) for i in range(1, 4)],
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_conversation_length_distribution(test_merchant, days=7)

        assert result["has_data"] is False


# ────────────────────────────────────────────────────────────────────
# Test: get_clarification_patterns (AC2)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-02")
class TestClarificationPatterns:
    """AC2: Clarification pattern analysis."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        """No clarification turns → has_data=False."""
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_clarification_patterns(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_clarification_data(self, async_session, test_merchant):
        """Turns with non-IDLE clarification_state → returns patterns."""
        turns_data = [
            _default_turn(
                1,
                intent="greeting",
                clarification_state="CLARIFYING",
                clarification_attempt_count=1,
            ),
            _default_turn(
                2,
                intent="clarify",
                clarification_state="CLARIFYING",
                clarification_attempt_count=2,
            ),
            _default_turn(
                3,
                intent="product_search",
                clarification_state="COMPLETE",
                clarification_attempt_count=2,
            ),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_clarification_patterns(test_merchant, days=7)

        assert result["has_data"] is True
        data = result["data"]
        assert data["total_clarifying_conversations"] >= 1
        assert data["avg_clarification_depth"] >= 0
        assert data["clarification_success_rate"] >= 0
        assert "top_sequences" in data

    async def test_all_idle_clarification_returns_no_data(self, async_session, test_merchant):
        """All turns have IDLE clarification_state → has_data=False."""
        turns_data = [_default_turn(i, clarification_state="IDLE") for i in range(1, 4)]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_clarification_patterns(test_merchant, days=7)

        assert result["has_data"] is False


# ────────────────────────────────────────────────────────────────────
# Test: get_friction_points (AC3)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-03")
class TestFrictionPoints:
    """AC3: Friction point detection."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_friction_points(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_data_detects_friction(self, async_session, test_merchant):
        """Closed conv with last intent + repeated intents → friction points."""
        turns_data = [
            _default_turn(1, intent="greeting", processing_time_ms=100),
            _default_turn(2, intent="product_search", processing_time_ms=200),
            _default_turn(3, intent="product_search", processing_time_ms=5000),
            _default_turn(4, intent="order_cancel", processing_time_ms=8000),
        ]
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            conv_status="closed",
            turns_data=turns_data,
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_friction_points(test_merchant, days=7)

        assert result["has_data"] is True
        data = result["data"]
        assert "friction_points" in data
        assert "drop_off_intents" in data
        assert "repeated_intents" in data
        assert data["processing_time_p90_ms"] >= 0
        assert data["total_conversations_analyzed"] == 1

        repeated_intents = [fp for fp in data["friction_points"] if fp["type"] == "repeated_intent"]
        assert len(repeated_intents) > 0
        assert repeated_intents[0]["intent"] == "product_search"

    async def test_repeated_intent_detection(self, async_session, test_merchant):
        """Consecutive same intents → repeated_intent friction."""
        turns_data = [
            _default_turn(1, intent="greeting"),
            _default_turn(2, intent="greeting"),
            _default_turn(3, intent="greeting"),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_friction_points(test_merchant, days=7)

        assert result["has_data"] is True
        repeated = [
            fp for fp in result["data"]["friction_points"] if fp["type"] == "repeated_intent"
        ]
        assert len(repeated) > 0


# ────────────────────────────────────────────────────────────────────
# Test: get_sentiment_distribution_by_stage (AC4)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-04")
class TestSentimentDistributionByStage:
    """AC4: Sentiment distribution across early/mid/late stages."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_sentiment_distribution_by_stage(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_sentiment_data(self, async_session, test_merchant):
        """Turns with sentiment → stages populated."""
        turns_data = [
            _default_turn(1, sentiment="POSITIVE"),
            _default_turn(2, sentiment="POSITIVE"),
            _default_turn(3, sentiment="NEUTRAL"),
            _default_turn(5, sentiment="NEGATIVE"),
            _default_turn(8, sentiment="NEGATIVE"),
            _default_turn(9, sentiment="NEGATIVE"),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_sentiment_distribution_by_stage(test_merchant, days=7)

        assert result["has_data"] is True
        stages = result["data"]["stages"]
        assert "early" in stages
        assert "mid" in stages
        assert "late" in stages
        assert stages["early"].get("POSITIVE", 0) > 0
        assert stages["late"].get("NEGATIVE", 0) > 0

    async def test_no_sentiment_returns_no_data(self, async_session, test_merchant):
        """Turns without sentiment → has_data=False."""
        turns_data = [
            _default_turn(1, sentiment=None),
            _default_turn(2, sentiment=None),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_sentiment_distribution_by_stage(test_merchant, days=7)

        assert result["has_data"] is False


# ────────────────────────────────────────────────────────────────────
# Test: get_handoff_correlation (AC5)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-05")
class TestHandoffCorrelation:
    """AC5: Handoff correlation analysis."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_handoff_data(self, async_session, test_merchant):
        """Handoff conversation with turns → returns triggers and rates."""
        turns_data = [
            _default_turn(1, intent="order_check"),
            _default_turn(2, intent="order_check"),
            _default_turn(3, intent="escalate"),
        ]
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            handoff_status="active",
            turns_data=turns_data,
        )

        # Also create a non-handoff conversation for resolved_length comparison
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            handoff_status="none",
            turns_data=[_default_turn(i) for i in range(1, 3)],
            platform_sender_id="conv-no-handoff-1",
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is True
        data = result["data"]
        assert "top_triggers" in data
        assert "avg_handoff_length" in data
        assert "avg_resolved_length" in data
        assert "handoff_rate_per_intent" in data
        assert data["total_handoff_conversations"] >= 1

    async def test_multiple_handoff_statuses(self, async_session, test_merchant):
        """active, resolved, escalated handoff statuses are all counted."""
        for idx, status_val in enumerate(["active", "resolved", "escalated"]):
            turns_data = [
                _default_turn(1, intent="complaint"),
                _default_turn(2, intent="escalate"),
            ]
            await _create_conversation_with_turns(
                async_session,
                test_merchant,
                handoff_status=status_val,
                turns_data=turns_data,
                platform_sender_id=f"conv-handoff-{idx}",
            )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is True
        assert result["data"]["total_handoff_conversations"] == 3


# ────────────────────────────────────────────────────────────────────
# Test: get_context_utilization (AC6)
# ────────────────────────────────────────────────────────────────────


@pytest.mark.p0
@pytest.mark.test_id("STORY-11-12b-SEQ-06")
class TestContextUtilization:
    """AC6: Context utilization metrics."""

    async def test_empty_data_returns_graceful_no_data(self, async_session, test_merchant):
        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_context_utilization(test_merchant, days=7)

        assert result["has_data"] is False
        assert "message" in result

    async def test_with_data_returns_utilization(self, async_session, test_merchant):
        """Turns with context references → returns utilization_rate and by_mode."""
        turns_data = [
            _default_turn(1, has_context_reference=False, mode="ecommerce"),
            _default_turn(2, has_context_reference=True, mode="ecommerce"),
            _default_turn(3, has_context_reference=True, mode="ecommerce"),
            _default_turn(4, has_context_reference=True, mode="general"),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_context_utilization(test_merchant, days=7)

        assert result["has_data"] is True
        data = result["data"]
        assert data["total_turns"] == 4
        assert data["turns_with_context"] == 3
        assert data["utilization_rate"] == 75.0
        assert len(data["by_mode"]) == 2
        assert data["improvement_opportunities"] >= 0

    async def test_low_utilization_detected(self, async_session, test_merchant):
        """Conversation with <50% context usage → low utilization."""
        turns_data = [
            _default_turn(1, has_context_reference=False),
            _default_turn(2, has_context_reference=False),
            _default_turn(3, has_context_reference=False),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_context_utilization(test_merchant, days=7)

        assert result["has_data"] is True
        assert result["data"]["utilization_rate"] == 0.0
        assert result["data"]["improvement_opportunities"] >= 1

    async def test_merchant_isolation(self, async_session, test_merchant):
        """Other merchant's turns are not visible."""
        from app.models.merchant import Merchant

        other = Merchant(
            merchant_key="iso-merchant-key",
            platform="messenger",
            email="iso@example.com",
            status="active",
        )
        async_session.add(other)
        await async_session.flush()
        await async_session.commit()

        await _create_conversation_with_turns(
            async_session,
            other.id,
            turns_data=[_default_turn(i, has_context_reference=True) for i in range(1, 4)],
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_context_utilization(test_merchant, days=7)

        assert result["has_data"] is False
