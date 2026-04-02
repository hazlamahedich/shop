"""Error handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.personality.transition_phrases import (
    TEMPLATES_WITH_OPENINGS,
    TransitionCategory,
)
from tests.unit.helpers.transition_assertions import assert_starts_with_transition


class TestErrorHandlerTransitions:
    RESPONSE_TYPE = "error"
    EXPECTED_CATEGORY = TransitionCategory.ACKNOWLEDGING

    @pytest.mark.parametrize(
        "message_key",
        ["general", "search_failed", "cart_failed", "checkout_failed", "order_lookup_failed"],
    )
    def test_error_templates_get_transition(self, message_key):
        result = PersonalityAwareResponseFormatter.format_response(
            self.RESPONSE_TYPE,
            message_key,
            PersonalityType.FRIENDLY,
            include_transition=True,
            conversation_id=f"error-{message_key}",
            mode="ecommerce",
        )
        assert_starts_with_transition(
            result,
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
        )

    def test_error_has_no_templates_with_openings(self):
        openings = TEMPLATES_WITH_OPENINGS.get(self.RESPONSE_TYPE, set())
        assert len(openings) == 0, "Error templates should not have built-in openings"
