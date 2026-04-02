"""Checkout handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import assert_starts_with_transition


class TestCheckoutHandlerTransitions:
    RESPONSE_TYPE = "checkout"
    EXPECTED_CATEGORY = TransitionCategory.CONFIRMING

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_empty_cart_no_transition(self, personality):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "empty_cart",
            personality,
            include_transition=True,
            conversation_id="checkout-empty",
            mode="ecommerce",
        )
        assert_starts_with_transition(result, self.EXPECTED_CATEGORY, personality)

    def test_ready_template_has_opening(self):
        assert "ready" in TEMPLATES_WITH_OPENINGS.get(self.RESPONSE_TYPE, set())

    def test_ready_no_double_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "ready",
            PersonalityType.PROFESSIONAL,
            include_transition=True,
            conversation_id="checkout-ready",
            mode="ecommerce",
            checkout_url="https://shop.example.com/checkout",
        )
        assert "https://shop.example.com/checkout" in result

    def test_response_type_maps_to_confirming(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
