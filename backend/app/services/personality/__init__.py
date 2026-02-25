"""Personality-based bot prompts (Story 1.10).

Provides system prompts that adapt the bot's communication style
based on the merchant's selected personality type.

Story 5-12: Extended with PersonalityAwareResponseFormatter for
consistent personality across all response types.
"""

from __future__ import annotations

from app.services.personality.personality_prompts import (
    get_personality_system_prompt,
    PersonalityPromptService,
)
from app.services.personality.bot_response_service import BotResponseService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

__all__ = [
    "get_personality_system_prompt",
    "PersonalityPromptService",
    "BotResponseService",
    "PersonalityAwareResponseFormatter",
]
