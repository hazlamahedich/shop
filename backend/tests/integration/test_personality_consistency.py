"""Integration tests for Story 5-12: Bot Personality Consistency.

Tests that all bot responses use the configured personality consistently
across all handlers and channels.

Acceptance Criteria:
- AC1: All responses use personality
- AC2: Professional = No emojis
- AC3: Friendly = Moderate emojis
- AC4: Enthusiastic = Expressive emojis
- AC5: Bot name only in greeting
- AC6: Channel consistency (Widget, Messenger, Preview)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock
import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter


class TestPersonalityConsistencySearchHandler:
    """Test SearchHandler applies personality to all responses (AC1)."""

    @pytest.mark.asyncio
    async def test_search_handler_friendly_has_emojis(self):
        """AC3: Friendly personality should have moderate emojis in search results."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.FRIENDLY,
            business_name="Test Store",
            products="• Product 1 - $10.00",
        )
        assert "Test Store" in result
        assert any(emoji in result for emoji in ["😊", "👋", "🎉"]), (
            f"Friendly should have emojis, got: {result}"
        )

    @pytest.mark.asyncio
    async def test_search_handler_professional_no_emojis(self):
        """AC2: Professional personality should have NO emojis in search results."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.PROFESSIONAL,
            business_name="Test Store",
            products="• Product 1 - $10.00",
        )
        assert "Test Store" in result
        assert not any(
            emoji in result for emoji in ["😊", "👋", "🎉", "🔥", "✨", "🤔", "💫", "🛒"]
        ), f"Professional should NOT have emojis, got: {result}"

    @pytest.mark.asyncio
    async def test_search_handler_enthusiastic_has_expressive_emojis(self):
        """AC4: Enthusiastic personality should have expressive emojis and exclamations."""
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            PersonalityType.ENTHUSIASTIC,
            business_name="Test Store",
            products="• Product 1 - $10.00",
        )
        assert "Test Store" in result
        assert "!!!" in result or "AMAZING" in result.upper() or "WOW" in result.upper(), (
            f"Enthusiastic should have high energy, got: {result}"
        )
        assert any(emoji in result for emoji in ["🔥", "🎉", "✨", "💫", "💖"]), (
            f"Enthusiastic should have expressive emojis, got: {result}"
        )

    @pytest.mark.asyncio
    async def test_search_handler_no_results_all_personalities(self):
        """AC1: No results message uses personality for all types."""
        for personality in PersonalityType:
            result = PersonalityAwareResponseFormatter.format_response(
                "product_search",
                "no_results",
                personality,
                query="missing item",
            )
            assert "couldn't find" in result.lower() or "unable" in result.lower(), (
                f"Should indicate no results for {personality}, got: {result}"
            )
            if personality == PersonalityType.PROFESSIONAL:
                assert "😊" not in result
                assert "🤔" not in result
            elif personality == PersonalityType.FRIENDLY:
                assert "🤔" in result
            elif personality == PersonalityType.ENTHUSIASTIC:
                assert "😢" in result or "💪" in result


class TestPersonalityConsistencyCartHandler:
    """Test CartHandler applies personality to all responses (AC1)."""

    @pytest.mark.asyncio
    async def test_cart_empty_friendly_has_emoji(self):
        """AC3: Friendly empty cart should have helpful emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        assert "empty" in result.lower()
        assert "😊" in result, f"Friendly empty cart should have emoji, got: {result}"

    @pytest.mark.asyncio
    async def test_cart_empty_professional_no_emoji(self):
        """AC2: Professional empty cart should have no emoji."""
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.PROFESSIONAL,
        )
        assert "empty" in result.lower()
        assert "😊" not in result, f"Professional should NOT have emoji, got: {result}"

    @pytest.mark.asyncio
    async def test_cart_add_success_all_personalities(self):
        """AC1: Cart add success uses personality for all types."""
        test_cases = [
            (
                PersonalityType.FRIENDLY,
                ["Added", "🛒"],
                "Friendly should be casual with emoji",
            ),
            (
                PersonalityType.PROFESSIONAL,
                ["has been added", "proceed to checkout"],
                "Professional should be formal without emoji",
            ),
            (
                PersonalityType.ENTHUSIASTIC,
                ["WOOHOO", "!!!"],
                "Enthusiastic should be excited",
            ),
        ]
        for personality, expected_phrases, description in test_cases:
            result = PersonalityAwareResponseFormatter.format_response(
                "cart",
                "add_success",
                personality,
                title="Test Product",
            )
            for phrase in expected_phrases:
                assert phrase in result, f"{description}, got: {result}"

    @pytest.mark.asyncio
    async def test_cart_remove_success_all_personalities(self):
        """AC1: Cart remove success uses personality for all types."""
        for personality in PersonalityType:
            result = PersonalityAwareResponseFormatter.format_response(
                "cart",
                "remove_success",
                personality,
            )
            assert "removed" in result.lower(), (
                f"Should mention removal for {personality}, got: {result}"
            )
            if personality == PersonalityType.PROFESSIONAL:
                assert "😊" not in result
                assert "🛒" not in result


