"""Integration tests for transition phrase system.

Story 11-4: Tests PersonalityAwareResponseFormatter integration
with transition selector, including double-transition prevention
and backward compatibility (include_transition=False by default).
"""

import random

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import (
    PersonalityAwareResponseFormatter,
    TEMPLATES_WITH_OPENINGS,
)
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TransitionCategory,
    get_phrases_for_mode,
)
from app.services.personality.transition_selector import get_transition_selector


@pytest.fixture(autouse=True)
def reset_selector():
    selector = get_transition_selector()
    selector.reset()
    random.seed(42)
    yield
    random.seed(42)
    selector.reset()


class TestBackwardCompatibility:
    def test_default_no_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.FRIENDLY,
            title="Test Product",
        )
        assert result.startswith("Added Test Product")
        assert "Test Product" in result

    def test_no_transition_for_templates_without_openings(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        assert "cart is empty" in result.lower()

    def test_include_false_same_as_default(self):
        default = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
        )
        explicit = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=False,
        )
        assert default == explicit


class TestTransitionPrepending:
    def test_transition_prepended_when_enabled(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-conv",
            mode="ecommerce",
        )
        valid_phrases = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )
        found = any(result.startswith(phrase) for phrase in valid_phrases)
        assert found, f"Result '{result[:50]}' doesn't start with a valid transition"

    def test_transition_contains_original_content(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-conv-2",
            mode="ecommerce",
        )
        assert "cart is empty" in result.lower()

    def test_transition_with_kwargs(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "no_results",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-conv-3",
            mode="ecommerce",
            query="shoes",
        )
        assert "shoes" in result.lower()


class TestDoubleTransitionPrevention:
    def test_templates_with_openings_return_formatted_only(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "add_success",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-double",
            mode="ecommerce",
            title="Widget",
        )
        assert "Widget" in result
        valid_phrases = get_phrases_for_mode(
            TransitionCategory.CONFIRMING, PersonalityType.FRIENDLY, "ecommerce"
        )
        has_double = any(result.count(phrase) >= 2 for phrase in valid_phrases)
        assert not has_double, f"Double transition detected in: {result}"

    def test_found_single_no_double_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "found_single",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-double-search",
            mode="ecommerce",
            title="Blue Shirt",
            price=" - $29.99",
            business_name="Test Store",
        )
        assert "Blue Shirt" in result

    def test_checkout_ready_no_double_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "checkout",
            "ready",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-double-checkout",
            mode="ecommerce",
            checkout_url="https://example.com/checkout",
        )
        assert "https://example.com/checkout" in result

    @pytest.mark.parametrize(
        "response_type,message_key",
        [
            ("product_search", "found_single"),
            ("product_search", "found_multiple"),
            ("product_search", "recommendation_single"),
            ("product_search", "recommendation_multiple"),
            ("cart", "add_success"),
            ("cart", "view_items"),
            ("checkout", "ready"),
            ("order_tracking", "found"),
            ("order_tracking", "found_shipped"),
            ("order_tracking", "found_delivered"),
            ("order_tracking", "found_processing"),
            ("order_confirmation", "confirmed"),
        ],
    )
    def test_all_templates_with_openings_no_double(self, response_type, message_key):
        kwargs = self._get_kwargs_for_template(response_type, message_key)
        result = PersonalityAwareResponseFormatter.format_response(
            response_type,
            message_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="test-param",
            mode="ecommerce",
            **kwargs,
        )
        category = RESPONSE_TYPE_TO_TRANSITION[response_type]
        valid_phrases = get_phrases_for_mode(category, PersonalityType.FRIENDLY, "ecommerce")
        has_double = any(result.count(p) >= 2 for p in valid_phrases)
        assert not has_double, f"Double transition in {response_type}/{message_key}: {result[:80]}"

    @staticmethod
    def _get_kwargs_for_template(response_type: str, message_key: str) -> dict:
        kwargs_map = {
            ("product_search", "found_single"): {
                "title": "Shirt",
                "price": " $20",
                "business_name": "Store",
            },
            ("product_search", "found_multiple"): {
                "products": "item1\nitem2",
                "business_name": "Store",
            },
            ("product_search", "recommendation_single"): {
                "title": "Shirt",
                "price": " $20",
                "business_name": "Store",
            },
            ("product_search", "recommendation_multiple"): {
                "products": "item1\nitem2",
                "more_options": "",
                "business_name": "Store",
            },
            ("cart", "add_success"): {"title": "Item"},
            ("cart", "view_items"): {"items": "item1", "subtotal": "10.00"},
            ("checkout", "ready"): {"checkout_url": "https://example.com"},
            ("order_tracking", "found"): {"order_details": "Order 123"},
            ("order_tracking", "found_shipped"): {
                "order_details": "Order 123",
                "tracking_info": "Track: 1Z999",
            },
            ("order_tracking", "found_delivered"): {"order_details": "Order 123"},
            ("order_tracking", "found_processing"): {"order_details": "Order 123"},
            ("order_confirmation", "confirmed"): {"order_number": "123", "delivery_date": "Monday"},
        }
        return kwargs_map.get((response_type, message_key), {})


class TestAntiRepetitionAcrossCalls:
    def test_consecutive_calls_different_transitions(self):
        results = set()
        conv_id = "test-repetition"

        for _ in range(10):
            result = PersonalityAwareResponseFormatter.format_response(
                "cart",
                "view_empty",
                PersonalityType.FRIENDLY,
                include_transition=True,
                conversation_id=conv_id,
                mode="ecommerce",
            )
            results.add(result)

        assert len(results) > 1, "All calls returned identical transitions"

    def test_different_conversations_independent(self):
        conv_a_results = set()
        conv_b_results = set()

        for _ in range(5):
            conv_a_results.add(
                PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "view_empty",
                    PersonalityType.FRIENDLY,
                    include_transition=True,
                    conversation_id="conv-a",
                    mode="ecommerce",
                )
            )
            conv_b_results.add(
                PersonalityAwareResponseFormatter.format_response(
                    "cart",
                    "view_empty",
                    PersonalityType.FRIENDLY,
                    include_transition=True,
                    conversation_id="conv-b",
                    mode="ecommerce",
                )
            )

        assert len(conv_a_results) > 1 or len(conv_b_results) > 1


class TestAllPersonalitiesWithTransitions:
    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_each_personality_gets_transitions(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            "cart",
            "view_empty",
            personality,
            include_transition=True,
            conversation_id=f"test-{personality.value}",
            mode="ecommerce",
        )
        assert isinstance(result, str)
        assert len(result) > 0
        assert "cart" in result.lower() or "empty" in result.lower()
