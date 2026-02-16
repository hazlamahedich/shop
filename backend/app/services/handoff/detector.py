"""Handoff detection service for human assistance triggers.

Detects when shoppers need human help based on:
- Keyword matching (human, agent, etc.)
- Low confidence scores (consecutive < 0.50)
- Clarification loops (same question 3 times)

Implements IS_TESTING pattern for deterministic test responses.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any

import structlog

from app.core.config import settings
from app.schemas.handoff import (
    HandoffReason,
    HandoffResult,
)

logger = structlog.get_logger(__name__)

CONFIDENCE_THRESHOLD = 0.50
CONFIDENCE_TRIGGER_COUNT = 3
LOOP_TRIGGER_COUNT = 3
CLARIFICATION_STATE_TTL = 86400  # 24 hours

HANDOFF_KEYWORDS = [
    "human",
    "person",
    "agent",
    "customer service",
    "real person",
    "talk to someone",
    "speak to someone",
    "representative",
    "manager",
    "support",
    "live chat",
    "operator",
    "help desk",
]

KEYWORD_PATTERN = r"\b(" + "|".join(re.escape(kw) for kw in HANDOFF_KEYWORDS) + r")\b"

CLARIFICATION_STATE_KEY = "clarification:{conversation_id}:state"


class HandoffDetector:
    """Detects when shoppers need human assistance.

    Three detection mechanisms:
    1. Keyword detection - immediate trigger on specific phrases
    2. Low confidence - trigger after 3 consecutive low-confidence responses
    3. Clarification loop - trigger after 3 same-type clarifications
    """

    def __init__(self, redis_client: Any | None = None):
        """Initialize handoff detector.

        Args:
            redis_client: Redis client for state tracking (optional in test mode)
        """
        self.redis_client = redis_client
        self._keyword_pattern = re.compile(KEYWORD_PATTERN, re.IGNORECASE)

    async def detect(
        self,
        message: str,
        conversation_id: int,
        confidence_score: float | None = None,
        clarification_type: str | None = None,
    ) -> HandoffResult:
        """Check if handoff should be triggered.

        Args:
            message: Customer message to analyze
            conversation_id: Conversation ID for state tracking
            confidence_score: LLM confidence score (0.0-1.0), if available
            clarification_type: Current clarification type if in clarification flow

        Returns:
            HandoffResult indicating if handoff should trigger and why
        """
        if settings().get("IS_TESTING", False):
            return HandoffResult(should_handoff=False, reason=None)

        keyword_result = self._check_keywords(message)
        if keyword_result.should_handoff:
            logger.info(
                "handoff_keyword_triggered",
                conversation_id=conversation_id,
                matched_keyword=keyword_result.matched_keyword,
            )
            return keyword_result

        confidence_result = await self._check_confidence(conversation_id, confidence_score)
        if confidence_result.should_handoff:
            logger.info(
                "handoff_low_confidence_triggered",
                conversation_id=conversation_id,
                confidence_count=confidence_result.confidence_count,
            )
            return confidence_result

        loop_result = await self._check_clarification_loop(conversation_id, clarification_type)
        if loop_result.should_handoff:
            logger.info(
                "handoff_loop_detected",
                conversation_id=conversation_id,
                loop_count=loop_result.loop_count,
                clarification_type=clarification_type,
            )
            return loop_result

        return HandoffResult(
            should_handoff=False,
            reason=None,
            confidence_count=confidence_result.confidence_count,
            loop_count=loop_result.loop_count,
        )

    def _check_keywords(self, message: str) -> HandoffResult:
        """Check for handoff keywords in message.

        Uses word boundary matching to avoid false positives
        (e.g., "humanity" should NOT trigger "human").

        Args:
            message: Customer message to analyze

        Returns:
            HandoffResult with should_handoff=True if keyword found
        """
        match = self._keyword_pattern.search(message)
        if match:
            return HandoffResult(
                should_handoff=True,
                reason=HandoffReason.KEYWORD,
                matched_keyword=match.group(1).lower(),
            )
        return HandoffResult(should_handoff=False, reason=None)

    async def _check_confidence(
        self,
        conversation_id: int,
        confidence_score: float | None,
    ) -> HandoffResult:
        """Check for consecutive low confidence scores.

        Tracks consecutive messages with confidence < 0.50.
        Triggers handoff after 3 consecutive low-confidence responses.

        Args:
            conversation_id: Conversation ID for state tracking
            confidence_score: Current confidence score (0.0-1.0)

        Returns:
            HandoffResult with should_handoff=True if threshold reached
        """
        if self.redis_client is None:
            return HandoffResult(should_handoff=False, reason=None)

        count_key = f"handoff:confidence:{conversation_id}:count"

        if confidence_score is None:
            return HandoffResult(should_handoff=False, reason=None)

        if confidence_score >= CONFIDENCE_THRESHOLD:
            await self._reset_confidence_count(count_key)
            return HandoffResult(should_handoff=False, reason=None, confidence_count=0)

        current_count = await self._increment_confidence_count(count_key)

        if current_count >= CONFIDENCE_TRIGGER_COUNT:
            await self._reset_confidence_count(count_key)
            return HandoffResult(
                should_handoff=True,
                reason=HandoffReason.LOW_CONFIDENCE,
                confidence_count=current_count,
            )

        return HandoffResult(
            should_handoff=False,
            reason=None,
            confidence_count=current_count,
        )

    async def _check_clarification_loop(
        self,
        conversation_id: int,
        clarification_type: str | None,
    ) -> HandoffResult:
        """Check for clarification loop (same question multiple times).

        Tracks clarification state in Redis with 24h TTL.
        Triggers handoff after 3 same-type clarifications.

        Args:
            conversation_id: Conversation ID for state tracking
            clarification_type: Current clarification type if in flow

        Returns:
            HandoffResult with should_handoff=True if loop detected
        """
        if self.redis_client is None or clarification_type is None:
            return HandoffResult(should_handoff=False, reason=None)

        state_key = CLARIFICATION_STATE_KEY.format(conversation_id=conversation_id)

        state_data = await self._get_clarification_state(state_key)

        if state_data is None or state_data.get("type") != clarification_type:
            await self._set_clarification_state(state_key, clarification_type, 1)
            return HandoffResult(should_handoff=False, reason=None, loop_count=1)

        current_count = state_data.get("count", 0) + 1

        if current_count >= LOOP_TRIGGER_COUNT:
            await self._clear_clarification_state(state_key)
            return HandoffResult(
                should_handoff=True,
                reason=HandoffReason.CLARIFICATION_LOOP,
                loop_count=current_count,
            )

        await self._set_clarification_state(state_key, clarification_type, current_count)
        return HandoffResult(
            should_handoff=False,
            reason=None,
            loop_count=current_count,
        )

    async def reset_state(self, conversation_id: int) -> None:
        """Reset all handoff state for a conversation.

        Called when conversation successfully progresses or handoff completes.

        Args:
            conversation_id: Conversation ID to reset
        """
        if self.redis_client is None:
            return

        count_key = f"handoff:confidence:{conversation_id}:count"
        state_key = CLARIFICATION_STATE_KEY.format(conversation_id=conversation_id)

        await self._reset_confidence_count(count_key)
        await self._clear_clarification_state(state_key)

        logger.info("handoff_state_reset", conversation_id=conversation_id)

    async def _increment_confidence_count(self, key: str) -> int:
        """Increment and return confidence counter."""
        if self.redis_client is None:
            return 0
        try:
            count = await self.redis_client.incr(key)
            await self.redis_client.expire(key, CLARIFICATION_STATE_TTL)
            return count
        except Exception as e:
            logger.warning("redis_confidence_count_failed", key=key, error=str(e))
            return 1

    async def _reset_confidence_count(self, key: str) -> None:
        """Reset confidence counter."""
        if self.redis_client is None:
            return
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.warning("redis_confidence_reset_failed", key=key, error=str(e))

    async def _get_clarification_state(self, key: str) -> dict | None:
        """Get clarification state from Redis."""
        if self.redis_client is None:
            return None
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning("redis_clarification_get_failed", key=key, error=str(e))
            return None

    async def _set_clarification_state(self, key: str, clarification_type: str, count: int) -> None:
        """Set clarification state in Redis with TTL."""
        if self.redis_client is None:
            return
        try:
            state = {
                "type": clarification_type,
                "count": count,
                "last_asked": datetime.now(timezone.utc).isoformat(),
            }
            await self.redis_client.setex(key, CLARIFICATION_STATE_TTL, json.dumps(state))
        except Exception as e:
            logger.warning("redis_clarification_set_failed", key=key, error=str(e))

    async def _clear_clarification_state(self, key: str) -> None:
        """Clear clarification state from Redis."""
        if self.redis_client is None:
            return
        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.warning("redis_clarification_clear_failed", key=key, error=str(e))


__all__ = [
    "HandoffDetector",
    "HANDOFF_KEYWORDS",
    "CONFIDENCE_THRESHOLD",
    "CONFIDENCE_TRIGGER_COUNT",
    "LOOP_TRIGGER_COUNT",
    "CLARIFICATION_STATE_TTL",
]
