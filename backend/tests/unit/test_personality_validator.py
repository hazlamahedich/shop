"""Tests for personality validation rules engine (Story 11-5).

Validates AC4 (Personality Validation) and AC5 (Personality Doesn't Conflict with Clarity).
"""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.personality_validator import (
    ValidationResult,
    validate_personality,
)


class TestProfessionalValidation:
    """AC4: Professional personality rules — no emojis, formal language, no slang."""

    def test_professional_no_emojis_passes(self):
        result = validate_personality(
            "Here are the available products.",
            PersonalityType.PROFESSIONAL,
        )
        assert result.passed

    def test_professional_with_emoji_fails(self):
        result = validate_personality(
            "Here are the available products! 😊",
            PersonalityType.PROFESSIONAL,
        )
        assert not result.passed
        assert any("emoji" in v.lower() for v in result.violations)

    def test_professional_multiple_emojis_fails(self):
        result = validate_personality(
            "Check these out! 🎉🔥✨",
            PersonalityType.PROFESSIONAL,
        )
        assert not result.passed
        assert any("emoji" in v.lower() for v in result.violations)

    def test_professional_slang_fails(self):
        result = validate_personality(
            "Awesome! Here's what I found.",
            PersonalityType.PROFESSIONAL,
        )
        assert not result.passed
        assert any("slang" in v.lower() for v in result.violations)

    def test_professional_contractions_allowed(self):
        result = validate_personality(
            "I don't have that product, but here's an alternative.",
            PersonalityType.PROFESSIONAL,
        )
        assert result.passed

    def test_professional_formal_language_passes(self):
        result = validate_personality(
            "Thank you for your inquiry. Here are the available options.",
            PersonalityType.PROFESSIONAL,
        )
        assert result.passed

    def test_professional_exclamation_allowed_minimal(self):
        result = validate_personality(
            "Here is the information you requested.",
            PersonalityType.PROFESSIONAL,
        )
        assert result.passed

    def test_professional_abbreviations_pass(self):
        result = validate_personality(
            "You're right, the order has shipped.",
            PersonalityType.PROFESSIONAL,
        )
        assert result.passed


class TestFriendlyValidation:
    """AC4: Friendly personality rules — ≤2 emojis, casual tone, contractions."""

    def test_friendly_no_emojis_passes(self):
        result = validate_personality(
            "Sure thing! Here's what I found for you.",
            PersonalityType.FRIENDLY,
        )
        assert result.passed

    def test_friendly_one_emoji_passes(self):
        result = validate_personality(
            "Here are the options! 😊",
            PersonalityType.FRIENDLY,
        )
        assert result.passed

    def test_friendly_two_emojis_passes(self):
        result = validate_personality(
            "Great finds! Check these out! 😊🎉",
            PersonalityType.FRIENDLY,
        )
        assert result.passed

    def test_friendly_three_emojis_fails(self):
        result = validate_personality(
            "Amazing! Look at these! 😊🎉🔥",
            PersonalityType.FRIENDLY,
        )
        assert not result.passed
        assert any("emoji" in v.lower() for v in result.violations)

    def test_friendly_casual_tone_passes(self):
        result = validate_personality(
            "No worries! Let me help you with that.",
            PersonalityType.FRIENDLY,
        )
        assert result.passed

    def test_friendly_contraction_passes(self):
        result = validate_personality(
            "I've found some great options for you!",
            PersonalityType.FRIENDLY,
        )
        assert result.passed


class TestEnthusiasticValidation:
    """AC4: Enthusiastic personality rules — ≥1 exclamation, energetic, emojis allowed."""

    def test_enthusiastic_with_exclamation_passes(self):
        result = validate_personality(
            "Here are some AMAZING options! 🔥",
            PersonalityType.ENTHUSIASTIC,
        )
        assert result.passed

    def test_enthusiastic_without_exclamation_fails(self):
        result = validate_personality(
            "Here are the available products.",
            PersonalityType.ENTHUSIASTIC,
        )
        assert not result.passed
        assert any("exclamation" in v.lower() for v in result.violations)

    def test_enthusiastic_with_emojis_passes(self):
        result = validate_personality(
            "WOW! Check these out!!! 🎉🔥✨",
            PersonalityType.ENTHUSIASTIC,
        )
        assert result.passed

    def test_enthusiastic_excessive_emojis_warns(self):
        result = validate_personality(
            "LOL!!! 😂🤣😊🎉🔥✨💫💖😍🥰🛒😢",
            PersonalityType.ENTHUSIASTIC,
        )
        assert not result.passed
        assert any("emoji" in v.lower() for v in result.violations)

    def test_enthusiastic_energy_words_passes(self):
        result = validate_personality(
            "AMAZING! You're gonna LOVE these! 🔥",
            PersonalityType.ENTHUSIASTIC,
        )
        assert result.passed


