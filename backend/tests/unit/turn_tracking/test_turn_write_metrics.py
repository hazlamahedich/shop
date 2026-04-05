"""Unit tests for turn write metrics initialization and incrementing.

Story 11-12a: Conversation Turn Tracking Pipeline

Tests that class-level metrics dict is properly initialized and incrementable.
"""

from __future__ import annotations

import pytest

from app.services.conversation.unified_conversation_service import (
    UnifiedConversationService,
)


class TestGivenTurnWriteMetrics:
    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-009")
    def test_when_checked_then_initialized_with_duplicate_and_unknown_keys(self):
        assert "duplicate" in UnifiedConversationService._turn_write_metrics
        assert "unknown" in UnifiedConversationService._turn_write_metrics
        assert UnifiedConversationService._turn_write_metrics["duplicate"] >= 0
        assert UnifiedConversationService._turn_write_metrics["unknown"] >= 0

    @pytest.mark.p0
    @pytest.mark.test_id("STORY-11-12a-010")
    def test_given_duplicate_when_incremented_then_counter_increases(self):
        prev = UnifiedConversationService._turn_write_metrics["duplicate"]
        UnifiedConversationService._turn_write_metrics["duplicate"] += 1
        assert UnifiedConversationService._turn_write_metrics["duplicate"] == prev + 1
        UnifiedConversationService._turn_write_metrics["duplicate"] = prev
