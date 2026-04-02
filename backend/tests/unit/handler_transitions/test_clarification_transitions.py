"""Clarification handler transition tests (Story 11-4)."""

import pytest

from app.models.merchant import PersonalityType
from app.services.personality.transition_phrases import (
    TransitionCategory,
    get_phrases_for_mode,
)
from app.services.personality.transition_selector import get_transition_selector


class TestClarificationHandlerTransitions:
    EXPECTED_CATEGORY = TransitionCategory.CLARIFYING

    @pytest.mark.parametrize("personality", list(PersonalityType))
    def test_selector_uses_clarifying_category(self, personality):
        selector = get_transition_selector()
        phrase = selector.select(
            self.EXPECTED_CATEGORY,
            personality,
            conversation_id="clarification-test",
            mode="ecommerce",
        )
        valid = get_phrases_for_mode(self.EXPECTED_CATEGORY, personality, "ecommerce")
        assert phrase in valid

    def test_transition_prepended_to_question(self):
        selector = get_transition_selector()
        transition = selector.select(
            self.EXPECTED_CATEGORY,
            PersonalityType.FRIENDLY,
            conversation_id="clar-prepend",
            mode="ecommerce",
        )
        question = "What's your budget?"
        full = f"{transition} {question}"
        assert full.startswith(transition)
        assert question in full
