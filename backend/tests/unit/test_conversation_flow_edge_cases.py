from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.conversation_context import ConversationTurn
from app.services.analytics.conversation_flow_analytics_service import (
    ConversationFlowAnalyticsService,
)


async def _create_conversation_with_turns(
    async_session: AsyncSession,
    merchant_id: int,
    *,
    handoff_status: str = "none",
    conv_status: str = "active",
    turns_data: list[dict] | None = None,
    platform_sender_id: str | None = None,
) -> tuple[Conversation, list[ConversationTurn]]:
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
    user_message: str | None = None,
) -> dict:
    return {
        "turn_number": turn_number,
        "intent_detected": intent or ("product_search" if turn_number % 2 == 0 else "greeting"),
        "sentiment": sentiment,
        "user_message": user_message,
        "context_snapshot": {
            "confidence": 0.9,
            "processing_time_ms": processing_time_ms,
            "has_context_reference": has_context_reference,
            "mode": mode,
            "clarification_state": clarification_state,
            "clarification_attempt_count": clarification_attempt_count,
        },
    }


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-08")
class TestErrorHandling:
    @pytest.mark.parametrize(
        "method_name,expected_message",
        [
            (
                "get_conversation_length_distribution",
                "Unable to compute conversation length distribution.",
            ),
            ("get_clarification_patterns", "Unable to compute clarification patterns."),
            ("get_friction_points", "Unable to compute friction points."),
            ("get_sentiment_distribution_by_stage", "Unable to compute sentiment distribution."),
            ("get_handoff_correlation", "Unable to compute handoff correlation."),
            ("get_context_utilization", "Unable to compute context utilization."),
        ],
    )
    async def test_error_handling_returns_graceful_no_data(self, method_name, expected_message):
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.execute = AsyncMock(side_effect=Exception("DB connection error"))
        service = ConversationFlowAnalyticsService(mock_db)
        method = getattr(service, method_name)
        result = await method(merchant_id=1, days=7)
        assert result["has_data"] is False
        assert result["message"] == expected_message


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-09")
class TestNegativeSentimentShift:
    async def test_negative_sentiment_shift_with_intent_correlation(
        self, async_session, test_merchant
    ):
        turns_data = []
        for i in range(1, 4):
            turns_data.append(_default_turn(i, sentiment="POSITIVE", intent="greeting"))
        for i in range(8, 11):
            turns_data.append(_default_turn(i, sentiment="NEGATIVE", intent="complaint"))
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_sentiment_distribution_by_stage(test_merchant, days=7)

        assert result["has_data"] is True
        negative_shifts = result["data"]["negative_shifts"]
        assert len(negative_shifts) > 0
        for shift in negative_shifts:
            assert "intent_at_shift" in shift
            assert shift["early_negative_rate"] < shift["late_negative_rate"]


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-10")
class TestAnonymizedExcerptTruncation:
    async def test_anonymized_excerpt_truncation(self, async_session, test_merchant):
        long_message = "X" * 150
        turns_data = [
            _default_turn(1, intent="escalate", user_message=long_message),
        ]
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            handoff_status="active",
            turns_data=turns_data,
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is True
        for excerpt in result["data"]["anonymized_excerpts"]:
            assert len(excerpt["anonymized_message"]) <= 100


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-11")
class TestPrivacyNoteInHandoffResponse:
    async def test_privacy_note_in_handoff_response(self, async_session, test_merchant):
        turns_data = [
            _default_turn(1, intent="complaint"),
            _default_turn(2, intent="escalate"),
        ]
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            handoff_status="active",
            turns_data=turns_data,
        )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is True
        assert result["data"]["privacy_note"] == "Conversation excerpts are anonymized for privacy"


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-12")
class TestContextUtilizationAt50PercentThreshold:
    async def test_context_utilization_at_50_percent_threshold(self, async_session, test_merchant):
        turns_50 = [
            _default_turn(1, has_context_reference=True),
            _default_turn(2, has_context_reference=True),
            _default_turn(3, has_context_reference=False),
            _default_turn(4, has_context_reference=False),
        ]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_50)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_context_utilization(test_merchant, days=7)

        assert result["has_data"] is True
        assert result["data"]["improvement_opportunities"] == 0

        turns_25 = [
            _default_turn(1, has_context_reference=True),
            _default_turn(2, has_context_reference=False),
            _default_turn(3, has_context_reference=False),
            _default_turn(4, has_context_reference=False),
        ]
        await _create_conversation_with_turns(
            async_session,
            test_merchant,
            turns_data=turns_25,
            platform_sender_id="conv-25pct",
        )

        result2 = await service.get_context_utilization(test_merchant, days=7)
        assert result2["has_data"] is True
        assert result2["data"]["improvement_opportunities"] >= 1


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-13")
class TestDaysParameterBoundaryMin:
    async def test_days_parameter_boundary_min(self, async_session, test_merchant):
        turns_data = [_default_turn(1)]
        await _create_conversation_with_turns(async_session, test_merchant, turns_data=turns_data)

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_conversation_length_distribution(test_merchant, days=1)

        assert result["has_data"] is True


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-14")
class TestClarificationSequenceOrdering:
    async def test_clarification_sequence_ordering(self, async_session, test_merchant):
        for i in range(3):
            turns_data = [
                _default_turn(
                    1,
                    intent="greeting",
                    clarification_state="CLARIFYING",
                    clarification_attempt_count=1,
                ),
                _default_turn(
                    2,
                    intent="product_search",
                    clarification_state="CLARIFYING",
                    clarification_attempt_count=2,
                ),
                _default_turn(
                    3,
                    intent="checkout",
                    clarification_state="COMPLETE",
                    clarification_attempt_count=2,
                ),
            ]
            await _create_conversation_with_turns(
                async_session,
                test_merchant,
                turns_data=turns_data,
                platform_sender_id=f"conv-clarity-{i}",
            )

        for i in range(2):
            turns_data = [
                _default_turn(
                    1,
                    intent="greeting",
                    clarification_state="CLARIFYING",
                    clarification_attempt_count=1,
                ),
                _default_turn(
                    2,
                    intent="order_check",
                    clarification_state="COMPLETE",
                    clarification_attempt_count=1,
                ),
            ]
            await _create_conversation_with_turns(
                async_session,
                test_merchant,
                turns_data=turns_data,
                platform_sender_id=f"conv-clarity-alt-{i}",
            )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_clarification_patterns(test_merchant, days=7)

        assert result["has_data"] is True
        top_sequences = result["data"]["top_sequences"]
        assert len(top_sequences) <= 5
        if len(top_sequences) > 1:
            for idx in range(len(top_sequences) - 1):
                assert top_sequences[idx]["count"] >= top_sequences[idx + 1]["count"]