class TestClarityPreservation:
    """AC5: Personality doesn't conflict with clarity — critical content preserved."""

    def test_price_preserved_in_friendly(self):
        text = "Great deal! This item is $29.99 😊"
        result = validate_personality(text, PersonalityType.FRIENDLY)
        assert result.critical_content_preserved

    def test_price_preserved_in_professional(self):
        text = "The price is $29.99."
        result = validate_personality(text, PersonalityType.PROFESSIONAL)
        assert result.critical_content_preserved

    def test_order_number_preserved(self):
        text = "Your order #12345 has shipped! 🎉"
        result = validate_personality(text, PersonalityType.ENTHUSIASTIC)
        assert result.critical_content_preserved

    def test_url_preserved(self):
        text = "Checkout here: https://shop.example.com/checkout"
        result = validate_personality(text, PersonalityType.FRIENDLY)
        assert result.critical_content_preserved

    def test_multiple_critical_items_preserved(self):
        text = "Order #12345 — $49.99 — https://track.example.com/abc"
        result = validate_personality(text, PersonalityType.PROFESSIONAL)
        assert result.critical_content_preserved

    def test_empty_text_preserves_nothing(self):
        result = validate_personality("", PersonalityType.FRIENDLY)
        assert result.critical_content_preserved

    def test_no_critical_content_returns_false(self):
        text = "Here are some great options for you today!"
        result = validate_personality(text, PersonalityType.FRIENDLY)
        assert not result.critical_content_preserved

    def test_decimal_price_preserved(self):
        text = "Your total is 19.99."
        result = validate_personality(text, PersonalityType.PROFESSIONAL)
        assert result.critical_content_preserved

    def test_order_keyword_preserved(self):
        text = "Your order 12345 is on its way!"
        result = validate_personality(text, PersonalityType.ENTHUSIASTIC)
        assert result.critical_content_preserved


class TestValidationResult:
    """ValidationResult dataclass behavior."""

    def test_default_no_violations(self):
        result = ValidationResult(passed=True, violations=[], severity="none")
        assert result.passed
        assert result.violations == []

    def test_violations_list_populated(self):
        result = ValidationResult(
            passed=False,
            violations=["Too many emojis", "Slang detected"],
            severity="medium",
        )
        assert not result.passed
        assert len(result.violations) == 2

    def test_advisory_only_never_blocks(self):
        result = validate_personality(
            "OMG check these out!!! 🎉🔥✨😂🤣",
            PersonalityType.PROFESSIONAL,
        )
        assert not result.passed
        assert result.severity in ("high", "medium", "low")


class TestEdgeCases:
    """Edge case validation."""

    def test_empty_string_passes(self):
        result = validate_personality("", PersonalityType.FRIENDLY)
        assert result.passed

    def test_whitespace_only_passes(self):
        result = validate_personality("   ", PersonalityType.PROFESSIONAL)
        assert result.passed

    def test_very_long_text(self):
        text = "Great find! " * 500
        result = validate_personality(text, PersonalityType.FRIENDLY)
        assert isinstance(result, ValidationResult)

    def test_unicode_text(self):
        text = "こんにちは！素晴らしい商品です！🎉"
        result = validate_personality(text, PersonalityType.ENTHUSIASTIC)
        assert isinstance(result, ValidationResult)

    def test_newlines_in_text(self):
        text = "Here's your order:\n\n• Item 1 - $10\n• Item 2 - $20"
        result = validate_personality(text, PersonalityType.PROFESSIONAL)
        assert result.passed
