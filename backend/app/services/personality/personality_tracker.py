"""Conversation-level personality consistency tracker (Story 11-5, AC1, AC2).

Per-conversation singleton that tracks personality compliance across turns.
Follows TransitionSelector singleton pattern from Story 11-4.

Design decisions:
- Module-level singleton: consistency tracking works across handlers
- In-memory dict: sufficient for process-per-worker model
- TTL-based cleanup: removes abandoned conversations after CONVERSATION_TTL_SECONDS
- Drift detection: flags when 2+ consecutive failures or score drops below threshold

Thread safety: Safe under asyncio (single-threaded event loop).
See transition_selector.py for detailed safety analysis.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from app.models.merchant import PersonalityType

CONVERSATION_TTL_SECONDS = 3600  # 1 hour
CLEANUP_INTERVAL = 100
DRIFT_THRESHOLD = 0.7


@dataclass
class ConsistencyReport:
    """Snapshot of personality consistency for a conversation."""

    conversation_id: str
    turn_count: int
    violation_count: int
    consistency_score: float
    is_drifting: bool
    personality: PersonalityType | None = None


class PersonalityTracker:
    """Per-conversation personality consistency tracker.

    Follows the same singleton pattern as TransitionSelector (Story 11-4).
    Tracks personality compliance across conversation turns.

    MUST be used via get_personality_tracker() (not instantiated per-handler)
    so tracking works across handlers within a single conversation.
    """

    _instance: PersonalityTracker | None = None

    def __new__(cls) -> PersonalityTracker:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._validations: dict[str, list[bool]] = {}
            cls._instance._personalities: dict[str, PersonalityType] = {}
            cls._instance._turn_numbers: dict[str, list[int]] = {}
            cls._instance._last_access: dict[str, float] = {}
            cls._instance._operation_count: int = 0
        return cls._instance

    def record_validation(
        self,
        conversation_id: str,
        personality: PersonalityType,
        passed: bool,
        turn_number: int,
    ) -> None:
        """Record a validation result for tracking.

        Args:
            conversation_id: Conversation identifier
            personality: Expected personality type
            passed: Whether validation passed
            turn_number: Current turn number in conversation
        """
        self._operation_count += 1
        if self._operation_count % CLEANUP_INTERVAL == 0:
            self._cleanup_stale()

        if conversation_id not in self._validations:
            self._validations[conversation_id] = []
            self._turn_numbers[conversation_id] = []

        self._validations[conversation_id].append(passed)
        self._turn_numbers[conversation_id].append(turn_number)
        self._personalities[conversation_id] = personality
        self._last_access[conversation_id] = time.monotonic()

    def get_consistency_score(self, conversation_id: str) -> float:
        """Return 0.0-1.0 consistency score for the conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Score from 0.0 (all violations) to 1.0 (perfect consistency)
        """
        validations = self._validations.get(conversation_id)
        if not validations:
            return 0.0
        return sum(validations) / len(validations)

    def is_drifting(self, conversation_id: str) -> bool:
        """Return True if personality is drifting.

        Drift detected when:
        - Overall score drops below DRIFT_THRESHOLD
        - OR 2+ consecutive validation failures

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if drift detected
        """
        validations = self._validations.get(conversation_id)
        if not validations or len(validations) < 3:
            return False

        consecutive_failures = 0
        for v in validations:
            if not v:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    return True
            else:
                consecutive_failures = 0

        score_below_threshold = (
            len(validations) >= 4 and self.get_consistency_score(conversation_id) < DRIFT_THRESHOLD
        )

        return score_below_threshold

    def get_consistency_report(self, conversation_id: str) -> ConsistencyReport:
        """Get full consistency report for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            ConsistencyReport with all tracking details
        """
        validations = self._validations.get(conversation_id, [])
        turns = self._turn_numbers.get(conversation_id, [])

        return ConsistencyReport(
            conversation_id=conversation_id,
            turn_count=len(validations),
            violation_count=sum(1 for v in validations if not v),
            consistency_score=self.get_consistency_score(conversation_id),
            is_drifting=self.is_drifting(conversation_id),
            personality=self._personalities.get(conversation_id),
        )

    def clear_conversation(self, conversation_id: str) -> None:
        """Remove tracking data for a completed conversation."""
        self._validations.pop(conversation_id, None)
        self._turn_numbers.pop(conversation_id, None)
        self._personalities.pop(conversation_id, None)
        self._last_access.pop(conversation_id, None)

    def reset(self) -> None:
        """Reset all tracking data. Primarily for testing."""
        self._validations.clear()
        self._turn_numbers.clear()
        self._personalities.clear()
        self._last_access.clear()
        self._operation_count = 0

    def _cleanup_stale(self) -> None:
        """Remove conversations not accessed within TTL period."""
        now = time.monotonic()
        cutoff = now - CONVERSATION_TTL_SECONDS
        stale_ids = [
            conv_id for conv_id, last_time in self._last_access.items() if last_time < cutoff
        ]
        for conv_id in stale_ids:
            self.clear_conversation(conv_id)

    @property
    def active_conversation_count(self) -> int:
        """Number of conversations currently tracked."""
        return len(self._validations)

    def get_turn_count(self, conversation_id: str) -> int:
        """Get number of turns tracked for a conversation."""
        return len(self._validations.get(conversation_id, []))


def get_personality_tracker() -> PersonalityTracker:
    """Get the shared PersonalityTracker singleton instance."""
    return PersonalityTracker()
