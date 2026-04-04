"""Gathering state persistence adapter for proactive information gathering.

Story 11-8: Proactive Information Gathering
Provides serialization/deserialization between GatheringState (Pydantic)
and ConversationContext metadata storage.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.services.proactive_gathering.schemas import GatheringState, MissingField

logger = structlog.get_logger(__name__)

_GATHERING_KEY = "proactive_gathering"


class GatheringStateAdapter:
    """Adapter between GatheringState and ConversationContext metadata.

    Single point of truth for serialization/deserialization of gathering
    state to/from ConversationContext.gathering_state field and metadata dict.
    """

    @staticmethod
    def load(context_metadata: dict[str, Any] | None) -> GatheringState | None:
        """Load GatheringState from conversation context metadata.

        Args:
            context_metadata: The context.metadata dict or gathering_state field

        Returns:
            GatheringState if active gathering flow exists, None otherwise
        """
        if not context_metadata:
            return None

        gs = context_metadata.get(_GATHERING_KEY)
        if not gs or not isinstance(gs, dict):
            return None

        if not gs.get("active", False):
            return None

        missing_fields = []
        for f in gs.get("missing_fields", []):
            missing_fields.append(
                MissingField(
                    field_name=f.get("field_name", ""),
                    display_name=f.get("display_name", ""),
                    priority=f.get("priority", 3),
                    mode=f.get("mode", "both"),
                    example_values=f.get("example_values", []),
                )
            )

        return GatheringState(
            active=gs.get("active", False),
            round_count=gs.get("round_count", 0),
            original_intent=gs.get("original_intent"),
            original_query=gs.get("original_query"),
            missing_fields=missing_fields,
            gathered_data=gs.get("gathered_data", {}),
            is_complete=gs.get("is_complete", False),
        )

    @staticmethod
    def save(
        context_metadata: dict[str, Any],
        state: GatheringState,
    ) -> dict[str, Any]:
        """Save GatheringState into conversation context metadata.

        Args:
            context_metadata: Current context.metadata dict
            state: GatheringState to persist

        Returns:
            Updated context.metadata dict
        """
        ctx = dict(context_metadata) if context_metadata else {}
        ctx[_GATHERING_KEY] = {
            "active": state.active,
            "round_count": state.round_count,
            "original_intent": state.original_intent,
            "original_query": state.original_query,
            "missing_fields": [
                {
                    "field_name": f.field_name,
                    "display_name": f.display_name,
                    "priority": f.priority,
                    "mode": f.mode,
                    "example_values": list(f.example_values),
                }
                for f in state.missing_fields
            ],
            "gathered_data": dict(state.gathered_data),
            "is_complete": state.is_complete,
        }
        return ctx

    @staticmethod
    def reset(context_metadata: dict[str, Any]) -> dict[str, Any]:
        """Reset gathering state in context metadata to inactive.

        Args:
            context_metadata: Current context.metadata dict

        Returns:
            Updated context.metadata dict
        """
        ctx = dict(context_metadata) if context_metadata else {}
        ctx[_GATHERING_KEY] = {
            "active": False,
            "round_count": 0,
            "original_intent": None,
            "original_query": None,
            "missing_fields": [],
            "gathered_data": {},
            "is_complete": False,
        }
        return ctx
