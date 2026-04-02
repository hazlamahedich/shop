"""Order confirmation handler transition tests (Story 11-4)."""

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    RESPONSE_TYPE_TO_TRANSITION,
    TEMPLATES_WITH_OPENINGS,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import assert_no_double_transition


class TestOrderConfirmationTransitions:
    RESPONSE_TYPE = "order_confirmation"
    EXPECTED_CATEGORY = TransitionCategory.CONFIRMING

    def test_confirmed_template_has_opening(self):
        assert "confirmed" in TEMPLATES_WITH_OPENINGS.get(self.RESPONSE_TYPE, set())

    def test_confirmed_no_double_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            "confirmed",
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id="confirm-double",
            mode="ecommerce",
            order_number="#123",
            delivery_date="Friday",
        )
        assert_no_double_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )
        assert "#123" in result

    def test_response_type_maps_to_confirming(self):
        assert RESPONSE_TYPE_TO_TRANSITION[self.RESPONSE_TYPE] == self.EXPECTED_CATEGORY