class TestPersonalityConsistencyCheckoutHandler:
    """Test CheckoutHandler applies personality to all responses (AC1)."""

    @pytest.mark.asyncio
    async def test_checkout_empty_cart_all_personalities(self):
        """AC1: Checkout empty cart uses personality for all types."""
        test_cases = [
            (PersonalityType.FRIENDLY, "😊"),
            (PersonalityType.PROFESSIONAL, None),
            (PersonalityType.ENTHUSIASTIC, "AWESOME"),
        ]
        for personality, expected in test_cases:
            result = PersonalityAwareResponseFormatter.format_response(
                "checkout",
                "empty_cart",
                personality,
            )
            assert "empty" in result.lower(), f"Should mention empty cart, got: {result}"
            if expected:
                assert expected in result, f"Should contain '{expected}', got: {result}"

    @pytest.mark.asyncio
    async def test_checkout_ready_all_personalities(self):
        """AC1: Checkout ready uses personality for all types."""
        test_url = "https://example.com/checkout/123"
        friendly_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.FRIENDLY,
            checkout_url=test_url,
        )
        professional_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.PROFESSIONAL,
            checkout_url=test_url,
        )
        enthusiastic_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.ENTHUSIASTIC,
            checkout_url=test_url,
        )
        assert test_url in friendly_result
        assert test_url in professional_result
        assert test_url in enthusiastic_result
        assert "🛒" in friendly_result
        assert "🛒" not in professional_result
        assert "!!!" in enthusiastic_result


class TestPersonalityConsistencyOrderHandler:
    """Test OrderHandler applies personality to all responses (AC1)."""

    @pytest.mark.asyncio
    async def test_order_welcome_back_all_personalities(self):
        """AC1: Order welcome back uses personality for all types."""
        test_name = "Maria"
        friendly = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.FRIENDLY,
            customer_name=test_name,
        )
        professional = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.PROFESSIONAL,
            customer_name=test_name,
        )
        enthusiastic = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "welcome_back",
            PersonalityType.ENTHUSIASTIC,
            customer_name=test_name,
        )
        assert test_name in friendly
        assert test_name in professional
        assert test_name in enthusiastic
        assert "👋" in friendly
        assert "👋" not in professional
        assert "!!!" in enthusiastic or "WELCOME" in enthusiastic.upper()

    @pytest.mark.asyncio
    async def test_order_not_found_all_personalities(self):
        """AC1: Order not found uses personality for all types."""
        friendly = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "not_found",
            PersonalityType.FRIENDLY,
        )
        professional = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "not_found",
            PersonalityType.PROFESSIONAL,
        )
        enthusiastic = PersonalityAwareResponseFormatter.format_response(
            "order_tracking",
            "not_found",
            PersonalityType.ENTHUSIASTIC,
        )
        assert "not" in friendly.lower() or "couldn't" in friendly.lower()
        assert "unable" in professional.lower() or "not" in professional.lower()
        assert "😢" in enthusiastic or "Oh no" in enthusiastic

    @pytest.mark.asyncio
    async def test_order_found_shipped_all_personalities(self):
        """AC1: Order found shipped uses personality for all types."""
        order_details = "Order #1234 - In Transit"
        for personality in PersonalityType:
            result = PersonalityAwareResponseFormatter.format_response(
                "order_tracking",
                "found_shipped",
                personality,
                order_details=order_details,
                tracking_info="Tracking: 1Z999AA10123456784",
            )
            assert order_details in result, f"Should contain order details for {personality}"


