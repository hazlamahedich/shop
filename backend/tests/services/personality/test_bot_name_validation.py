"""Tests for AC5: Bot name only in greeting, not operational responses (Story 5-12).

Validates that bot_name placeholder does not appear in operational
response templates (cart, checkout, product search, order tracking).
"""

from __future__ import annotations

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


@pytest.mark.test_id("5.12-UNIT-010")
@pytest.mark.priority("P0")
class TestNoBotNameInOperationalResponses:
    """Test AC5: Bot name only appears in greetings, not operational responses."""

    def test_cart_messages_do_not_contain_bot_name_placeholder(self) -> None:
        """5.12-UNIT-010a: Cart messages should not reference bot name."""
        for message_key in ["add_success", "view_empty", "remove_success", "clear_success"]:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "cart", message_key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Cart message {message_key} should not have bot_name placeholder"
                    )

    def test_checkout_messages_do_not_contain_bot_name_placeholder(self) -> None:
        """5.12-UNIT-010b: Checkout messages should not reference bot name."""
        for message_key in ["ready", "empty_cart", "fallback", "circuit_open"]:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "checkout", message_key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Checkout message {message_key} should not have bot_name placeholder"
                    )

    def test_product_search_messages_do_not_contain_bot_name_placeholder(self) -> None:
        """5.12-UNIT-010c: Product search messages should not reference bot name."""
        for message_key in [
            "found_single",
            "found_multiple",
            "no_results",
            "fallback",
            "recommendation_single",
            "recommendation_multiple",
        ]:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "product_search", message_key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Product search message {message_key} should not have bot_name placeholder"
                    )
