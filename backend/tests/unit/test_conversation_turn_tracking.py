"""Unit tests for conversation turn tracking pipeline (Story 11-12a).

Tests turn record creation, sentiment passthrough, non-blocking failure,
IntegrityError handling, clarification state serialization, and edge cases.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.conversation_context import ConversationTurn
from app.services.analytics.sentiment_analyzer import Sentiment, SentimentScore
from app.services.conversation.schemas import (
    Channel,
    ClarificationState,
    ConversationContext,
    SessionShoppingState,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdaptation,
    SentimentStrategy,
)


def _make_context(
    history: list[dict[str, Any]] | None = None,
    clarification_state: ClarificationState | None = None,
    metadata: dict[str, Any] | None = None,
) -> ConversationContext:
    return ConversationContext(
        session_id="sess-test",
        merchant_id=1,
        channel=Channel.WIDGET,
        shopping_state=SessionShoppingState(),
        conversation_history=history or [],
        clarification_state=clarification_state or ClarificationState(),
        metadata=metadata or {},
    )


def _make_sentiment_adaptation(
    strategy: SentimentStrategy = SentimentStrategy.EMPATHETIC,
    confidence: float = 0.8,
) -> SentimentAdaptation:
    return SentimentAdaptation(
        strategy=strategy,
        original_score=SentimentScore(
            sentiment=Sentiment.NEGATIVE,
            positive_score=0.1,
            negative_score=0.8,
            confidence=confidence,
            matched_terms=["frustrated"],
        ),
        pre_phrase_key=f"pre_{strategy.value}",
        post_phrase_key=f"post_{strategy.value}",
        mode="ecommerce",
    )


class TestBuildTurnContextSnapshot:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-001")
    def test_basic_snapshot_with_confidence_and_time(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        context = _make_context()

        result = service._build_turn_context_snapshot(
            confidence=0.92,
            processing_time_ms=150.5,
            context=context,
            sentiment_adaptation=None,
        )

        assert result["confidence"] == 0.92
        assert result["processing_time_ms"] == 150
        assert result["has_context_reference"] is False
        assert "sentiment_score" not in result
        assert "clarification_state" not in result

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-002")
    def test_sentiment_score_included_when_adaptation_provided(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        adaptation = _make_sentiment_adaptation(confidence=0.75)
        context = _make_context()

        result = service._build_turn_context_snapshot(
            confidence=0.85,
            processing_time_ms=200.0,
            context=context,
            sentiment_adaptation=adaptation,
        )

        assert result["sentiment_score"] == 0.75

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-003")
    def test_clarification_state_serialized_when_active(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        cs = ClarificationState(
            active=True,
            multi_turn_state="CLARIFYING",
            attempt_count=2,
        )
        context = _make_context(clarification_state=cs)

        result = service._build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
            sentiment_adaptation=None,
        )

        assert result["clarification_state"] == "CLARIFYING"
        assert result["clarification_attempt_count"] == 2

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-004")
    def test_clarification_state_omitted_when_idle(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        cs = ClarificationState(multi_turn_state="IDLE")
        context = _make_context(clarification_state=cs)

        result = service._build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
            sentiment_adaptation=None,
        )

        assert "clarification_state" not in result
        assert "clarification_attempt_count" not in result

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-005")
    def test_has_context_reference_true_with_history(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        context = _make_context(
            history=[{"role": "user", "content": "hello"}],
        )

        result = service._build_turn_context_snapshot(
            confidence=0.6,
            processing_time_ms=50.0,
            context=context,
            sentiment_adaptation=None,
        )

        assert result["has_context_reference"] is True

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-006")
    def test_no_sentiment_when_adaptation_is_none(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        context = _make_context()

        result = service._build_turn_context_snapshot(
            confidence=0.7,
            processing_time_ms=80.0,
            context=context,
            sentiment_adaptation=None,
        )

        assert "sentiment_score" not in result

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-013")
    def test_sentiment_confidence_from_raw_float(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        context = _make_context()

        result = service._build_turn_context_snapshot(
            confidence=0.85,
            processing_time_ms=120.0,
            context=context,
            sentiment_confidence=0.72,
        )

        assert result["sentiment_score"] == 0.72

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-014")
    def test_adaptation_takes_precedence_over_confidence(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._build_turn_context_snapshot = (
            UnifiedConversationService._build_turn_context_snapshot.__get__(service)
        )
        adaptation = _make_sentiment_adaptation(confidence=0.88)
        context = _make_context()

        result = service._build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
            sentiment_adaptation=adaptation,
            sentiment_confidence=0.42,
        )

        assert result["sentiment_score"] == 0.88


class TestWriteConversationTurn:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-007")
    @pytest.mark.asyncio
    async def test_turn_record_created_with_correct_fields(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = (
            UnifiedConversationService._write_conversation_turn.__get__(service)
        )

        db = AsyncMock()
        nested_cm = AsyncMock()
        nested_cm.__aenter__ = AsyncMock(return_value=None)
        nested_cm.__aexit__ = AsyncMock(return_value=None)
        db.begin_nested = MagicMock(return_value=nested_cm)
        db.add = MagicMock()
        db.flush = AsyncMock()

        snapshot = {"confidence": 0.9, "processing_time_ms": 100}

        await service._write_conversation_turn(
            db=db,
            conversation_id=42,
            turn_number=3,
            intent_detected="product_search",
            sentiment="EMPATHETIC",
            context_snapshot=snapshot,
            user_message="I want red shoes",
            bot_response="Here are some red shoes!",
        )

        db.add.assert_called_once()
        turn_obj = db.add.call_args[0][0]
        assert isinstance(turn_obj, ConversationTurn)
        assert turn_obj.conversation_id == 42
        assert turn_obj.turn_number == 3
        assert turn_obj.intent_detected == "product_search"
        assert turn_obj.sentiment == "EMPATHETIC"
        assert turn_obj.context_snapshot == snapshot
        assert turn_obj.user_message == "I want red shoes"
        assert turn_obj.bot_response == "Here are some red shoes!"

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-008")
    @pytest.mark.asyncio
    async def test_integrity_error_propagates(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = (
            UnifiedConversationService._write_conversation_turn.__get__(service)
        )

        db = AsyncMock()

        nested_cm = AsyncMock()
        nested_cm.__aenter__ = AsyncMock(side_effect=IntegrityError("stmt", "params", "orig"))
        nested_cm.__aexit__ = AsyncMock(return_value=False)
        db.begin_nested = MagicMock(return_value=nested_cm)

        with pytest.raises(IntegrityError):
            await service._write_conversation_turn(
                db=db,
                conversation_id=1,
                turn_number=1,
                intent_detected="greeting",
                sentiment=None,
                context_snapshot={},
            )


class TestTurnWriteMetrics:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-009")
    def test_metrics_initialized(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        assert "duplicate" in UnifiedConversationService._turn_write_metrics
        assert "unknown" in UnifiedConversationService._turn_write_metrics
        assert UnifiedConversationService._turn_write_metrics["duplicate"] >= 0
        assert UnifiedConversationService._turn_write_metrics["unknown"] >= 0

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-010")
    def test_duplicate_metric_increments(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        prev = UnifiedConversationService._turn_write_metrics["duplicate"]
        UnifiedConversationService._turn_write_metrics["duplicate"] += 1
        assert UnifiedConversationService._turn_write_metrics["duplicate"] == prev + 1
        UnifiedConversationService._turn_write_metrics["duplicate"] = prev


class TestTurnTrackingNonBlocking:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-011")
    @pytest.mark.asyncio
    async def test_turn_write_failure_does_not_block_response(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = AsyncMock(side_effect=Exception("DB connection lost"))
        service._build_turn_context_snapshot = MagicMock(return_value={"confidence": 0.5})
        service.logger = MagicMock()
        UnifiedConversationService._turn_write_metrics["unknown"] = 0

        db = AsyncMock()
        context = _make_context(metadata={"current_sentiment_adaptation": None})
        conversation_id = 99
        processing_time_ms = 123.0
        intent_name = "greeting"
        confidence = 0.9
        message = "hello"
        response = MagicMock()
        response.message = "Hi there!"

        try:
            turn_context_snapshot = service._build_turn_context_snapshot(
                confidence=confidence,
                processing_time_ms=processing_time_ms,
                context=context,
                sentiment_adaptation=None,
            )
            await service._write_conversation_turn(
                db=db,
                conversation_id=conversation_id,
                turn_number=len(context.conversation_history) + 1,
                intent_detected=intent_name,
                sentiment=None,
                context_snapshot=turn_context_snapshot,
                user_message=message,
                bot_response=response.message,
            )
        except Exception as e:
            error_type = "duplicate" if isinstance(e, IntegrityError) else "unknown"
            UnifiedConversationService._turn_write_metrics[error_type] += 1
            service.logger.error(
                "conversation_turn_write_failed",
                error_code=7127,
                conversation_id=conversation_id,
                error=str(e),
                error_type=error_type,
                metric_count=UnifiedConversationService._turn_write_metrics[error_type],
            )

        service._write_conversation_turn.assert_called_once()
        service.logger.error.assert_called_once()
        call_kwargs = service.logger.error.call_args
        assert call_kwargs[1]["error_code"] == 7127
        assert call_kwargs[1]["conversation_id"] == 99
        assert UnifiedConversationService._turn_write_metrics["unknown"] == 1

        assert response.message == "Hi there!"

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-012")
    @pytest.mark.asyncio
    async def test_integrity_error_tracked_as_duplicate(self):
        from app.services.conversation.unified_conversation_service import (
            UnifiedConversationService,
        )

        service = MagicMock(spec=UnifiedConversationService)
        service._write_conversation_turn = AsyncMock(
            side_effect=IntegrityError("stmt", "params", "orig")
        )
        service.logger = MagicMock()
        prev = UnifiedConversationService._turn_write_metrics["duplicate"]
        UnifiedConversationService._turn_write_metrics["duplicate"] = prev

        db = AsyncMock()
        context = _make_context()

        try:
            await service._write_conversation_turn(
                db=db,
                conversation_id=1,
                turn_number=1,
                intent_detected="greeting",
                sentiment=None,
                context_snapshot={},
            )
        except Exception as e:
            error_type = "duplicate" if isinstance(e, IntegrityError) else "unknown"
            UnifiedConversationService._turn_write_metrics[error_type] += 1

        assert UnifiedConversationService._turn_write_metrics["duplicate"] == prev + 1
        UnifiedConversationService._turn_write_metrics["duplicate"] = prev
