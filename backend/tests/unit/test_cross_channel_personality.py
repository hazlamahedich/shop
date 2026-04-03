"""Tests for cross-channel personality consistency (Story 11-5, AC10).

Validates that messenger (Widget) and conversation handler templates
produce consistent personality tones across all channels.
"""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.conversation_templates import (
    CONVERSATION_TEMPLATES,
    register_conversation_templates,
)
from app.services.personality.messenger_templates import (
    MESSENGER_TEMPLATES,
    register_messenger_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.fixture(autouse=True)
def _register_templates():
    register_messenger_templates()
    register_conversation_templates()


class TestConversationTemplateCompleteness:
    def test_all_personalities_have_same_keys(self):
        friendly_keys = set(CONVERSATION_TEMPLATES[PersonalityType.FRIENDLY].keys())
        professional_keys = set(CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL].keys())
        enthusiastic_keys = set(CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC].keys())
        assert friendly_keys == professional_keys == enthusiastic_keys

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_templates_non_empty(self, personality):
        templates = CONVERSATION_TEMPLATES[personality]
        for key, value in templates.items():
            assert value.strip(), f"Template '{key}' for {personality.value} is empty"


class TestConversationTemplateFormatting:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_clarification_fallback(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "clarification_fallback",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_consent_check_error(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "consent_check_error",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_forget_rate_limited(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "forget_rate_limited",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_forget_error(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "forget_error",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_forget_unexpected_error(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "forget_unexpected_error",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_llm_classification_leak(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "llm_classification_leak",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_llm_fallback_with_business_name(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "llm_fallback",
            personality,
            business_name="Test Store",
        )
        assert "Test Store" in result

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_welcome_back_fallback(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "welcome_back_fallback",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_bot_paused(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "bot_paused",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestCrossChannelToneParity:
    """Verify same personality produces consistent tone across channels."""

    def test_friendly_has_emojis_in_both_channels(self):
        messenger_error = MESSENGER_TEMPLATES[PersonalityType.FRIENDLY]["error"]
        conv_consent_err = CONVERSATION_TEMPLATES[PersonalityType.FRIENDLY]["consent_check_error"]
        assert any(ord(c) > 0x1F000 for c in messenger_error)
        assert any(ord(c) > 0x1F000 for c in conv_consent_err)

    def test_professional_no_emoji_in_both_channels(self):
        messenger_error = MESSENGER_TEMPLATES[PersonalityType.PROFESSIONAL]["error"]
        conv_consent_err = CONVERSATION_TEMPLATES[PersonalityType.PROFESSIONAL][
            "consent_check_error"
        ]
        assert not any(ord(c) > 0x1F000 for c in messenger_error)
        assert not any(ord(c) > 0x1F000 for c in conv_consent_err)

    def test_enthusiastic_uses_caps_in_both_channels(self):
        messenger_greeting = MESSENGER_TEMPLATES[PersonalityType.ENTHUSIASTIC]["greeting"]
        conv_leak = CONVERSATION_TEMPLATES[PersonalityType.ENTHUSIASTIC]["llm_classification_leak"]
        assert any(c.isupper() for c in messenger_greeting)
        assert any(c.isupper() for c in conv_leak)

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_error_messages_helpful_in_both_channels(self, personality):
        messenger_error = MESSENGER_TEMPLATES[PersonalityType(personality)]["error"]
        conv_error = CONVERSATION_TEMPLATES[PersonalityType(personality)]["forget_error"]
        for msg in [messenger_error, conv_error]:
            assert "try again" in msg.lower() or "try" in msg.lower()


class TestConversationTemplateRegistration:
    def test_register_idempotent(self):
        register_conversation_templates()
        register_conversation_templates()
        result = PersonalityAwareResponseFormatter.format_response(
            "conversation",
            "clarification_fallback",
            PersonalityType.FRIENDLY,
        )
        assert "Could you" in result

    def test_all_keys_accessible_via_formatter(self):
        friendly_keys = set(CONVERSATION_TEMPLATES[PersonalityType.FRIENDLY].keys())
        for key in friendly_keys:
            result = PersonalityAwareResponseFormatter.format_response(
                "conversation",
                key,
                PersonalityType.FRIENDLY,
            )
            assert result != "I'm here to help.", f"Template key '{key}' not found via formatter"
