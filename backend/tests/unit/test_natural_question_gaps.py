"""Gap-filling unit tests for Story 11-11 natural clarification questions.

Covers identified coverage gaps:
- G1 (AC1, P1): Negative assertions — output lacks robotic patterns
- G2 (AC2, P2): Combined question capping at 3 constraints
- G3 (AC4, P1): _handle_partial_response unit-level tests
- G4 (AC5, P1): Mode template cross-contamination prevention
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.models.merchant import PersonalityType
from app.services.clarification.question_generator import QuestionGenerator
from app.services.conversation.handlers.clarification_handler import (
    ClarificationHandler,
)
from app.services.personality.clarification_question_templates import (
    register_natural_question_templates,
)

register_natural_question_templates()

ROBOTIC_PATTERNS = [
    "Please specify your",
    "Required:",
    "Provide input for",
    "Missing parameter:",
    "Enter value for",
]


class TestG1NoRoboticPatterns:
    """G1 (AC1, P1): Verify generated questions contain NO robotic patterns."""

    @pytest.mark.asyncio
    async def test_ecommerce_question_no_robotic_patterns(self):
        for constraint in QuestionGenerator.QUESTION_PRIORITY:
            templates = QuestionGenerator.QUESTION_TEMPLATES[constraint]
            for template in templates:
                for pattern in ROBOTIC_PATTERNS:
                    assert (
                        pattern.lower() not in template.lower()
                    ), f"Robotic '{pattern}' in {constraint}: {template}"

    @pytest.mark.asyncio
    async def test_general_question_no_robotic_patterns(self):
        for constraint in QuestionGenerator.GENERAL_QUESTION_PRIORITY:
            templates = QuestionGenerator.GENERAL_MODE_TEMPLATES[constraint]
            for template in templates:
                for pattern in ROBOTIC_PATTERNS:
                    assert (
                        pattern.lower() not in template.lower()
                    ), f"Robotic '{pattern}' in general {constraint}: {template}"

    @pytest.mark.asyncio
    async def test_context_aware_output_no_robotic_patterns(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={"category": "shoes"},
            mode="ecommerce",
        )
        for pattern in ROBOTIC_PATTERNS:
            assert (
                pattern.lower() not in result.lower()
            ), f"Robotic '{pattern}' in context-aware: {result}"

    def test_combined_question_no_robotic_patterns(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color", "brand"],
            mode="ecommerce",
        )
        for pattern in ROBOTIC_PATTERNS:
            assert (
                pattern.lower() not in result.lower()
            ), f"Robotic '{pattern}' in combined: {result}"


class TestG2ConstraintCapping:
    """G2 (AC2, P2): Combined question capping — more than 3 constraints."""

    def test_four_constraints_capped_to_three_names(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["budget", "category", "size", "color"],
            mode="ecommerce",
        )
        assert len(result) <= 200
        assert "?" in result
        assert "color" not in result.lower()

    def test_five_constraints_capped_to_three_names(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["budget", "category", "size", "color", "brand"],
            mode="ecommerce",
        )
        assert len(result) <= 200
        assert "?" in result
        assert "color" not in result.lower()
        assert "brand" not in result.lower()

    def test_many_constraints_does_not_crash(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["budget", "category", "size", "color", "brand", "material"],
            mode="ecommerce",
        )
        assert len(result) > 0
        assert result.endswith("?") or result.endswith("...")
        assert len(result) <= 200


class TestG3PartialResponseUnit:
    """G3 (AC4, P1): Unit-level tests for _handle_partial_response."""

    def _make_merchant(self, personality: PersonalityType = PersonalityType.FRIENDLY) -> MagicMock:
        merchant = MagicMock()
        merchant.personality = personality
        merchant.business_name = "Test Shop"
        return merchant

    def test_friendly_partial_response(self):
        handler = ClarificationHandler()
        merchant = self._make_merchant(PersonalityType.FRIENDLY)
        result = handler._handle_partial_response(
            accepted_field="color",
            follow_up_question="What size do you need?",
            merchant=merchant,
        )
        assert "color" in result.lower()
        assert "size" in result.lower()

    def test_professional_partial_response(self):
        handler = ClarificationHandler()
        merchant = self._make_merchant(PersonalityType.PROFESSIONAL)
        result = handler._handle_partial_response(
            accepted_field="budget",
            follow_up_question="What brand do you prefer?",
            merchant=merchant,
        )
        assert "budget" in result.lower()
        assert "brand" in result.lower()

    def test_enthusiastic_partial_response(self):
        handler = ClarificationHandler()
        merchant = self._make_merchant(PersonalityType.ENTHUSIASTIC)
        result = handler._handle_partial_response(
            accepted_field="size",
            follow_up_question="Any color preference?",
            merchant=merchant,
        )
        assert "size" in result.lower()
        assert "color" in result.lower()

    def test_fallback_on_missing_personality(self):
        handler = ClarificationHandler()
        merchant = MagicMock()
        merchant.personality = None
        merchant.business_name = "Test Shop"
        result = handler._handle_partial_response(
            accepted_field="brand",
            follow_up_question="What is your budget?",
            merchant=merchant,
        )
        assert "brand" in result.lower()
        assert len(result) > 10

    def test_fallback_on_formatter_exception(self):
        handler = ClarificationHandler()
        merchant = self._make_merchant()
        result = handler._handle_partial_response(
            accepted_field="unknown_field_xyz",
            follow_up_question="Tell me more?",
            merchant=merchant,
        )
        assert len(result) > 0


class TestG4ModeCrossContamination:
    """G4 (AC5, P1): Verify ecommerce and general modes use separate templates."""

    @pytest.mark.asyncio
    async def test_ecommerce_mode_does_not_use_general_templates(self):
        for constraint in QuestionGenerator.QUESTION_PRIORITY:
            assert (
                constraint not in QuestionGenerator.GENERAL_MODE_TEMPLATES
            ), f"Ecommerce constraint '{constraint}' found in general templates"

    @pytest.mark.asyncio
    async def test_general_mode_does_not_use_ecommerce_templates(self):
        for constraint in QuestionGenerator.GENERAL_QUESTION_PRIORITY:
            assert (
                constraint not in QuestionGenerator.QUESTION_TEMPLATES
            ), f"General constraint '{constraint}' found in ecommerce templates"

    @pytest.mark.asyncio
    async def test_ecommerce_question_uses_ecommerce_templates(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={},
            mode="ecommerce",
        )
        ecommerce_templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        assert result.rstrip("?.! ") in [t.rstrip("?.! ") for t in ecommerce_templates]

    @pytest.mark.asyncio
    async def test_general_question_uses_general_templates(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="severity",
            accumulated_constraints={},
            mode="general",
        )
        general_templates = QuestionGenerator.GENERAL_MODE_TEMPLATES["severity"]
        assert result.rstrip("?.! ") in [t.rstrip("?.! ") for t in general_templates]

    def test_display_name_ecommerce_vs_general(self):
        gen = QuestionGenerator()
        budget_name = gen._get_display_name("budget", "ecommerce")
        severity_name = gen._get_display_name("severity", "general")
        assert budget_name != severity_name
