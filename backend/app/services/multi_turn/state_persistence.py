"""State persistence adapter for multi-turn conversation state.

Story 11-2 Tech Debt: Decouples state machine from JSONB persistence.
Provides a single adapter between MultiTurnState (Pydantic) and
conversation.context JSONB storage, so schema changes only need to
update this file instead of both the API and state machine.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.multi_turn.schemas import (
    MultiTurnState,
    MultiTurnStateEnum,
)

logger = structlog.get_logger(__name__)

_CONTEXT_KEY = "clarification_state"


class MultiTurnStateAdapter:
    """Adapter between MultiTurnState and conversation.context JSONB.

    Single point of truth for serialization/deserialization of multi-turn
    state to/from database storage. All reads/writes of multi-turn state
    from conversation.context MUST go through this adapter.
    """

    @staticmethod
    def load(conversation_context: dict[str, Any] | None) -> MultiTurnState | None:
        """Load MultiTurnState from conversation context JSONB.

        Args:
            conversation_context: The conversation.context dict from DB

        Returns:
            MultiTurnState if active multi-turn flow exists, None otherwise
        """
        if not conversation_context:
            return None

        cs = conversation_context.get(_CONTEXT_KEY)
        if not cs or not isinstance(cs, dict):
            return None

        state_str = cs.get("multi_turn_state", "IDLE")
        if state_str in (MultiTurnStateEnum.IDLE, "COMPLETE"):
            return None

        return MultiTurnState(
            state=state_str,
            turn_count=cs.get("turn_count", 0),
            accumulated_constraints=cs.get("accumulated_constraints", {}),
            questions_asked=list(cs.get("questions_asked", [])),
            pending_questions=[],
            original_query=cs.get("original_query"),
            invalid_response_count=cs.get("invalid_response_count", 0),
            mode=cs.get("mode", "ecommerce"),
        )

    @staticmethod
    def save(
        conversation_context: dict[str, Any],
        state: MultiTurnState,
    ) -> dict[str, Any]:
        """Save MultiTurnState into conversation context JSONB.

        Args:
            conversation_context: Current conversation.context dict
            state: MultiTurnState to persist

        Returns:
            Updated conversation.context dict (safe to assign back)
        """
        ctx = dict(conversation_context) if conversation_context else {}
        ctx[_CONTEXT_KEY] = {
            "multi_turn_state": state.state.value
            if hasattr(state.state, "value")
            else str(state.state),
            "turn_count": state.turn_count,
            "accumulated_constraints": state.accumulated_constraints,
            "questions_asked": list(state.questions_asked),
            "pending_questions": list(state.pending_questions),
            "original_query": state.original_query,
            "invalid_response_count": state.invalid_response_count,
            "mode": state.mode,
            "clarification_turns": [_serialize_turn(t) for t in state.clarification_turns],
        }
        return ctx

    @staticmethod
    def reset(conversation_context: dict[str, Any]) -> dict[str, Any]:
        """Reset multi-turn state in conversation context to IDLE.

        Args:
            conversation_context: Current conversation.context dict

        Returns:
            Updated conversation.context dict
        """
        ctx = dict(conversation_context) if conversation_context else {}
        ctx[_CONTEXT_KEY] = {
            "multi_turn_state": "IDLE",
            "turn_count": 0,
            "accumulated_constraints": {},
            "questions_asked": [],
            "pending_questions": [],
            "original_query": None,
            "invalid_response_count": 0,
            "mode": "ecommerce",
            "clarification_turns": [],
        }
        return ctx


def _serialize_turn(turn: Any) -> dict[str, Any]:
    """Serialize a ClarificationTurn to dict for JSONB storage."""
    return {
        "question_asked": turn.question_asked,
        "constraint_name": turn.constraint_name,
        "user_response": turn.user_response,
        "is_valid": turn.is_valid,
    }
