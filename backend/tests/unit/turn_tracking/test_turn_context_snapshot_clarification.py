"""Unit tests for build_turn_context_snapshot — clarification state cases.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests clarification state serialization and omission logic.
"""

from __future__ import annotations

import pytest

from app.services.conversation.schemas import ClarificationState
from app.services.conversation.unified_conversation_service import (
    build_turn_context_snapshot,
)


class TestGivenClarificationStateWhenSnapshotBuilt:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-003")
    def test_given_active_clarification_when_snapshot_built_then_serializes_state(
        self, make_context
    ):
        cs = ClarificationState(
            active=True,
            multi_turn_state="CLARIFYING",
            attempt_count=2,
        )
        context = make_context(clarification_state=cs)

        result = build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
        )

        assert result["clarification_state"] == "CLARIFYING"
        assert result["clarification_attempt_count"] == 2

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-004")
    def test_given_idle_clarification_when_snapshot_built_then_omits_fields(self, make_context):
        cs = ClarificationState(multi_turn_state="IDLE")
        context = make_context(clarification_state=cs)

        result = build_turn_context_snapshot(
            confidence=0.5,
            processing_time_ms=100.0,
            context=context,
        )

        assert "clarification_state" not in result
        assert "clarification_attempt_count" not in result