class TestPersonalityConsistencyHandoffHandler:
    """Test HandoffHandler applies personality to all responses (AC1)."""

    @pytest.mark.asyncio
    async def test_handoff_standard_all_personalities(self):
        """AC1: Handoff standard uses personality for all types."""
        friendly = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "standard",
            PersonalityType.FRIENDLY,
        )
        professional = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "standard",
            PersonalityType.PROFESSIONAL,
        )
        enthusiastic = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "standard",
            PersonalityType.ENTHUSIASTIC,
        )
        assert "human agent" in friendly.lower()
        assert "human agent" in professional.lower()
        assert "human agent" in enthusiastic.lower()
        assert "😊" in friendly
        assert "😊" not in professional
        assert "✨" in enthusiastic or "SUPER" in enthusiastic.upper()

    @pytest.mark.asyncio
    async def test_handoff_after_hours_all_personalities(self):
        """AC1: Handoff after hours uses personality for all types."""
        business_hours = "9 AM - 5 PM"
        friendly = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "after_hours",
            PersonalityType.FRIENDLY,
            business_hours=business_hours,
        )
        professional = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "after_hours",
            PersonalityType.PROFESSIONAL,
            business_hours=business_hours,
        )
        enthusiastic = PersonalityAwareResponseFormatter.format_response(
            "handoff",
            "after_hours",
            PersonalityType.ENTHUSIASTIC,
            business_hours=business_hours,
        )
        assert business_hours in friendly
        assert business_hours in professional
        assert business_hours in enthusiastic
        assert "😊" in friendly
        assert "😊" not in professional


class TestChannelConsistency:
    """Test AC6: Channel consistency - same personality = same tone across channels."""

    @pytest.mark.parametrize(
        "personality",
        [PersonalityType.FRIENDLY, PersonalityType.PROFESSIONAL, PersonalityType.ENTHUSIASTIC],
    )
    @pytest.mark.asyncio
    async def test_same_personality_same_tone_across_channels(self, personality: PersonalityType):
        """AC6: Same personality should produce same tone regardless of channel."""
        channels = ["widget", "messenger", "preview"]
        results_by_channel = {}
        for channel in channels:
            result = PersonalityAwareResponseFormatter.format_response(
                "cart",
                "add_success",
                personality,
                title="Test Product",
            )
            results_by_channel[channel] = result
        widget_result = results_by_channel["widget"]
        messenger_result = results_by_channel["messenger"]
        preview_result = results_by_channel["preview"]
        assert widget_result == messenger_result == preview_result, (
            f"Same personality should produce identical results across channels. "
            f"Widget: {widget_result}, Messenger: {messenger_result}, Preview: {preview_result}"
        )

    @pytest.mark.asyncio
    async def test_all_handlers_consistent_across_channels(self):
        """AC6: All handlers should be consistent across channels."""
        response_types = ["product_search", "cart", "checkout", "order_tracking", "handoff"]
        channels = ["widget", "messenger", "preview"]
        for response_type in response_types:
            for personality in PersonalityType:
                results = []
                templates = PersonalityAwareResponseFormatter.TEMPLATES.get(response_type, {})
                personality_templates = templates.get(personality, {})
                if len(personality_templates) > 0:
                    first_key = next(iter(personality_templates.keys()))
                    for channel in channels:
                        result = PersonalityAwareResponseFormatter.format_response(
                            response_type,
                            first_key,
                            personality,
                        )
                        results.append(result)
                if len(results) > 1:
                    assert all(r == results[0] for r in results), (
                        f"Response type '{response_type}' inconsistent across channels"
                    )


class TestNoBotNameInOperationalResponses:
    """Test AC5: Bot name only appears in greetings, not operational responses."""

    @pytest.mark.asyncio
    async def test_cart_messages_no_bot_name(self):
        """AC5: Cart messages should not contain bot name."""
        cart_keys = [
            "view_empty",
            "view_items",
            "add_success",
            "add_needs_selection",
            "remove_success",
            "clear_success",
        ]
        for key in cart_keys:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template("cart", key, personality)
                if template:
                    assert "{bot_name}" not in template, (
                        f"Cart message '{key}' should not have bot_name placeholder"
                    )

    @pytest.mark.asyncio
    async def test_checkout_messages_no_bot_name(self):
        """AC5: Checkout messages should not contain bot name."""
        checkout_keys = ["ready", "empty_cart", "fallback", "circuit_open"]
        for key in checkout_keys:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "checkout", key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Checkout message '{key}' should not have bot_name placeholder"
                    )

    @pytest.mark.asyncio
    async def test_product_search_messages_no_bot_name(self):
        """AC5: Product search messages should not contain bot name."""
        search_keys = [
            "found_single",
            "found_multiple",
            "no_results",
            "fallback",
            "recommendation_single",
            "recommendation_multiple",
        ]
        for key in search_keys:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "product_search", key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Product search message '{key}' should not have bot_name placeholder"
                    )

    @pytest.mark.asyncio
    async def test_order_tracking_messages_no_bot_name(self):
        """AC5: Order tracking messages should not contain bot name."""
        order_keys = [
            "not_found",
            "found",
            "found_shipped",
            "found_delivered",
            "found_processing",
        ]
        for key in order_keys:
            for personality in PersonalityType:
                template = PersonalityAwareResponseFormatter._get_template(
                    "order_tracking", key, personality
                )
                if template:
                    assert "{bot_name}" not in template, (
                        f"Order tracking message '{key}' should not have bot_name placeholder"
                    )


