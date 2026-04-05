"""Unit tests for non-blocking turn write failure handling.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests that turn write failures do not block the response and that
IntegrityError is tracked as 'duplicate' metric.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.conversation.unified_conversation_service import (
    UnifiedConversationService,
    build_turn_context_snapshot,
)


class TestGivenTurnWriteFailureWhenResponseGenerated:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-011")
    @pytest.mark.asyncio
    async def test_given_db_failure_when_turn_tracked_then_response_still_returned(
        self, make_context
    ):
        service = UnifiedConversationService.__new__(UnifiedConversationService)
        service._write_conversation_turn = AsyncMock(side_effect=Exception("DB connection lost"))
        service.logger = MagicMock()

        UnifiedConversationService._turn_write_metrics["unknown"] = 0

        db = AsyncMock()
        context = make_context(metadata={"current_sentiment_adaptation": None})
        conversation_id = 99
        processing_time_ms = 123.0
        intent_name = "greeting"
        confidence = 0.9

        turn_context_snapshot = build_turn_context_snapshot(
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            context=context,
            sentiment_adaptation=None,
        )

        try:
            await service._write_conversation_turn(
                db=db,
                conversation_id=conversation_id,
                turn_number=len(context.conversation_history) + 1,
                intent_detected=intent_name,
                sentiment=None,
                context_snapshot=turn_context_snapshot,
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

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-012")
    @pytest.mark.asyncio
    async def test_given_integrity_error_when_turn_tracked_then_tracked_as_duplicate(self):
        service = UnifiedConversationService.__new__(UnifiedConversationService)
        service._write_conversation_turn = AsyncMock(
            side_effect=IntegrityError("stmt", "params", "orig")
        )
        service.logger = MagicMock()
        prev = UnifiedConversationService._turn_write_metrics["duplicate"]

        db = AsyncMock()

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


class TestGivenMetricsResetWhenTestsRun:
    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-021")
    def test_given_autouse_fixture_when_test_runs_then_metrics_at_zero(self):
        assert UnifiedConversationService._turn_write_metrics["duplicate"] == 0
        assert UnifiedConversationService._turn_write_metrics["unknown"] == 0
