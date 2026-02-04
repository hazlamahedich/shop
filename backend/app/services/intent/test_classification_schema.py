"""Tests for classification schema.

Unit tests for Pydantic validation and camelCase conversion.
"""

from __future__ import annotations

import pytest

from app.services.intent import ClassificationResult, ExtractedEntities, IntentType


def test_extracted_entities_validation():
    """Test ExtractedEntities schema validation."""
    entities = ExtractedEntities(
        category="shoes",
        budget=100.0,
        size="8",
        color="red",
        brand="Nike",
        constraints={"type": "running"},
    )

    assert entities.category == "shoes"
    assert entities.budget == 100.0
    assert entities.budget_currency == "USD"
    assert entities.size == "8"
    assert entities.color == "red"
    assert entities.brand == "Nike"
    assert entities.constraints == {"type": "running"}


def test_extracted_entities_optional_fields():
    """Test ExtractedEntities with optional fields."""
    entities = ExtractedEntities()

    assert entities.category is None
    assert entities.budget is None
    assert entities.budget_currency == "USD"  # Default value
    assert entities.size is None
    assert entities.color is None
    assert entities.brand is None
    assert entities.constraints == {}


def test_extracted_entities_camel_case_alias():
    """Test ExtractedEntities camelCase API alias."""
    entities = ExtractedEntities(
        category="shoes",
        budget=100.0,
    )

    # Test model_dump with camelCase
    data = entities.model_dump(by_alias=True, exclude_none=True)
    assert "category" in data
    assert "budget" in data
    assert "budgetCurrency" in data


def test_classification_result_validation():
    """Test ClassificationResult schema validation."""
    entities = ExtractedEntities(category="shoes", budget=100.0)
    result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=entities,
        raw_message="running shoes under $100",
        reasoning="Clear product search",
        llm_provider="ollama",
        model="llama3",
        processing_time_ms=150.5,
    )

    assert result.intent == IntentType.PRODUCT_SEARCH
    assert result.confidence == 0.95
    assert result.entities.category == "shoes"
    assert result.raw_message == "running shoes under $100"
    assert result.reasoning == "Clear product search"
    assert result.llm_provider == "ollama"
    assert result.model == "llama3"
    assert result.processing_time_ms == 150.5


def test_classification_result_confidence_validation():
    """Test confidence range validation."""
    entities = ExtractedEntities()

    # Valid confidence values
    ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.0,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=0,
    )

    ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=1.0,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=0,
    )

    # Invalid confidence values should raise validation error
    with pytest.raises(Exception):
        ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=1.5,  # Invalid: > 1.0
            entities=entities,
            raw_message="test",
            llm_provider="test",
            model="test",
            processing_time_ms=0,
        )


def test_needs_clarification_property():
    """Test needs_clarification property."""
    entities = ExtractedEntities()

    # High confidence - no clarification needed
    result_high = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=0,
    )
    assert result_high.needs_clarification is False

    # Exactly at threshold - no clarification needed
    result_threshold = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.80,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=0,
    )
    assert result_threshold.needs_clarification is False

    # Below threshold - clarification needed
    result_low = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.75,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=0,
    )
    assert result_low.needs_clarification is True


def test_intent_type_enum():
    """Test IntentType enum values."""
    assert IntentType.PRODUCT_SEARCH.value == "product_search"
    assert IntentType.GREETING.value == "greeting"
    assert IntentType.CLARIFICATION.value == "clarification"
    assert IntentType.CART_VIEW.value == "cart_view"
    assert IntentType.CART_ADD.value == "cart_add"
    assert IntentType.CHECKOUT.value == "checkout"
    assert IntentType.ORDER_TRACKING.value == "order_tracking"
    assert IntentType.HUMAN_HANDOFF.value == "human_handoff"
    assert IntentType.UNKNOWN.value == "unknown"


def test_classification_result_camel_case_alias():
    """Test ClassificationResult camelCase API alias."""
    entities = ExtractedEntities(category="shoes")
    result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=entities,
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=100,
    )

    # Test model_dump with camelCase
    data = result.model_dump(by_alias=True, exclude_none=True)
    assert "intent" in data
    assert "confidence" in data
    assert "entities" in data
    assert "rawMessage" in data
    assert "llmProvider" in data
    assert "processingTimeMs" in data


def test_multiple_entity_types():
    """Test entities with multiple fields."""
    entities = ExtractedEntities(
        category="electronics",
        budget=500.0,
        size="M",
        color="black",
        brand="Apple",
        constraints={"condition": "new", "storage": "256GB"},
    )

    assert entities.category == "electronics"
    assert entities.budget == 500.0
    assert entities.size == "M"
    assert entities.color == "black"
    assert entities.brand == "Apple"
    assert entities.constraints == {"condition": "new", "storage": "256GB"}
