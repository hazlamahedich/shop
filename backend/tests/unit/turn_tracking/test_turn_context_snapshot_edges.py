"""Unit tests for build_turn_context_snapshot — edge cases.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests mode omission, boundary values, float rounding, and empty inputs.
"""

from __future__ import annotations

import pytest

from app.services.conversation.unified_conversation_service import (
    build_turn_context_snapshot,
)


class TestGivenEdgeCaseInputsWhenSnapshotBuilt:
    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-015")
    def test_given_none_mode_when_snapshot_built_then_mode_omitted(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.7,
            processing_time_ms=80.0,
            context=context,
            mode=None,
        )

        assert "mode" not in result
        assert result["confidence"] == 0.7
        assert result["processing_time_ms"] == 80

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-016")
    def test_given_zero_confidence_when_snapshot_built_then_records_zero(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=50.0,
            context=context,
            sentiment_confidence=0.0,
        )

        assert result["sentiment_score"] == 0.0

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-017")
    def test_given_float_processing_time_when_snapshot_built_then_rounds_to_int(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.9,
            processing_time_ms=99.7,
            context=context,
        )

        assert result["processing_time_ms"] == 99
        assert isinstance(result["processing_time_ms"], int)

    @pytest.mark.p1
    @pytest.mark.test_id("STORY-11-12a-019")
    def test_given_zero_processing_time_when_snapshot_built_then_rounds_correctly(
        self, make_context
    ):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.4,
            processing_time_ms=0.0,
            context=context,
        )

        assert result["processing_time_ms"] == 0
        assert isinstance(result["processing_time_ms"], int)

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-020")
    def test_given_no_optional_fields_when_snapshot_built_then_only_mandatories(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.3,
            processing_time_ms=10.0,
            context=context,
        )

        assert result == {
            "confidence": 0.3,
            "processing_time_ms": 10,
            "has_context_reference": False,
        }

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-022")
    def test_given_confidence_above_one_when_snapshot_built_then_records_as_is(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=1.5,
            processing_time_ms=100.0,
            context=context,
        )

        assert result["confidence"] == 1.5

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-023")
    def test_given_negative_confidence_when_snapshot_built_then_records_as_is(self, make_context):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=-0.1,
            processing_time_ms=100.0,
            context=context,
        )

        assert result["confidence"] == -0.1

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-024")
    def test_given_negative_sentiment_confidence_when_snapshot_built_then_records(
        self, make_context
    ):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=50.0,
            context=context,
            sentiment_confidence=-0.5,
        )

        assert result["sentiment_score"] == -0.5

    @pytest.mark.p2
    @pytest.mark.test_id("STORY-11-12a-025")
    def test_given_large_processing_time_when_snapshot_built_then_truncates_to_int(
        self, make_context
    ):
        context = make_context()

        result = build_turn_context_snapshot(
            confidence=0.8,
            processing_time_ms=99999.9,
            context=context,
        )

        assert result["processing_time_ms"] == 99999
        assert isinstance(result["processing_time_ms"], int)
