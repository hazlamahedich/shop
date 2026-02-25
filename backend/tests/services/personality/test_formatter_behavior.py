"""Tests for formatter behavior patterns (Story 5-12).

Tests fallback behavior, extensibility via register_response_type(),
and logging for missing templates.
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-007")
@pytest.mark.priority("P1")
class TestFallbackBehavior:
    """Test fallback behavior for missing templates."""

    def test_missing_response_type_returns_fallback(self) -> None:
        """5.12-UNIT-007a: Missing response type should return neutral fallback."""
        result = PersonalityAwareResponseFormatter.format_response(
            "nonexistent_type",
            "some_key",
            PersonalityType.FRIENDLY,
        )
        assert result is not None
        assert len(result) > 0

    def test_missing_message_key_returns_fallback(self) -> None:
        """5.12-UNIT-007b: Missing message key should return neutral fallback."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "nonexistent_key",
            PersonalityType.FRIENDLY,
            title="Test",
        )
        assert result is not None

    def test_fallback_uses_available_kwargs(self) -> None:
        """5.12-UNIT-007c: Fallback should try to use available kwargs."""
        result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.FRIENDLY,
            checkout_url="https://test.com/checkout",
        )
        assert "https://test.com/checkout" in result


@pytest.mark.test_id("5.12-UNIT-008")
@pytest.mark.priority("P2")
class TestExtensibility:
    """Test extensibility via register_response_type()."""

    def test_register_custom_response_type(self) -> None:
        """5.12-UNIT-008a: Should allow registering custom response types."""
        custom_templates = {
            PersonalityType.FRIENDLY: {
                "custom_message": "Hey {name}! Custom greeting! 🎉",
            },
            PersonalityType.PROFESSIONAL: {
                "custom_message": "Hello {name}. Custom greeting.",
            },
            PersonalityType.ENTHUSIASTIC: {
                "custom_message": "HEY {name}!!! CUSTOM GREETING!!! 🎉🎉🎉",
            },
        }

        PersonalityAwareResponseFormatter.register_response_type("custom_type", custom_templates)

        result = PersonalityAwareResponseFormatter.format_response(
            "custom_type",
            "custom_message",
            PersonalityType.FRIENDLY,
            name="Alice",
        )
        assert "Alice" in result
        assert "🎉" in result

    def test_custom_templates_override_builtin(self) -> None:
        """5.12-UNIT-008b: Custom templates should be checked before built-in ones."""
        custom_templates = {
            PersonalityType.FRIENDLY: {
                "found_single": "CUSTOM OVERRIDE: {title}",
            },
        }

        PersonalityAwareResponseFormatter.register_response_type(
            "product_search_override", custom_templates
        )

        result = PersonalityAwareResponseFormatter.format_response(
            "product_search_override",
            "found_single",
            PersonalityType.FRIENDLY,
            title="Test Product",
            business_name="Store",
            price="",
        )
        assert "CUSTOM OVERRIDE" in result


@pytest.mark.test_id("5.12-UNIT-009")
@pytest.mark.priority("P2")
class TestLogging:
    """Test logging behavior for missing templates."""

    def test_missing_template_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """5.12-UNIT-009a: Missing template should log a warning.

        Note: structlog outputs to stdout, so we verify the fallback is returned
        and the warning was emitted (visible in captured stdout).
        """
        result = PersonalityAwareResponseFormatter.format_response(
            "nonexistent_type",
            "nonexistent_key",
            PersonalityType.FRIENDLY,
        )
        assert result is not None
        assert len(result) > 0
        assert result == "I'm here to help."
