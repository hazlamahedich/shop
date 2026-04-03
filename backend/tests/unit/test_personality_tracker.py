"""Tests for conversation-level personality tracker (Story 11-5, AC1, AC2).

Validates cross-turn consistency tracking and drift detection.
"""

import time

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.personality_tracker import (
    DRIFT_THRESHOLD,
    PersonalityTracker,
    get_personality_tracker,
)


@pytest.fixture(autouse=True)
def reset_tracker():
    tracker = get_personality_tracker()
    tracker.reset()
    yield
    tracker.reset()


class TestPersonalityTrackerSingleton:
    """Tracker follows TransitionSelector singleton pattern."""

    def test_singleton_returns_same_instance(self):
        t1 = get_personality_tracker()
        t2 = get_personality_tracker()
        assert t1 is t2

    def test_new_direct_also_singleton(self):
        t1 = PersonalityTracker()
        t2 = PersonalityTracker()
        assert t1 is t2


class TestRecordValidation:
    """Record personality validation results per conversation."""

    def test_record_single_validation(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        assert tracker.get_consistency_score("conv-1") == 1.0

    def test_record_multiple_validations_all_pass(self):
        tracker = get_personality_tracker()
        for turn in range(1, 6):
            tracker.record_validation(
                "conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=turn
            )
        assert tracker.get_consistency_score("conv-1") == 1.0

    def test_record_mixed_validations(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=False, turn_number=2)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=3)
        score = tracker.get_consistency_score("conv-1")
        assert 0.5 < score < 1.0

    def test_record_all_failures(self):
        tracker = get_personality_tracker()
        for turn in range(1, 4):
            tracker.record_validation(
                "conv-1", PersonalityType.FRIENDLY, passed=False, turn_number=turn
            )
        assert tracker.get_consistency_score("conv-1") == 0.0


class TestConsistencyScore:
    """Consistency score calculation (0.0-1.0)."""

    def test_no_data_returns_zero(self):
        tracker = get_personality_tracker()
        assert tracker.get_consistency_score("unknown-conv") == 0.0

    def test_perfect_score(self):
        tracker = get_personality_tracker()
        for i in range(10):
            tracker.record_validation(
                "conv-1", PersonalityType.PROFESSIONAL, passed=True, turn_number=i + 1
            )
        assert tracker.get_consistency_score("conv-1") == 1.0

    def test_zero_score(self):
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(
                "conv-1", PersonalityType.PROFESSIONAL, passed=False, turn_number=i + 1
            )
        assert tracker.get_consistency_score("conv-1") == 0.0


class TestDriftDetection:
    """Drift detection: 2+ consecutive failures → drifting."""

    def test_no_drift_when_consistent(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=2)
        assert not tracker.is_drifting("conv-1")

    def test_drift_after_consecutive_failures(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=False, turn_number=2)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=False, turn_number=3)
        assert tracker.is_drifting("conv-1")

    def test_no_drift_with_single_failure(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=2)
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=False, turn_number=3)
        assert not tracker.is_drifting("conv-1")

    def test_drift_from_low_score_without_consecutive(self):
        tracker = get_personality_tracker()
        for i in range(10):
            passed = i % 2 == 0
            tracker.record_validation(
                "conv-1", PersonalityType.FRIENDLY, passed=passed, turn_number=i + 1
            )
        assert tracker.get_consistency_score("conv-1") < DRIFT_THRESHOLD
        assert tracker.is_drifting("conv-1")

    def test_no_drift_for_unknown_conversation(self):
        tracker = get_personality_tracker()
        assert not tracker.is_drifting("unknown-conv")

    def test_drift_threshold_below_score(self):
        tracker = get_personality_tracker()
        for i in range(10):
            passed = i < 3
            tracker.record_validation(
                "conv-1", PersonalityType.FRIENDLY, passed=passed, turn_number=i + 1
            )
        assert tracker.get_consistency_score("conv-1") < DRIFT_THRESHOLD


class TestTTLBasedCleanup:
    """TTL-based cleanup prevents memory leaks."""

    def test_cleanup_removes_stale_conversations(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        assert tracker.active_conversation_count == 1
        tracker._last_access["conv-1"] = time.monotonic() - 7200
        tracker._cleanup_stale()
        assert tracker.active_conversation_count == 0

    def test_cleanup_keeps_active_conversations(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker._cleanup_stale()
        assert tracker.active_conversation_count == 1

    def test_cleanup_triggered_by_operations(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker._last_access["conv-1"] = time.monotonic() - 7200
        for _ in range(200):
            tracker.record_validation(
                "conv-2", PersonalityType.FRIENDLY, passed=True, turn_number=1
            )
        assert "conv-1" not in tracker._validations


class TestClearConversation:
    """Clear conversation data."""

    def test_clear_removes_tracking(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.clear_conversation("conv-1")
        assert tracker.get_consistency_score("conv-1") == 0.0
        assert tracker.active_conversation_count == 0

    def test_clear_nonexistent_is_noop(self):
        tracker = get_personality_tracker()
        tracker.clear_conversation("nonexistent")
        assert tracker.active_conversation_count == 0


class TestReset:
    """Reset all tracking data."""

    def test_reset_clears_everything(self):
        tracker = get_personality_tracker()
        for i in range(5):
            tracker.record_validation(
                f"conv-{i}", PersonalityType.FRIENDLY, passed=True, turn_number=1
            )
        assert tracker.active_conversation_count == 5
        tracker.reset()
        assert tracker.active_conversation_count == 0
        assert tracker.get_consistency_score("conv-0") == 0.0


class TestMultipleConversations:
    """Tracker handles multiple conversations independently."""

    def test_independent_conversation_tracking(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation(
            "conv-2", PersonalityType.PROFESSIONAL, passed=False, turn_number=1
        )
        assert tracker.get_consistency_score("conv-1") == 1.0
        assert tracker.get_consistency_score("conv-2") == 0.0

    def test_clear_one_doesnt_affect_other(self):
        tracker = get_personality_tracker()
        tracker.record_validation("conv-1", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.record_validation("conv-2", PersonalityType.FRIENDLY, passed=True, turn_number=1)
        tracker.clear_conversation("conv-1")
        assert tracker.get_consistency_score("conv-1") == 0.0
        assert tracker.get_consistency_score("conv-2") == 1.0
