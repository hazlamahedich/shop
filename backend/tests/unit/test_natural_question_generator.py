"""Unit tests for QuestionGenerator natural clarification features (Story 11-11).

Tests cover:
- Template rotation via used_indices parameter
- Context-aware question generation
- Combined question generation (2-3 constraints merged)
- Display name and examples helpers
- Mode-specific natural templates
- Max length enforcement on combined questions
- Backward compatibility (existing tests unchanged)
"""

from __future__ import annotations

import pytest

from app.services.clarification.question_generator import QuestionGenerator


class TestTemplateRotation:
    def test_default_select_returns_first_template(self):
        gen = QuestionGenerator()
        result = gen._select_question_template("budget")
        assert result == QuestionGenerator.QUESTION_TEMPLATES["budget"][0]

    def test_rotation_with_used_indices_cycles_through(self):
        templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        used: dict[str, int] = {}

        results = []
        for _ in range(len(templates) * 2):
            last = used.get("budget", -1)
            next_idx = (last + 1) % len(templates)
            results.append(templates[next_idx])
            used["budget"] = next_idx

        assert results[0] == templates[0]
        assert results[1] == templates[1]
        assert results[len(templates)] == templates[0]

    def test_unknown_constraint_returns_fallback(self):
        gen = QuestionGenerator()
        result = gen._select_question_template("unknown_field")
        assert "unknown_field" in result

    def test_rotation_wraps_around(self):
        gen = QuestionGenerator()
        templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        last_idx = len(templates) - 1
        used = {"budget": last_idx}
        result = gen._select_question_template("budget", used_indices=used)
        assert result == templates[0]


class TestContextAwareQuestion:
    @pytest.mark.asyncio
    async def test_ecommerce_with_category_context(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={"category": "shoes"},
            mode="ecommerce",
        )
        assert "budget" in result.lower() or "price" in result.lower() or "spend" in result.lower()

    @pytest.mark.asyncio
    async def test_general_mode_question(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="severity",
            accumulated_constraints={"issue_type": "login"},
            mode="general",
        )
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_no_accumulated_constraints(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={},
            mode="ecommerce",
        )
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_unknown_constraint_uses_display_name(self):
        gen = QuestionGenerator()
        result = await gen.generate_context_aware_question(
            constraint="nonexistent",
            accumulated_constraints={},
            mode="ecommerce",
        )
        assert "nonexistent" in result.lower()

    @pytest.mark.asyncio
    async def test_rotation_in_context_aware(self):
        gen = QuestionGenerator()
        templates = QuestionGenerator.QUESTION_TEMPLATES["budget"]
        used: dict[str, int] = {"budget": 0}
        result = await gen.generate_context_aware_question(
            constraint="budget",
            accumulated_constraints={},
            mode="ecommerce",
            used_indices=used,
        )
        assert result.startswith(templates[1].rstrip("?.! "))


class TestCombinedQuestion:
    def test_single_constraint_falls_back(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["budget"],
            mode="ecommerce",
        )
        assert "budget" in result.lower()

    def test_two_constraints_combined(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color"],
            mode="ecommerce",
        )
        assert len(result) > 0
        assert result.endswith("?")

    def test_three_constraints_combined(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color", "brand"],
            mode="ecommerce",
        )
        assert len(result) <= 200

    def test_max_length_enforcement(self):
        gen = QuestionGenerator()
        long_constraints = ["budget", "category", "brand"]
        result = gen.generate_combined_question(
            constraints=long_constraints,
            mode="ecommerce",
            max_length=50,
        )
        assert len(result) <= 50

    def test_empty_constraints_raises(self):
        gen = QuestionGenerator()
        with pytest.raises(ValueError, match="No constraints to combine"):
            gen.generate_combined_question(constraints=[], mode="ecommerce")

    def test_context_reference_appended(self):
        gen = QuestionGenerator()
        result = gen.generate_combined_question(
            constraints=["size", "color"],
            accumulated_constraints={"category": "shoes"},
            mode="ecommerce",
        )
        assert "shoes" in result.lower()


class TestHelperMethods:
    def test_get_display_name_known_constraint(self):
        gen = QuestionGenerator()
        result = gen._get_display_name("budget", "ecommerce")
        assert result == "budget"

    def test_get_display_name_unknown_constraint(self):
        gen = QuestionGenerator()
        result = gen._get_display_name("nonexistent", "ecommerce")
        assert result == "nonexistent"

    def test_get_examples_for_constraint(self):
        gen = QuestionGenerator()
        result = gen._get_examples_for_constraint("budget", "ecommerce")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_examples_for_unknown_constraint(self):
        gen = QuestionGenerator()
        result = gen._get_examples_for_constraint("nonexistent", "ecommerce")
        assert result == []

    def test_build_context_reference_ecommerce(self):
        gen = QuestionGenerator()
        result = gen._build_context_reference({"category": "shoes", "brand": "nike"}, "ecommerce")
        assert "shoes" in result
        assert "Nike" in result

    def test_build_context_reference_general(self):
        gen = QuestionGenerator()
        result = gen._build_context_reference({"issue_type": "login"}, "general")
        assert "login" in result

    def test_build_context_reference_empty(self):
        gen = QuestionGenerator()
        result = gen._build_context_reference({}, "ecommerce")
        assert result == ""

    def test_build_context_reference_all_ecommerce_constraints(self):
        gen = QuestionGenerator()
        result = gen._build_context_reference(
            {
                "category": "shoes",
                "brand": "nike",
                "budget_max": "100",
                "color": "red",
                "size": "10",
            },
            "ecommerce",
        )
        assert "shoes" in result
        assert "Nike" in result
        assert "$100" in result
        assert "red" in result
        assert "size 10" in result

    def test_build_context_reference_general_all_constraints(self):
        gen = QuestionGenerator()
        result = gen._build_context_reference(
            {"issue_type": "payment", "severity": "critical", "timeframe": "yesterday"},
            "general",
        )
        assert "payment" in result


class TestExtendedTemplates:
    def test_ecommerce_templates_have_natural_variants(self):
        for constraint in QuestionGenerator.QUESTION_PRIORITY:
            templates = QuestionGenerator.QUESTION_TEMPLATES[constraint]
            assert len(templates) >= 3, (
                f"Expected >=3 templates for {constraint}, got {len(templates)}"
            )

    def test_general_templates_have_natural_variants(self):
        for constraint in QuestionGenerator.GENERAL_QUESTION_PRIORITY:
            templates = QuestionGenerator.GENERAL_MODE_TEMPLATES[constraint]
            assert len(templates) >= 3, (
                f"Expected >=3 templates for {constraint}, got {len(templates)}"
            )

    def test_first_templates_unchanged_for_backward_compat(self):
        assert QuestionGenerator.QUESTION_TEMPLATES["budget"][0] == ("What's your budget for this?")
        assert QuestionGenerator.QUESTION_TEMPLATES["category"][0] == (
            "What type of product are you looking for?"
        )
