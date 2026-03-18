"""Consent prompt service for personality-aware consent messages.

Story 6-1: Opt-In Consent Flow

Provides personality-aware consent prompts using PersonalityAwareResponseFormatter.
"""

from __future__ import annotations

from datetime import datetime

import structlog

from app.models.merchant import PersonalityType
from app.schemas.consent import ConsentStatus
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
            "status_opted_in": "Yup! Your preferences are saved! 😊 I'll remember you for faster shopping. (Saved on {date})",
            "status_opted_out": "No worries! You chose not to save your data, so I treat every chat as a fresh start. 👍",
            "status_pending": "I haven't asked about saving your preferences yet! Want me to remember you for next time?",
        },
        PersonalityType.PROFESSIONAL: {
            "prompt": "To provide personalized service in future conversations, I'll save your conversation data. Do you consent?",
            "opt_in_confirm": "Your preferences have been saved. This will help provide better service in future conversations.",
            "opt_out_confirm": "Your preference has been recorded. Your current session will function normally without data persistence.",
            "forget_confirm": "Your preferences and conversation history have been deleted. Order references are retained for business purposes.",
            "status_opted_in": "Your preferences are currently saved. You opted in on {date}. This helps provide personalized service in future conversations.",
            "status_opted_out": "Your preference to not save conversation data is recorded. Each session will start fresh.",
            "status_pending": "No consent preference has been recorded yet. Would you like to save your preferences for future conversations?",
        },
        PersonalityType.ENTHUSIASTIC: {
            "prompt": "Want me to remember your preferences so I can help you shop EVEN FASTER next time?! 🎉",
            "opt_in_confirm": "AWESOME! I'll remember everything to give you the BEST shopping experience! ✨🛒",
            "opt_out_confirm": "No worries! I'll treat every chat like a fresh start! Still here to help you find AMAZING products! 💪",
            "forget_confirm": "POOF! Your preferences are gone! 🎩✨ Order info stays for business stuff, but everything else is wiped clean!",
            "status_opted_in": "YES! I remember you! 🎉 Your preferences are saved (since {date}) and I'm ready to help you shop EVEN FASTER!",
            "status_opted_out": "Got it! You prefer fresh starts, so every chat is a NEW ADVENTURE! 🌟",
            "status_pending": "We haven't set up your preferences yet! Ready to make shopping AMAZING? 🛒✨",
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

    def get_status_check_message(
        self,
        personality: PersonalityType,
        status: ConsentStatus,
        granted_at: datetime | None = None,
        locale: str = "en_US",
    ) -> str:
        """Get personality-aware consent status check message.

        Args:
            personality: Merchant's personality type
            status: Current consent status
            granted_at: Optional timestamp when consent was granted
            locale: Locale for date formatting (default: en_US)

        Returns:
            Status check message in appropriate tone
        """
        if status == ConsentStatus.OPTED_IN:
            template_key = "status_opted_in"
            date_str = self._format_localized_date(granted_at, locale) if granted_at else "recently"
            return PersonalityAwareResponseFormatter.format_response(
                "consent",
                template_key,
                personality,
            ).format(date=date_str)
        elif status == ConsentStatus.OPTED_OUT:
            return PersonalityAwareResponseFormatter.format_response(
                "consent",
                "status_opted_out",
                personality,
            )
        else:
            return PersonalityAwareResponseFormatter.format_response(
                "consent",
                "status_pending",
                personality,
            )

    def _format_localized_date(self, dt: datetime | None, locale: str = "en_US") -> str:
        """Format date according to locale.

        Args:
            dt: Datetime to format
            locale: Locale string (e.g., 'en_US', 'en_GB', 'de_DE')

        Returns:
            Formatted date string
        """
        if dt is None:
            return "recently"

        try:
            from babel.dates import format_date

            locale_map = {"en_GB": "en_GB", "de_DE": "de_DE", "fr_FR": "fr_FR", "es_ES": "es_ES"}
            babel_locale = locale_map.get(locale, "en_US")
            return format_date(dt, format="long", locale=babel_locale)
        except ImportError:
            if locale == "en_GB":
                return dt.strftime("%d %B %Y")
            return dt.strftime("%B %d, %Y")

    def get_consent_management_quick_replies(self, status: ConsentStatus) -> list[dict[str, str]]:
        """Get quick reply buttons for consent status response.

        Args:
            status: Current consent status to determine appropriate options

        Returns:
            List of quick reply button definitions
        """
        if status == ConsentStatus.OPTED_IN:
            return [
                {
                    "content_type": "text",
                    "title": "Change my preferences",
                    "payload": "CONSENT_CHANGE",
                },
                {
                    "content_type": "text",
                    "title": "Delete my data",
                    "payload": "CONSENT_DELETE",
                },
            ]
        elif status == ConsentStatus.OPTED_OUT:
            return [
                {
                    "content_type": "text",
                    "title": "Save my preferences",
                    "payload": "CONSENT_OPT_IN",
                },
            ]
        else:
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
