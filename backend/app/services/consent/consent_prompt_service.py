"""Consent prompt service for personality-aware consent messages.

Story 6-1: Opt-In Consent Flow

Provides personality-aware consent prompts using PersonalityAwareResponseFormatter.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


logger = structlog.get_logger(__name__)


class ConsentPromptService:
    """Service for generating personality-aware consent prompts.

    Uses PersonalityAwareResponseFormatter for consistent tone and style
    across all consent-related messages.
    """

    CONSENT_TEMPLATES = {
        PersonalityType.FRIENDLY: {
            "prompt": "To remember your preferences for faster shopping next time, I'll save your conversation. OK? 😊",
            "opt_in_confirm": "Great! I'll remember your preferences to help you shop faster! 🛍️",
            "opt_out_confirm": "No problem! I won't save your conversation history. Your current session will still work normally. 👍",
            "forget_confirm": "I've forgotten your preferences and conversation history. Your order references are kept for business purposes. 🗑️",
        },
        PersonalityType.PROFESSIONAL: {
            "prompt": "To provide personalized service in future conversations, I'll save your conversation data. Do you consent?",
            "opt_in_confirm": "Your preferences have been saved. This will help provide better service in future conversations.",
            "opt_out_confirm": "Your preference has been recorded. Your current session will function normally without data persistence.",
            "forget_confirm": "Your preferences and conversation history have been deleted. Order references are retained for business purposes.",
        },
        PersonalityType.ENTHUSIASTIC: {
            "prompt": "Want me to remember your preferences so I can help you shop EVEN FASTER next time?! 🎉",
            "opt_in_confirm": "AWESOME! I'll remember everything to give you the BEST shopping experience! ✨🛒",
            "opt_out_confirm": "No worries! I'll treat every chat like a fresh start! Still here to help you find AMAZING products! 💪",
            "forget_confirm": "POOF! Your preferences are gone! 🎩✨ Order info stays for business stuff, but everything else is wiped clean!",
        },
    }

    def __init__(self) -> None:
        """Initialize consent prompt service and register templates."""
        PersonalityAwareResponseFormatter.register_response_type(
            "consent",
            self.CONSENT_TEMPLATES,
        )
        self.logger = structlog.get_logger(__name__)

    def get_consent_prompt_message(self, personality: PersonalityType) -> str:
        """Get personality-aware consent prompt message.

        Args:
            personality: Merchant's personality type

        Returns:
            Consent prompt message in appropriate tone
        """
        return PersonalityAwareResponseFormatter.format_response(
            "consent",
            "prompt",
            personality,
        )

    def get_opt_in_confirm_message(self, personality: PersonalityType) -> str:
        """Get personality-aware opt-in confirmation message.

        Args:
            personality: Merchant's personality type

        Returns:
            Opt-in confirmation message in appropriate tone
        """
        return PersonalityAwareResponseFormatter.format_response(
            "consent",
            "opt_in_confirm",
            personality,
        )

    def get_opt_out_confirm_message(self, personality: PersonalityType) -> str:
        """Get personality-aware opt-out confirmation message.

        Args:
            personality: Merchant's personality type

        Returns:
            Opt-out confirmation message in appropriate tone
        """
        return PersonalityAwareResponseFormatter.format_response(
            "consent",
            "opt_out_confirm",
            personality,
        )

    def get_forget_confirm_message(self, personality: PersonalityType) -> str:
        """Get personality-aware forget preferences confirmation message.

        Args:
            personality: Merchant's personality type

        Returns:
            Forget confirmation message in appropriate tone
        """
        return PersonalityAwareResponseFormatter.format_response(
            "consent",
            "forget_confirm",
            personality,
        )

    def get_consent_quick_replies(self) -> list[dict[str, str]]:
        """Get quick reply buttons for consent prompt.

        Returns:
            List of quick reply button definitions
        """
        return [
            {
                "content_type": "text",
                "title": "Yes, save my preferences",
                "payload": "CONSENT_OPT_IN",
            },
            {
                "content_type": "text",
                "title": "No, don't save",
                "payload": "CONSENT_OPT_OUT",
            },
        ]
