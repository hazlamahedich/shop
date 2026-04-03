"""Personality-based bot prompts (Story 1.10).

Provides system prompts that adapt the bot's communication style
based on the merchant's selected personality type.

Story 5-12: Extended with PersonalityAwareResponseFormatter for
consistent personality across all response types.

Story 11-4: Extended with TransitionSelector for natural conversational
transition phrases with anti-repetition tracking.

Story 11-5: Extended with personality validation, tracking, reinforcement,
middleware, and messenger templates for personality consistency.
"""

from __future__ import annotations

from app.services.personality.bot_response_service import BotResponseService
from app.services.personality.conversation_templates import register_conversation_templates
from app.services.personality.messenger_templates import register_messenger_templates
from app.services.personality.personality_middleware import with_personality
from app.services.personality.personality_prompts import (
    PersonalityPromptService,
    get_personality_system_prompt,
)
from app.services.personality.personality_reinforcement import get_personality_reinforcement
from app.services.personality.personality_tracker import (
    PersonalityTracker,
    get_personality_tracker,
)
from app.services.personality.personality_validator import validate_personality
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
    "validate_personality",
    "PersonalityTracker",
    "get_personality_tracker",
    "get_personality_reinforcement",
    "with_personality",
    "register_messenger_templates",
    "register_conversation_templates",
]
