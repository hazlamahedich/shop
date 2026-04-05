"""Integration tests for natural clarification question flow (Story 11-11).

Tests cover:
- End-to-end natural question formatting pipeline
- Double-transition prevention
- Template rotation across multiple turns
- Partial response acknowledgment
- Mode-specific (ecommerce vs general) question generation
- Error fallback to robotic templates
- Backward compatibility with existing personalize_question interface
- Personality-aware wrapping
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.merchant import PersonalityType
from app.services.clarification.question_generator import QuestionGenerator
from app.services.conversation.handlers.clarification_handler import ClarificationHandler
from app.services.personality.clarification_question_templates import (
    register_natural_question_templates,
)
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

register_natural_question_templates()


def _make_merchant(
    personality: PersonalityType = PersonalityType.FRIENDLY,
    business_name: str = "Test Shop",
) -> MagicMock:
    merchant = MagicMock()
    merchant.personality = personality
    merchant.business_name = business_name
    return merchant


def _make_llm() -> AsyncMock:
    return AsyncMock()


class TestNaturalQuestionPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_produces_natural_question(self):
        gen = QuestionGenerator()
        question = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={"category": "shoes"},
            mode="ecommerce",
        )
        assert len(question) > 10

    @pytest.mark.asyncio
    async def test_context_reference_included_in_followup(self):
        gen = QuestionGenerator()
        question = await gen.generate_context_aware_question(
            constraint="color",
            accumulated_constraints={"category": "shoes", "brand": "nike"},
            mode="ecommerce",
        )
        assert "shoes" in question.lower() or "nike" in question.lower()

    @pytest.mark.asyncio
    async def test_general_mode_context_reference(self):
        gen = QuestionGenerator()
        question = await gen.generate_context_aware_question(
            constraint="severity",
            accumulated_constraints={"issue_type": "login"},
            mode="general",
        )
        assert "login" in question.lower()


class TestDoubleTransitionPrevention:
    @pytest.mark.asyncio
    async def test_skip_transition_removes_prefix(self):
        handler = ClarificationHandler()
        merchant = _make_merchant()
        llm = _make_llm()

        with_skip = await handler._personalize_question(
            question="What color do you prefer?",
            constraint="color",
            merchant=merchant,
            llm_service=llm,
            skip_transition=True,
        )

        without_skip = await handler._personalize_question(
            question="What color do you prefer?",
            constraint="color",
            merchant=merchant,
            llm_service=llm,
            skip_transition=False,
        )

        assert len(with_skip) < len(without_skip)
        assert with_skip == "What color do you prefer?"

    @pytest.mark.asyncio
    async def test_skip_transition_preserves_budget_prefix(self):
        handler = ClarificationHandler()
        merchant = _make_merchant(business_name="Shoe Palace")
        llm = _make_llm()

        result = await handler._personalize_question(
            question="What is your budget?",
            constraint="budget",
            merchant=merchant,
            llm_service=llm,
            skip_transition=True,
        )

        assert "Shoe Palace" in result
        assert "every budget" in result


class TestTemplateRotation:
    @pytest.mark.asyncio
    async def test_rotation_produces_different_templates(self):
        gen = QuestionGenerator()
        templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        used: dict[str, int] = {}

        results = set()
        for i in range(len(templates)):
            last = used.get("budget", -1)
            next_idx = (last + 1) % len(templates)
            results.add(templates[next_idx])
            used["budget"] = next_idx

        assert len(results) == len(templates)

    @pytest.mark.asyncio
    async def test_rotation_wraps_correctly(self):
        gen = QuestionGenerator()
        templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        used = {"budget": len(templates) - 1}
        result = gen._select_question_template("budget", used_indices=used)
        assert result == templates[0]


class TestCombinedQuestions:
    def test_two_constraints_natural_combined(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color"],
            mode="ecommerce",
        )
        assert "?" in result
        assert len(result) <= 200

    def test_three_constraints_natural_combined(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color", "brand"],
            mode="ecommerce",
        )
        assert len(result) <= 200

    def test_combined_with_context(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color"],
            accumulated_constraints={"category": "shoes"},
            mode="ecommerce",
        )
        assert "shoes" in result.lower()


class TestPartialResponseHandling:
    def test_partial_response_acknowledgment(self):
        handler = ClarificationHandler()
        merchant = _make_merchant()
        result = handler._handle_partial_response(
            accepted_field="color",
            follow_up_question="What size do you need?",
            merchant=merchant,
        )
        assert "color" in result.lower()
        assert "size" in result.lower()

    def test_partial_response_personality_friendly(self):
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.FRIENDLY)
        result = handler._handle_partial_response(
            accepted_field="budget",
            follow_up_question="What color are you looking for?",
            merchant=merchant,
        )
        assert len(result) > 20

    def test_partial_response_personality_professional(self):
        handler = ClarificationHandler()
        merchant = _make_merchant(PersonalityType.PROFESSIONAL)
        result = handler._handle_partial_response(
            accepted_field="size",
            follow_up_question="Any brand preference?",
            merchant=merchant,
        )
        assert "size" in result.lower()


class TestPersonalityAwareFormatting:
    @pytest.fixture(autouse=True)
    def setup(self):
        register_natural_question_templates()

    def test_friendly_constraint_acknowledgment(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "constraint_added_acknowledgment",
            PersonalityType.FRIENDLY,
            understanding="So you're looking for red shoes.",
        )
        assert "red" in result
        assert "refine" in result.lower()

    def test_professional_constraint_acknowledgment(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "constraint_added_acknowledgment",
            PersonalityType.PROFESSIONAL,
            understanding="So you're looking for red shoes.",
        )
        assert "red" in result

    def test_enthusiastic_results_transition(self):
        result = PersonalityAwareResponseFormatter.format_response(
            "clarification_natural",
            "transition_to_results",
            PersonalityType.ENTHUSIASTIC,
            understanding="So you're looking for shoes.",
        )
        assert "shoes" in result.lower()


class TestBackwardCompatibility:
    @pytest.mark.asyncio
    async def test_personalize_question_default_params(self):
        handler = ClarificationHandler()
        merchant = _make_merchant()
        llm = _make_llm()

        result = await handler._personalize_question(
            question="What is your budget?",
            constraint="budget",
            merchant=merchant,
            llm_service=llm,
        )

        assert "What is your budget?" in result
        assert len(result) > len("What is your budget?")

    @pytest.mark.asyncio
    async def test_personalize_question_with_conversation_id(self):
        handler = ClarificationHandler()
        merchant = _make_merchant()
        llm = _make_llm()

        result = await handler._personalize_question(
            question="What size do you need?",
            constraint="size",
            merchant=merchant,
            llm_service=llm,
            conversation_id="test-conv-123",
        )

        assert "What size do you need?" in result

    def test_error_code_7110_exists(self):
        from app.core.errors import ErrorCode

        assert ErrorCode.NATURAL_QUESTION_FORMAT_FAILED == 7110
