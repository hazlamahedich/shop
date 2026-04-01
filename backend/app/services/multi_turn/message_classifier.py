"""Message classifier for multi-turn conversations.

Story 11-2: Multi-Turn Query Handling (AC6, AC10)
Two-tier classification: LLM primary + heuristic fallback.
"""

from __future__ import annotations

import re

import structlog

from app.core.errors import ErrorCode
from app.services.multi_turn.schemas import (
    MessageType,
    MultiTurnState,
    MultiTurnStateEnum,
)

logger = structlog.get_logger(__name__)


class MessageClassifier:
    """Classifies incoming messages in a multi-turn conversation.

    Two-tier approach:
    1. LLM-based classification (primary)
    2. Heuristic keyword matching (fallback when LLM fails)

    Ensures the conversation never blocks — always returns a classification.
    """

    INVALID_RESPONSES = frozenset({"asdf", "idk", "whatever", "dont know", "n/a", "huh", "?"})
    CONSTRAINT_PATTERNS = [
        r"\$\d+",
        r"under\s+\d+",
        r"over\s+\d+",
        r"size\s+\w+",
        r"color\s+\w+",
        r"brand\s+\w+",
        r"under\s+\$?\d+",
        r"less\s+than\s+\d+",
        r"more\s+than\s+\d+",
        r"between\s+\d+\s+and\s+\d+",
        r"cheap",
        r"expensive",
        r"affordable",
        r"premium",
        r"urgent",
        r"asap",
        r"critical",
        r"minor",
    ]

    def __init__(self, intent_classifier=None) -> None:
        self._llm = intent_classifier
        self.logger = structlog.get_logger(__name__)

    async def classify(
        self,
        message: str,
        state: MultiTurnState,
        context: dict | None = None,
    ) -> MessageType:
        if state.state == MultiTurnStateEnum.IDLE or state.state == "IDLE":
            return MessageType.NEW_QUERY

        if not state.original_query:
            return MessageType.NEW_QUERY

        if self._llm:
            try:
                result = await self._classify_with_llm(message, state, context)
                if result is not None:
                    return result
            except Exception as e:
                self.logger.warning(
                    "LLM classification failed, falling back to heuristic",
                    exc_info=True,
                    error=str(e),
                )
                self.logger.error(
                    "llm_classification_fallback",
                    error_code=ErrorCode.LLM_PROVIDER_ERROR,
                    error=str(e),
                    original_error_code=7090,
                )

        return self._classify_with_heuristics(message, state)

    async def _classify_with_llm(
        self,
        message: str,
        state: MultiTurnState,
        context: dict | None,
    ) -> MessageType | None:
        prompt = (
            f"Classify this message in a multi-turn conversation:\n"
            f"Original query: {state.original_query}\n"
            f"Current state: {state.state}\n"
            f"Constraints so far: {state.accumulated_constraints}\n"
            f"User message: {message}\n"
            f"Respond with exactly one: new_query, clarification_response, "
            f"constraint_addition, topic_change"
        )

        result = await self._llm.classify(prompt, context or {})

        if hasattr(result, "confidence") and result.confidence >= 0.7:
            label = result.intent.value if hasattr(result.intent, "value") else str(result.intent)
            label_map = {
                "new_query": MessageType.NEW_QUERY,
                "clarification_response": MessageType.CLARIFICATION_RESPONSE,
                "constraint_addition": MessageType.CONSTRAINT_ADDITION,
                "topic_change": MessageType.TOPIC_CHANGE,
            }
            return label_map.get(label)

        return None

    def _classify_with_heuristics(
        self,
        message: str,
        state: MultiTurnState,
    ) -> MessageType:
        if self._is_topic_change(message, state.original_query or ""):
            return MessageType.TOPIC_CHANGE

        current_state = state.state
        if isinstance(current_state, MultiTurnStateEnum):
            current_state = current_state.value

        if current_state in ("CLARIFYING", "REFINE_RESULTS"):
            if self._is_invalid_response(message):
                return MessageType.INVALID_RESPONSE
            if self._is_constraint_addition(message, state):
                return MessageType.CONSTRAINT_ADDITION

        if current_state == "CLARIFYING":
            return MessageType.CLARIFICATION_RESPONSE

        if current_state == "REFINE_RESULTS":
            if self._is_constraint_addition(message, state):
                return MessageType.CONSTRAINT_ADDITION
            return MessageType.TOPIC_CHANGE

        return MessageType.NEW_QUERY

    def _is_topic_change(self, message: str, original_query: str) -> bool:
        if not original_query:
            return False
        msg_words = set(message.lower().split())
        orig_words = set(original_query.lower().split())
        stop_words = {
            "i",
            "a",
            "an",
            "the",
            "is",
            "are",
            "was",
            "were",
            "it",
            "my",
            "me",
            "to",
            "for",
            "and",
            "or",
            "of",
            "in",
            "on",
            "at",
        }
        msg_keywords = msg_words - stop_words
        orig_keywords = orig_words - stop_words
        if not msg_keywords or not orig_keywords:
            return len(msg_keywords) < 2 and len(msg_words) > 3
        overlap = msg_keywords & orig_keywords
        return len(overlap) < 2 and len(msg_keywords) > 3

    def _is_constraint_addition(self, message: str, state: MultiTurnState) -> bool:
        lower_msg = message.lower()
        return any(re.search(p, lower_msg) for p in self.CONSTRAINT_PATTERNS)

    def _is_invalid_response(self, message: str) -> bool:
        stripped = message.strip()
        if len(stripped) < 2:
            return True
        if stripped.lower() in self.INVALID_RESPONSES:
            return True
        return False
