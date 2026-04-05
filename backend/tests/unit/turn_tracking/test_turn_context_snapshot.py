"""Unit tests for build_turn_context_snapshot — basic cases.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests the pure function that builds a context snapshot dictionary
from confidence, processing time, context, sentiment, and mode inputs.
"""

from __future__ import annotations

import pytest

from app.services.conversation.schemas import ClarificationState
from app.services.conversation.unified_conversation_service import (
    build_turn_context_snapshot,
)


class TestGivenBasicInputsWhenSnapshotBuilt:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-001")
    def test_then_includes_confidence_processing_time_and_mode(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.92,
            processing_time_ms=150.5,
            context=context,
            mode="ecommerce",
        )

        assert result["confidence"] == 0.92
        assert result["processing_time_ms"] == 150
        assert result["has_context_reference"] is False
        assert result["mode"] == "ecommerce"
        assert "sentiment_score" not in result
        assert "clarification_state" not in result

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-005")
    def test_given_history_when_snapshot_built_then_has_context_reference_true(self, make_context):
        context = make_context(history=[{"role": "user", "content": "hello"}])

        result = build_turn_context_snapshot(
            confidence=0.6,
            processing_time_ms=50.0,
            context=context,
        )

        assert result["has_context_reference"] is True

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-006")
    def test_given_no_adaptation_when_snapshot_built_then_no_sentiment(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.7,
            processing_time_ms=80.0,
            context=context,
        )

        assert "sentiment_score" not in result

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-013")
    def test_given_sentiment_confidence_float_when_snapshot_built_then_includes_score(
        self, make_context
    ):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.85,
            processing_time_ms=120.0,
            context=context,
            sentiment_confidence=0.72,
        )

        assert result["sentiment_score"] == 0.72

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-014")
    def test_given_adaptation_and_confidence_when_snapshot_built_then_adaptation_takes_precedence(
        self, make_context, make_sentiment_adaptation
    ):
        adaptation = make_sentiment_adaptation(confidence=0.88)
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
            sentiment_adaptation=adaptation,
            sentiment_confidence=0.42,
        )

        assert result["sentiment_score"] == 0.88
