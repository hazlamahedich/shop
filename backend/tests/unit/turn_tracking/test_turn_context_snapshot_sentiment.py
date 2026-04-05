"""Unit tests for build_turn_context_snapshot — sentiment cases.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests sentiment passthrough, adaptation precedence, and score inclusion.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.conversation.unified_conversation_service import (
    build_turn_context_snapshot,
)


class TestGivenSentimentInputsWhenSnapshotBuilt:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-002")
    def test_given_adaptation_when_snapshot_built_then_includes_sentiment_score(
        self, make_context, make_sentiment_adaptation
    ):
        adaptation = make_sentiment_adaptation(confidence=0.75)
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.85,
            processing_time_ms=200.0,
            context=context,
            sentiment_adaptation=adaptation,
        )

        assert result["sentiment_score"] == 0.75

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-018")
    def test_given_adaptation_without_score_when_snapshot_built_then_omits_field(
        self, make_context
    ):
        context = make_context()
        adaptation_no_score = MagicMock()
        adaptation_no_score.original_score = None

        result = build_turn_context_snapshot(
            confidence=0.6,
            processing_time_ms=70.0,
            context=context,
            sentiment_adaptation=adaptation_no_score,
        )

        assert "sentiment_score" not in result
