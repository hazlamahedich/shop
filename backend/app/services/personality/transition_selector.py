"""Transition phrase selector with anti-repetition tracking (Story 11-4).

Shared singleton that tracks recently used phrases per conversation
to avoid repetitive patterns in bot responses.

Design decisions:
- Module-level singleton: anti-repetition works across handlers
- In-memory dict: sufficient for process-per-worker model
- MAX_RECENT_PER_CONVERSATION: prevents unbounded growth per conversation
- TTL-based cleanup: removes abandoned conversations after CONVERSATION_TTL_SECONDS
"""

from __future__ import annotations

import random
import time

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    TRANSITION_PHRASES,
    TransitionCategory,
    get_phrases_for_mode,
)

MAX_RECENT_PER_CONVERSATION = 50
CONVERSATION_TTL_SECONDS = 3600  # 1 hour
CLEANUP_INTERVAL = 100  # run cleanup every N selects


class TransitionSelector:
    """Shared singleton — tracks recently used phrases per conversation.

    MUST be used via get_transition_selector() (not instantiated per-handler)
    so anti-repetition works across handlers within a single conversation.
    """

    MAX_RECENT_PER_CONVERSATION = MAX_RECENT_PER_CONVERSATION

    _instance: TransitionSelector | None = None

    def __new__(cls) -> TransitionSelector:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._recent: dict[str, set[str]] = {}
            cls._instance._last_access: dict[str, float] = {}
            cls._instance._select_count: int = 0
        return cls._instance

    def _cleanup_stale(self) -> None:
        """Remove conversations not accessed within TTL period."""
        now = time.monotonic()
        cutoff = now - CONVERSATION_TTL_SECONDS
        stale_ids = [
            conv_id for conv_id, last_time in self._last_access.items() if last_time < cutoff
        ]
        for conv_id in stale_ids:
            self._recent.pop(conv_id, None)
            self._last_access.pop(conv_id, None)

    def select(
        self,
        category: TransitionCategory,
        personality: PersonalityType,
        conversation_id: str | None = None,
        mode: str = "ecommerce",
    ) -> str:
        """Select a transition phrase with anti-repetition.

        Args:
            category: Transition context category
            personality: Merchant's personality type
            conversation_id: Conversation ID for anti-repetition tracking
            mode: "ecommerce" or "general" for mode-specific phrases

        Returns:
            Selected transition phrase
        """
        self._select_count += 1
        if self._select_count % CLEANUP_INTERVAL == 0:
            self._cleanup_stale()

        phrases = get_phrases_for_mode(category, personality, mode)

        available = phrases
        if conversation_id and conversation_id in self._recent:
            used = self._recent[conversation_id]
            unused = [p for p in phrases if p not in used]
            if unused:
                available = unused
            else:
                self._recent[conversation_id].clear()
                available = phrases

        selected = random.choice(available)

        if conversation_id:
            recent = self._recent.setdefault(conversation_id, set())
            recent.add(selected)
            if len(recent) > self.MAX_RECENT_PER_CONVERSATION:
                excess = len(recent) - self.MAX_RECENT_PER_CONVERSATION
                to_remove = list(recent)[:excess]
                for item in to_remove:
                    recent.discard(item)
            self._last_access[conversation_id] = time.monotonic()

        return selected

    def clear_conversation(self, conversation_id: str) -> None:
        """Remove tracking data for a completed conversation."""
        self._recent.pop(conversation_id, None)
        self._last_access.pop(conversation_id, None)

    def reset(self) -> None:
        """Reset all tracking data. Primarily for testing."""
        self._recent.clear()
        self._last_access.clear()
        self._select_count = 0

    def get_recent_count(self, conversation_id: str) -> int:
        """Get number of tracked phrases for a conversation. For testing."""
        return len(self._recent.get(conversation_id, set()))

    @property
    def active_conversation_count(self) -> int:
        """Number of conversations currently tracked. For testing/monitoring."""
        return len(self._recent)


def get_transition_selector() -> TransitionSelector:
    """Get the shared TransitionSelector singleton instance."""
    return TransitionSelector()
