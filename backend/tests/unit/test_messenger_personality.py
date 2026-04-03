"""Tests for messenger personality template coverage (Story 11-5, AC8).

Validates that all messenger templates produce personality-appropriate
responses for all 3 personality types, and that message_processor.py
_fmt() calls correctly route to these templates.
"""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.messenger_templates import (
    MESSENGER_TEMPLATES,
    register_messenger_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.fixture(autouse=True)
def _register_templates():
    register_messenger_templates()


class TestMessengerTemplateCompleteness:
    def test_all_personalities_have_same_keys(self):
        friendly_keys = set(MESSENGER_TEMPLATES[PersonalityType.FRIENDLY].keys())
        professional_keys = set(MESSENGER_TEMPLATES[PersonalityType.PROFESSIONAL].keys())
        enthusiastic_keys = set(MESSENGER_TEMPLATES[PersonalityType.ENTHUSIASTIC].keys())
        assert friendly_keys == professional_keys == enthusiastic_keys

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_templates_non_empty(self, personality):
        templates = MESSENGER_TEMPLATES[personality]
        for key, value in templates.items():
            assert value.strip(), f"Template '{key}' for {personality.value} is empty"

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_all_templates_are_strings(self, personality):
        templates = MESSENGER_TEMPLATES[personality]
        for key, value in templates.items():
            assert isinstance(value, str), (
                f"Template '{key}' for {personality.value} is not a string"
            )


class TestMessengerTemplateFormatting:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_greeting_format(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "greeting",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_error_format(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "error",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_cart_confirm_with_substitution(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "cart_confirm",
            personality,
            title="Test Product",
            price="29.99",
        )
        assert "Test Product" in result
        assert "29.99" in result

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_welcome_back_with_substitution(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "welcome_back",
            personality,
            item_count=3,
            s="s",
        )
        assert "3" in result

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_out_of_stock_with_substitution(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "out_of_stock",
            personality,
            title="Cool Shoes",
        )
        assert "Cool Shoes" in result

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_fallback_format(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "fallback",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_forget_success_format(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "forget_success",
            personality,
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestMessengerPersonalityTone:
    def test_friendly_uses_emojis(self):
        templates = MESSENGER_TEMPLATES[PersonalityType.FRIENDLY]
        emoji_templates = ["greeting", "error", "unavailable", "fallback"]
        for key in emoji_templates:
            has_emoji = any(ord(c) > 0x1F000 for c in templates[key])
            assert has_emoji, f"Friendly template '{key}' should have emoji"

    def test_professional_no_excessive_emoji(self):
        templates = MESSENGER_TEMPLATES[PersonalityType.PROFESSIONAL]
        for key, value in templates.items():
            emoji_count = sum(1 for c in value if ord(c) > 0x1F000)
            assert emoji_count == 0, f"Professional template '{key}' should not have emoji"

    def test_enthusiastic_uses_exclamation(self):
        templates = MESSENGER_TEMPLATES[PersonalityType.ENTHUSIASTIC]
        exclamation_templates = ["greeting", "fallback", "handoff"]
        for key in exclamation_templates:
            assert "!" in templates[key], f"Enthusiastic template '{key}' should use exclamation"


class TestMessengerTemplateRegistration:
    def test_register_idempotent(self):
        register_messenger_templates()
        register_messenger_templates()
        result = PersonalityAwareResponseFormatter.format_response(
            "messenger",
            "greeting",
            PersonalityType.FRIENDLY,
        )
        assert "Hi" in result

    def test_all_keys_accessible_via_formatter(self):
        friendly_keys = set(MESSENGER_TEMPLATES[PersonalityType.FRIENDLY].keys())
        for key in friendly_keys:
            result = PersonalityAwareResponseFormatter.format_response(
                "messenger",
                key,
                PersonalityType.FRIENDLY,
            )
            assert result != "I'm here to help.", f"Template key '{key}' not found via formatter"
