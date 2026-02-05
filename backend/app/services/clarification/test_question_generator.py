"""Tests for QuestionGenerator.

Tests cover:
- Priority-based question selection (critical constraints first)
- Template-based question construction
- Context-aware question phrasing (based on questions_asked)
"""

from __future__ import annotations

import pytest

from app.services.clarification.question_generator import QuestionGenerator
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType


@pytest.mark.asyncio
async def test_question_generation_budget_first():
    """Test budget question is asked first (highest priority)."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(
            color="red", brand="nike"
        ),  # Missing budget, category, size
        raw_message="red nike",
        reasoning="Missing constraints",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=[],
    )

    # Budget should be asked first (highest priority)
    assert "budget" in question.lower() or "spend" in question.lower()
    assert constraint == "budget"


@pytest.mark.asyncio
async def test_question_generation_category_second():
    """Test category question is asked second when budget already asked."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(
            budget=100, color="red", brand="nike"
        ),  # Missing category, size
        raw_message="$100 red nike",
        reasoning="Missing category",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=["budget"],
    )

    # Category should be asked next
    assert (
        "type" in question.lower()
        or "category" in question.lower()
        or "looking for" in question.lower()
    )
    assert constraint == "category"


@pytest.mark.asyncio
async def test_question_generation_size_third():
    """Test size question is asked third when budget and category already asked."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(
            budget=100, category="shoes", color="red"
        ),  # Missing size
        raw_message="$100 shoes red",
        reasoning="Missing size",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=["budget", "category"],
    )

    # Size should be asked next
    assert "size" in question.lower()
    assert constraint == "size"


@pytest.mark.asyncio
async def test_question_generation_color_fourth():
    """Test color question is asked fourth when budget, category, size already asked."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(budget=100, category="shoes", size="10"),
        raw_message="$100 shoes size 10",
        reasoning="Missing color",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=["budget", "category", "size"],
    )

    # Color should be asked next
    assert "color" in question.lower()
    assert constraint == "color"


@pytest.mark.asyncio
async def test_question_generation_brand_fifth():
    """Test brand question is asked last (lowest priority)."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(budget=100, category="shoes", size="10", color="red"),
        raw_message="$100 shoes size 10 red",
        reasoning="Missing brand",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=["budget", "category", "size", "color"],
    )

    # Brand should be asked next
    assert "brand" in question.lower()
    assert constraint == "brand"


@pytest.mark.asyncio
async def test_question_generation_skips_already_asked():
    """Test question generation skips constraints already asked about."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red"),  # Missing budget, category, size, brand
        raw_message="red",
        reasoning="Missing constraints",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    # Budget was already asked, should skip to category
    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=["budget"],
    )

    # Should ask about category, not budget
    assert "budget" not in question.lower()
    assert (
        "type" in question.lower()
        or "category" in question.lower()
        or "looking for" in question.lower()
    )
    assert constraint == "category"


@pytest.mark.asyncio
async def test_question_generation_no_missing_constraints():
    """Test error raised when no constraints are missing."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(
            budget=100, category="shoes", size="10", color="red", brand="nike"
        ),  # All constraints present
        raw_message="$100 nike shoes size 10 red",
        reasoning="All constraints present",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with pytest.raises(ValueError, match="No more questions to ask"):
        await generator.generate_next_question(
            classification=classification,
            questions_asked=[],
        )


@pytest.mark.asyncio
async def test_question_generation_all_constraints_asked():
    """Test error raised when all questions have been asked."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red"),  # Still missing constraints
        raw_message="red",
        reasoning="Missing constraints",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    # All questions already asked
    with pytest.raises(ValueError, match="No more questions to ask"):
        await generator.generate_next_question(
            classification=classification,
            questions_asked=["budget", "category", "size", "color", "brand"],
        )


@pytest.mark.asyncio
async def test_question_priority_order():
    """Test QUESTION_PRIORITY follows correct order."""
    expected_order = ["budget", "category", "size", "color", "brand"]
    assert QuestionGenerator.QUESTION_PRIORITY == expected_order


@pytest.mark.asyncio
async def test_question_templates_exist_for_all_constraints():
    """Test question templates exist for all priority constraints."""
    generator = QuestionGenerator()

    for constraint in QuestionGenerator.QUESTION_PRIORITY:
        templates = generator.QUESTION_TEMPLATES.get(constraint, [])
        assert len(templates) > 0, f"No templates for {constraint}"
        assert all(isinstance(t, str) for t in templates), f"Invalid template for {constraint}"


@pytest.mark.asyncio
async def test_question_generation_uses_first_template():
    """Test question generation uses first template by default."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(category="shoes"),  # Missing budget
        raw_message="shoes",
        reasoning="Missing budget",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    question, constraint = await generator.generate_next_question(
        classification=classification,
        questions_asked=[],
    )

    # Should use first budget template
    assert question == QuestionGenerator.QUESTION_TEMPLATES["budget"][0]
    assert constraint == "budget"