@pytest.mark.p1
@pytest.mark.test_id("STORY-11-12b-SEQ-15")
class TestHandoffRatePerIntentCalculation:
    async def test_handoff_rate_per_intent_calculation(self, async_session, test_merchant):
        for i in range(2):
            turns_data = [
                _default_turn(1, intent="escalate"),
            ]
            await _create_conversation_with_turns(
                async_session,
                test_merchant,
                handoff_status="active",
                turns_data=turns_data,
                platform_sender_id=f"conv-handoff-intent-{i}",
            )

        for i in range(3):
            turns_data = [
                _default_turn(1, intent="escalate"),
            ]
            await _create_conversation_with_turns(
                async_session,
                test_merchant,
                handoff_status="none",
                turns_data=turns_data,
                platform_sender_id=f"conv-no-handoff-intent-{i}",
            )

        service = ConversationFlowAnalyticsService(async_session)
        result = await service.get_handoff_correlation(test_merchant, days=7)

        assert result["has_data"] is True
        handoff_rates = result["data"]["handoff_rate_per_intent"]
        escalate_rate = next((r for r in handoff_rates if r["intent"] == "escalate"), None)
        assert escalate_rate is not None
        assert escalate_rate["handoff_count"] == 2
        assert escalate_rate["total_count"] == 5
        assert escalate_rate["handoff_rate"] == 40.0
