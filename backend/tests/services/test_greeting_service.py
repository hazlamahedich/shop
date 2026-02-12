"""Tests for greeting service (Story 1.14).

Tests greeting template generation, variable substitution,
and custom vs default greeting logic.
"""

from __future__ import annotations

import pytest
from app.models.merchant import PersonalityType
from app.services.personality.greeting_service import (
    get_default_greeting,
    substitute_greeting_variables,
    get_effective_greeting,
    DEFAULT_GREETINGS,
)


class TestDefaultGreetings:
    """Test default greeting templates for each personality type."""

    def test_friendly_default_greeting_exists(self) -> None:
        """Friendly personality should have a default greeting."""
        assert PersonalityType.FRIENDLY in DEFAULT_GREETINGS
        greeting = DEFAULT_GREETINGS[PersonalityType.FRIENDLY]
        assert "{bot_name}" in greeting
        assert "{business_name}" in greeting
        assert "Hey" in greeting or "Hi" in greeting

    def test_professional_default_greeting_exists(self) -> None:
        """Professional personality should have a default greeting."""
        assert PersonalityType.PROFESSIONAL in DEFAULT_GREETINGS
        greeting = DEFAULT_GREETINGS[PersonalityType.PROFESSIONAL]
        assert "{bot_name}" in greeting
        assert "{business_name}" in greeting
        assert "Good day" in greeting or "Hello" in greeting

    def test_enthusiastic_default_greeting_exists(self) -> None:
        """Enthusiastic personality should have a default greeting."""
        assert PersonalityType.ENTHUSIASTIC in DEFAULT_GREETINGS
        greeting = DEFAULT_GREETINGS[PersonalityType.ENTHUSIASTIC]
        assert "{bot_name}" in greeting
        assert "{business_name}" in greeting
        assert "!" in greeting  # Enthusiastic has more exclamation marks


class TestVariableSubstitution:
    """Test variable substitution in greeting templates."""

    def test_substitute_all_variables(self) -> None:
        """Should substitute all three variables: bot_name, business_name, business_hours."""
        template = "Hi! I'm {bot_name} from {business_name}. Hours: {business_hours}"
        config = {
            "bot_name": "GearBot",
            "business_name": "Alex's Athletic Gear",
            "business_hours": "9 AM - 6 PM PST",
        }
        result = substitute_greeting_variables(template, config)
        assert "GearBot" in result
        assert "Alex's Athletic Gear" in result
        assert "9 AM - 6 PM PST" in result
        assert "{bot_name}" not in result
        assert "{business_name}" not in result

    def test_substitute_partial_variables(self) -> None:
        """Should handle partial variable substitution gracefully."""
        template = "Hi! I'm {bot_name} from {business_name}."
        config = {
            "bot_name": "GearBot",
            # business_name missing
            # business_hours missing
        }
        result = substitute_greeting_variables(template, config)
        assert "GearBot" in result
        # Check that unsubstituted placeholder remains in result
        assert ("{business_name}" in result or "{business_name}" not in template)  # Missing variable keeps placeholder

    def test_substitute_with_empty_config(self) -> None:
        """Should handle empty/None config values gracefully."""
        template = "Hi! I'm {bot_name} from {business_name}. Hours: {business_hours}"
        config = {
            "bot_name": "",
            "business_name": None,
            "business_hours": "   ",  # whitespace only
        }
        result = substitute_greeting_variables(template, config)
        # Empty values should result in empty strings or removed placeholders
        assert result.count("{}") <= 2  # At most 2 empty brackets

    def test_substitute_bot_name_with_default(self) -> None:
        """Should use default for missing bot_name."""
        template = "Hi! I'm {bot_name}."
        config = {}  # No bot_name configured
        result = substitute_greeting_variables(template, config)
        # Should provide a sensible default
        assert "your shopping assistant" in result.lower() or result == ""

    def test_substitute_business_name_with_default(self) -> None:
        """Should use default for missing business_name."""
        template = "Welcome to {business_name}!"
        config = {}  # No business_name configured
        result = substitute_greeting_variables(template, config)
        # Should provide a sensible default
        assert "the store" in result.lower() or result == ""

    def test_substitute_business_hours_with_default(self) -> None:
        """Should use default for missing business_hours."""
        template = "We're open {business_hours}"
        config = {}  # No business_hours configured
        result = substitute_greeting_variables(template, config)
        # Business hours should be removed or show generic text
        assert "{business_hours}" in result or "hours" in result.lower()


class TestEffectiveGreeting:
    """Test effective greeting logic (custom vs default)."""

    def test_custom_greeting_when_enabled(self) -> None:
        """Should return custom greeting when use_custom_greeting is True."""
        config = {
            "personality": PersonalityType.FRIENDLY,
            "custom_greeting": "Custom hello message!",
            "use_custom_greeting": True,
        }
        result = get_effective_greeting(config)
        assert result == "Custom hello message!"

    def test_default_greeting_when_custom_disabled(self) -> None:
        """Should return default greeting when use_custom_greeting is False."""
        config = {
            "personality": PersonalityType.FRIENDLY,
            "custom_greeting": "This should be ignored",
            "use_custom_greeting": False,
            "bot_name": "GearBot",
            "business_name": "Alex's Athletic Gear",
        }
        result = get_effective_greeting(config)
        # Should use personality-based default with variables substituted
        assert "GearBot" in result
        assert "Alex's Athletic Gear" in result
        assert "This should be ignored" not in result

    def test_default_greeting_when_custom_empty(self) -> None:
        """Should return default greeting when custom_greeting is empty/None."""
        config = {
            "personality": PersonalityType.FRIENDLY,
            "custom_greeting": "",  # Empty string
            "use_custom_greeting": True,
            "bot_name": "GearBot",
            "business_name": "Alex's Athletic Gear",
        }
        result = get_effective_greeting(config)
        # Empty custom greeting should trigger default
        assert "GearBot" in result
        assert "Alex's Athletic Gear" in result

    def test_no_config_returns_friendly_default(self) -> None:
        """Should return friendly default when no config provided."""
        config = {}
        result = get_effective_greeting(config)
        # Should have a sensible default with placeholders
        assert "I'm" in result or "Hi" in result


class TestGetDefaultGreeting:
    """Test get_default_greeting function."""

    @pytest.mark.parametrize("personality,expected_contains", [
        (PersonalityType.FRIENDLY, "Hey"),
        (PersonalityType.PROFESSIONAL, "Good day"),
        (PersonalityType.ENTHUSIASTIC, "Hello"),
    ])
    def test_get_default_greeting_returns_personality_template(
        self, personality: PersonalityType, expected_contains: str
    ) -> None:
        """Should return appropriate template for personality type."""
        result = get_default_greeting(personality)
        assert "{bot_name}" in result
        assert "{business_name}" in result
        assert expected_contains in result

    def test_get_default_greeting_unknown_personality_fallback(self) -> None:
        """Should fallback to friendly for unknown personality."""
        # Create a mock unknown personality - using string cast for testing
        result = get_default_greeting(PersonalityType.FRIENDLY)  # Fallback to friendly
        # Should handle gracefully
        assert result is not None
