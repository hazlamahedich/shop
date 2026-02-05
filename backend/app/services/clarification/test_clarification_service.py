"""Tests for ClarificationService.

Tests cover:
- Confidence threshold checking (< 0.80 triggers clarification)
- Missing constraint detection (budget, size, category, color, brand)
- Fallback to assumptions after max attempts
- Assumption message generation
"""

from __future__ import annotations

import pytest

from app.services.clarification.clarification_service import ClarificationService
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType


@pytest.mark.asyncio
async def test_needs_clarification_low_confidence():
    """Test clarification triggered by low confidence score (< 0.80)."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.75,  # Below threshold
        entities=ExtractedEntities(budget=100, category="shoes"),
        raw_message="I want shoes",
        reasoning="Low confidence",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    needs_clarification = await service.needs_clarification(
        classification=classification,
        context={},
    )

    assert needs_clarification is True


@pytest.mark.asyncio
async def test_needs_clarification_missing_budget():
    """Test clarification triggered by missing critical budget constraint."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.85,  # Above threshold
        entities=ExtractedEntities(category="shoes"),  # Missing budget
        raw_message="I want shoes",
        reasoning="Missing budget",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    needs_clarification = await service.needs_clarification(
        classification=classification,
        context={},
    )

    assert needs_clarification is True


@pytest.mark.asyncio
async def test_needs_clarification_missing_category():
    """Test clarification triggered by missing critical category constraint."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.85,  # Above threshold
        entities=ExtractedEntities(budget=100),  # Missing category
        raw_message="I want something for $100",
        reasoning="Missing category",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    needs_clarification = await service.needs_clarification(
        classification=classification,
        context={},
    )

    assert needs_clarification is True


@pytest.mark.asyncio
async def test_no_clarification_needed_high_confidence():
    """Test no clarification when confidence is high and constraints present."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(budget=100, category="shoes"),
        raw_message="I want shoes for $100",
        reasoning="High confidence",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    needs_clarification = await service.needs_clarification(
        classification=classification,
        context={},
    )

    assert needs_clarification is False


@pytest.mark.asyncio
async def test_no_clarification_for_non_product_search():
    """Test clarification not triggered for non-product-search intents."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.GREETING,
        confidence=0.50,  # Low confidence but not product search
        entities=ExtractedEntities(),
        raw_message="hi",
        reasoning="Greeting",
        llm_provider="test",
        model="test-model",
        processing_time_ms=50,
    )

    needs_clarification = await service.needs_clarification(
        classification=classification,
        context={},
    )

    assert needs_clarification is False


@pytest.mark.asyncio
async def test_fallback_to_assumptions_after_max_attempts():
    """Test fallback to assumptions after max 3 attempts."""
    service = ClarificationService()

    context = {
        "clarification": {
            "active": True,
            "attempt_count": 3,  # Max attempts reached
            "questions_asked": ["budget", "category", "size"],
        }
    }

    should_fallback = await service.should_fallback_to_assumptions(context)

    assert should_fallback is True


@pytest.mark.asyncio
async def test_no_fallback_before_max_attempts():
    """Test no fallback before max 3 attempts."""
    service = ClarificationService()

    context = {
        "clarification": {
            "active": True,
            "attempt_count": 2,  # Below max
            "questions_asked": ["budget", "category"],
        }
    }

    should_fallback = await service.should_fallback_to_assumptions(context)

    assert should_fallback is False


@pytest.mark.asyncio
async def test_no_fallback_when_no_clarification_state():
    """Test no fallback when clarification state is missing."""
    service = ClarificationService()

    context = {}  # No clarification state

    should_fallback = await service.should_fallback_to_assumptions(context)

    assert should_fallback is False


@pytest.mark.asyncio
async def test_assumption_message_generation_with_category():
    """Test generation of assumption message with category."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.70,
        entities=ExtractedEntities(category="shoes"),  # Missing budget
        raw_message="shoes",
        reasoning="Missing budget",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    message, assumed = await service.generate_assumption_message(
        classification=classification,
        context={},
    )

    assert "shoes" in message.lower() or "options" in message.lower()
    assert assumed["budget"] is None


@pytest.mark.asyncio
async def test_assumption_message_generation_without_category():
    """Test generation of assumption message without category."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.70,
        entities=ExtractedEntities(),  # Missing both budget and category
        raw_message="something",
        reasoning="Missing constraints",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    message, assumed = await service.generate_assumption_message(
        classification=classification,
        context={},
    )

    # Should use generic term "items" when no category
    assert "items" in message.lower() or "options" in message.lower()
    assert assumed["budget"] is None


@pytest.mark.asyncio
async def test_assumption_message_includes_adjustment_hint():
    """Test assumption message includes suggestion to adjust preferences."""
    service = ClarificationService()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.70,
        entities=ExtractedEntities(category="shoes"),
        raw_message="shoes",
        reasoning="Missing budget",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    message, assumed = await service.generate_assumption_message(
        classification=classification,
        context={},
    )

    # Should mention ability to adjust
    assert "adjust" in message.lower() or "let me know" in message.lower()


@pytest.mark.asyncio
async def test_confidence_threshold_constant():
    """Test CONFIDENCE_THRESHOLD is set to 0.80."""
    assert ClarificationService.CONFIDENCE_THRESHOLD == 0.80


@pytest.mark.asyncio
async def test_max_attempts_constant():
    """Test MAX_CLARIFICATION_ATTEMPTS is set to 3."""
    assert ClarificationService.MAX_CLARIFICATION_ATTEMPTS == 3