class TestErrorHandling:
    """Test error responses apply personality correctly."""

    @pytest.mark.asyncio
    async def test_error_general_all_personalities(self):
        """AC1: Error messages use personality for all types."""
        friendly = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.FRIENDLY,
        )
        professional = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.PROFESSIONAL,
        )
        enthusiastic = PersonalityAwareResponseFormatter.format_response(
            "error",
            "general",
            PersonalityType.ENTHUSIASTIC,
        )
        assert "😅" in friendly
        assert "error" in professional.lower()
        assert "💪" in enthusiastic or "😅" in enthusiastic

    @pytest.mark.asyncio
    async def test_error_search_failed_all_personalities(self):
        """AC1: Search error uses personality for all types."""
        for personality in PersonalityType:
            result = PersonalityAwareResponseFormatter.format_response(
                "error",
                "search_failed",
                personality,
            )
            assert "search" in result.lower() or "try again" in result.lower(), (
                f"Should mention search/try again for {personality}"
            )


class TestAllResponseTypesHaveAllPersonalities:
    """Verify all response types have templates for all three personalities."""

    @pytest.mark.asyncio
    async def test_all_response_types_covered(self):
        """AC1: All response types should have all personality variants."""
        response_types = [
            "product_search",
            "cart",
            "checkout",
            "order_tracking",
            "handoff",
            "error",
            "order_confirmation",
        ]
        for response_type in response_types:
            templates = PersonalityAwareResponseFormatter.TEMPLATES.get(response_type, {})
            for personality in PersonalityType:
                assert personality in templates, (
                    f"Response type '{response_type}' missing personality '{personality}'"
                )
                assert len(templates[personality]) > 0, (
                    f"Response type '{response_type}' has empty templates for '{personality}'"
                )


class TestFullConversationFlow:
    """Test complete conversation flows with each personality (Task 4.1)."""

    @pytest.mark.asyncio
    async def test_friendly_conversation_flow(self):
        """Test complete conversation flow with Friendly personality."""
        personality = PersonalityType.FRIENDLY
        search_result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            personality,
            business_name="Friendly Store",
            products="• Widget A - $10.00",
        )
        cart_result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            personality,
            title="Widget A",
        )
        checkout_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            personality,
            checkout_url="https://example.com/checkout",
        )
        assert "👋" in search_result or "😊" in search_result
        assert "🛒" in cart_result
        assert "🛒" in checkout_result

    @pytest.mark.asyncio
    async def test_professional_conversation_flow(self):
        """Test complete conversation flow with Professional personality."""
        personality = PersonalityType.PROFESSIONAL
        search_result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            personality,
            business_name="Professional Shop",
            products="• Widget A - $10.00",
        )
        cart_result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            personality,
            title="Widget A",
        )
        checkout_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            personality,
            checkout_url="https://example.com/checkout",
        )
        emojis = ["😊", "👋", "🎉", "🔥", "✨", "🤔", "💫", "🛒", "🛍️"]
        assert not any(e in search_result for e in emojis)
        assert not any(e in cart_result for e in emojis)
        assert not any(e in checkout_result for e in emojis)

    @pytest.mark.asyncio
    async def test_enthusiastic_conversation_flow(self):
        """Test complete conversation flow with Enthusiastic personality."""
        personality = PersonalityType.ENTHUSIASTIC
        search_result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_multiple",
            personality,
            business_name="Exciting Store",
            products="• Widget A - $10.00",
        )
        cart_result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            personality,
            title="Widget A",
        )
        checkout_result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            personality,
            checkout_url="https://example.com/checkout",
        )
        assert "!!!" in search_result or "AMAZING" in search_result.upper()
        assert "WOOHOO" in cart_result or "!!!" in cart_result
        assert "!!!" in checkout_result or "LOVE" in checkout_result.upper()
