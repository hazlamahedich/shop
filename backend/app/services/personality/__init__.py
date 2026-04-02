"""Personality-based bot prompts (Story 1.10).

Provides system prompts that adapt the bot's communication style
based on the merchant's selected personality type.

Story 5-12: Extended with PersonalityAwareResponseFormatter for
consistent personality across all response types.

Story 11-4: Extended with TransitionSelector for natural conversational
transition phrases with anti-repetition tracking.
"""

from __future__ import annotations

from app.services.personality.bot_response_service import BotResponseService
from app.services.personality.personality_prompts import (
    PersonalityPromptService,
    get_personality_system_prompt,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
    TransitionCategory,
    get_phrases_for_mode,
)
from app.services.personality.transition_selector import (
    TransitionSelector,
    get_transition_selector,
)

__all__ = [
    "get_personality_system_prompt",
    "PersonalityPromptService",
    "BotResponseService",
    "PersonalityAwareResponseFormatter",
    "TransitionCategory",
    "TransitionSelector",
    "get_transition_selector",
    "get_phrases_for_mode",
    "RESPONSE_TYPE_TO_TRANSITION",
    "TEMPLATES_WITH_OPENINGS",
]
