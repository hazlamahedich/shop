"""Story 2-1: Natural Language Intent Classification - Edge Case Tests.

Comprehensive edge case tests for intent classification covering:
- Varied phrasing patterns
- Multi-constraint scenarios
- Budget extraction edge cases
- Ambiguity detection
- Conversation context integration
- Performance requirements (<1 second response time)
"""

from __future__ import annotations

import json
import pytest
import time
from unittest.mock import AsyncMock, patch

from app.services.intent import IntentClassifier, IntentType
from app.services.intent.classification_schema import ClassificationResult, ExtractedEntities


@pytest.mark.asyncio
async def test_varied_phrasing_product_search():
    """Test classification handles varied phrasing for same intent.

    Acceptance Criteria: "system supports varied phrasing:
    'I need marathon training shoes' or 'running shoes budget 100'"
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        # Test varied phrasings that should all classify as product_search
        test_phrases = [
            "I need marathon training shoes",
            "running shoes budget 100",
            "looking for some running shoes",
            "show me shoes for running",
            "I want running shoes",
            "need shoes for marathon training",
        ]

        results = []
        for phrase in test_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "product_search",
                "confidence": 0.90,
                "entities": {"category": "shoes", "constraints": {"type": "running"}},
                "reasoning": "Product search for running shoes"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)
            results.append(result)

        # All should classify as product_search with high confidence
        for result in results:
            assert result.intent == IntentType.PRODUCT_SEARCH
            assert result.confidence >= 0.80
            assert result.entities.category == "shoes"


@pytest.mark.asyncio
async def test_multi_constraint_extraction():
    """Test extraction of multiple constraints simultaneously.

    Tests: budget + size + category + color constraints
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.92,
            "entities": {
                "category": "shoes",
                "budget": 150.0,
                "size": "9",
                "color": "red",
                "brand": "Nike"
            },
            "reasoning": "Product search with multiple constraints"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)
        result = await classifier.classify("red Nike running shoes size 9 under $150")

        assert result.intent == IntentType.PRODUCT_SEARCH
        assert result.entities.category == "shoes"
        assert result.entities.budget == 150.0
        assert result.entities.size == "9"
        assert result.entities.color == "red"
        assert result.entities.brand == "Nike"


@pytest.mark.asyncio
async def test_budget_extraction_variations():
    """Test budget extraction with various phrasing formats.

    Tests: "$100", "under 100", "100 dollars", "budget 100", "< 100"
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        budget_phrases = [
            ("shoes under $100", 100.0),
            ("shoes under 100", 100.0),
            ("shoes budget 100 dollars", 100.0),
            ("shoes max 100", 100.0),
            ("shoes less than 100", 100.0),
            ("shoes around $50", 50.0),
        ]

        for phrase, expected_budget in budget_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "product_search",
                "confidence": 0.90,
                "entities": {"category": "shoes", "budget": expected_budget},
                "reasoning": "Product search with budget"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.intent == IntentType.PRODUCT_SEARCH
            assert result.entities.budget == expected_budget


@pytest.mark.asyncio
async def test_ambiguity_detection_low_confidence():
    """Test ambiguity detection triggers clarification threshold.

    Acceptance Criteria: "if confidence < 0.80, bot triggers clarification flow"
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        # Low confidence should trigger clarification
        mock_response.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.65,
            "entities": {"category": None},
            "reasoning": "Vague request, unclear category"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)
        result = await classifier.classify("I want something")

        # Should have low confidence triggering clarification
        assert result.confidence < 0.80
        assert result.needs_clarification is True


@pytest.mark.asyncio
async def test_conversation_context_clarification_flow():
    """Test conversation context improves classification in clarification flow.

    Tests Story 2.4 interaction where context from previous messages
    helps clarify ambiguous follow-up.
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        # First message establishes context
        mock_response1 = AsyncMock()
        mock_response1.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.90,
            "entities": {"category": "shoes"},
            "reasoning": "Product search for shoes"
        })
        mock_response1.provider = "test"
        mock_response1.model = "test-model"

        # Second message (ambiguous) uses context
        mock_response2 = AsyncMock()
        mock_response2.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.88,
            "entities": {"category": "shoes", "size": "8"},
            "reasoning": "Using context: clarifying size for shoes"
        })
        mock_response2.provider = "test"
        mock_response2.model = "test-model"

        mock_router.chat.side_effect = [mock_response1, mock_response2]

        classifier = IntentClassifier(llm_router=mock_router)

        # First message
        result1 = await classifier.classify("I need running shoes")

        # Second message with context
        context = {
            "previous_intent": "product_search",
            "extracted_entities": {"category": "shoes"},
            "missing_constraints": ["size"]
        }
        result2 = await classifier.classify("size 8", conversation_context=context)

        # Second classification should have higher confidence with context
        assert result2.intent == IntentType.PRODUCT_SEARCH
        assert result2.entities.size == "8"
        assert result2.confidence >= 0.80  # Above threshold due to context


@pytest.mark.asyncio
async def test_response_time_under_one_second():
    """Test classification response time is under 1 second.

    Acceptance Criteria: "response time from message to classification is < 1 second"
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.95,
            "entities": {"category": "shoes", "budget": 100.0},
            "reasoning": "Clear product search"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)

        start_time = time.time()
        result = await classifier.classify("running shoes under $100")
        end_time = time.time()

        processing_time = end_time - start_time

        assert result.intent == IntentType.PRODUCT_SEARCH
        assert processing_time < 1.0, f"Response time {processing_time}s exceeds 1 second requirement"
        # Verify processing_time_ms is recorded
        assert result.processing_time_ms > 0


@pytest.mark.asyncio
async def test_all_intents_classifiable():
    """Test all supported intent types can be classified.

    Ensures IntentType enum covers all major shopping scenarios.
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        intent_examples = [
            ("running shoes under $100", "product_search"),
            ("Hi there", "greeting"),
            ("Show me my cart", "cart_view"),
            ("I want to buy these", "checkout"),
            ("Where's my order", "order_tracking"),
            ("Talk to a human", "human_handoff"),
            ("size 8", "clarification"),  # Follow-up clarification
        ]

        for phrase, expected_intent in intent_examples:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": expected_intent,
                "confidence": 0.90,
                "entities": {},
                "reasoning": f"Classified as {expected_intent}"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.intent.value == expected_intent


@pytest.mark.asyncio
async def test_unknown_intent_fallback():
    """Test classification returns UNKNOWN for truly unclassifiable input.

    Tests: gibberish, completely unrelated topics, malicious input patterns
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = json.dumps({
            "intent": "unknown",
            "confidence": 0.30,
            "entities": {},
            "reasoning": "Unable to classify, input is unclear"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)
        result = await classifier.classify("asdfghjkl qwerty")

        assert result.intent == IntentType.UNKNOWN
        assert result.confidence < 0.50
        assert result.needs_clarification is True


@pytest.mark.asyncio
async def test_constraints_dictionary_extraction():
    """Test extraction of arbitrary constraint key-value pairs.

    Tests: constraints field can store various non-standard attributes
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.91,
            "entities": {
                "category": "shoes",
                "constraints": {
                    "type": "running",
                    "usage": "marathon",
                    "terrain": "road"
                }
            },
            "reasoning": "Product search with multiple constraint types"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)
        result = await classifier.classify("marathon running shoes for road")

        assert result.intent == IntentType.PRODUCT_SEARCH
        assert result.entities.constraints["type"] == "running"
        assert result.entities.constraints["usage"] == "marathon"
        assert result.entities.constraints["terrain"] == "road"


@pytest.mark.asyncio
async def test_human_handoff_keywords():
    """Test classification detects human handoff intent keywords.

    Acceptance Criteria references: Story 4.5 human assistance detection
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        handoff_phrases = [
            "talk to a person",
            "I need a human",
            "customer service",
            "real person please",
            "agent",
            "human assistance",
        ]

        for phrase in handoff_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "human_handoff",
                "confidence": 0.95,
                "entities": {},
                "reasoning": "Human handoff request detected"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.intent == IntentType.HUMAN_HANDOFF
            assert result.confidence >= 0.80


@pytest.mark.asyncio
async def test_cart_related_intents():
    """Test classification of cart-related intents.

    Covers: cart_view, cart_add (future), checkout
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        cart_phrases = [
            ("show me my cart", "cart_view"),
            ("what's in my cart", "cart_view"),
            ("view cart", "cart_view"),
            ("I want to checkout", "checkout"),
            ("complete purchase", "checkout"),
            ("buy these now", "checkout"),
        ]

        for phrase, expected_intent in cart_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": expected_intent,
                "confidence": 0.95,
                "entities": {},
                "reasoning": f"Cart-related intent: {expected_intent}"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.intent.value == expected_intent


@pytest.mark.asyncio
async def test_order_tracking_phrases():
    """Test classification of order tracking intent variations.

    Acceptance Criteria: "Where's my order?", "Order status", "Track my order"
    """
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        order_phrases = [
            "Where's my order?",
            "Order status",
            "Track my order",
            "check order status",
            "where is my package",
            "order tracking",
        ]

        for phrase in order_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "order_tracking",
                "confidence": 0.92,
                "entities": {},
                "reasoning": "Order tracking inquiry"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.intent == IntentType.ORDER_TRACKING
            assert result.confidence >= 0.80


@pytest.mark.asyncio
async def test_color_entity_extraction():
    """Test color entity extraction from various phrasing."""
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        color_phrases = [
            ("red shoes", "red"),
            ("blue Nike shoes", "blue"),
            ("shoes in black", "black"),
            ("white running shoes", "white"),
        ]

        for phrase, expected_color in color_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "product_search",
                "confidence": 0.90,
                "entities": {"category": "shoes", "color": expected_color},
                "reasoning": "Product search with color"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.entities.color == expected_color


@pytest.mark.asyncio
async def test_brand_entity_extraction():
    """Test brand entity extraction from various phrasing."""
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        brand_phrases = [
            ("Nike running shoes", "Nike"),
            ("shoes by Adidas", "Adidas"),
            ("New Balance shoes", "New Balance"),
            ("Puma sneakers", "Puma"),
        ]

        for phrase, expected_brand in brand_phrases:
            mock_response = AsyncMock()
            mock_response.content = json.dumps({
                "intent": "product_search",
                "confidence": 0.90,
                "entities": {"category": "shoes", "brand": expected_brand},
                "reasoning": "Product search with brand"
            })
            mock_response.provider = "test"
            mock_response.model = "test-model"
            mock_router.chat.return_value = mock_response

            classifier = IntentClassifier(llm_router=mock_router)
            result = await classifier.classify(phrase)

            assert result.entities.brand == expected_brand


@pytest.mark.asyncio
async def test_context_formatting_empty_context():
    """Test _format_context handles empty/None values gracefully."""
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = json.dumps({
            "intent": "product_search",
            "confidence": 0.90,
            "entities": {"category": "shoes"},
            "reasoning": "Product search"
        })
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)

        # Empty context
        result = await classifier.classify("shoes", conversation_context={})
        assert result.intent == IntentType.PRODUCT_SEARCH

        # None context
        result2 = await classifier.classify("shoes", conversation_context=None)
        assert result2.intent == IntentType.PRODUCT_SEARCH


@pytest.mark.asyncio
async def test_confidence_threshold_boundary():
    """Test behavior at exactly 0.80 confidence threshold boundary.

    Acceptance Criteria: CLARIFICATION_THRESHOLD = 0.80
    """
    # Test exactly at threshold (should NOT trigger clarification)
    result_at_threshold = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.80,
        entities=ExtractedEntities(category="shoes"),
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=100,
    )
    assert result_at_threshold.needs_clarification is False

    # Test just below threshold (should trigger clarification)
    result_below_threshold = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.79,
        entities=ExtractedEntities(category="shoes"),
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=100,
    )
    assert result_below_threshold.needs_clarification is True


@pytest.mark.asyncio
async def test_json_with_trailing_comma_handling():
    """Test parsing handles various JSON formats including edge cases."""
    with patch("app.services.intent.intent_classifier.LLMRouter") as mock_router_class:
        mock_router = AsyncMock()

        # Valid JSON with extra whitespace
        mock_response = AsyncMock()
        mock_response.content = """
        {
            "intent": "product_search",
            "confidence": 0.90,
            "entities": {"category": "shoes"},
            "reasoning": "Product search"
        }
        """
        mock_response.provider = "test"
        mock_response.model = "test-model"
        mock_router.chat.return_value = mock_response

        classifier = IntentClassifier(llm_router=mock_router)
        result = await classifier.classify("shoes")

        assert result.intent == IntentType.PRODUCT_SEARCH


@pytest.mark.asyncio
async def test_classification_result_serialization():
    """Test ClassificationResult can be properly serialized.

    Ensures Pydantic model_dump works for all fields including camelCase.
    """
    result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.92,
        entities=ExtractedEntities(
            category="shoes",
            budget=100.0,
            size="8",
            color="red",
        ),
        raw_message="red Nike running shoes size 8 under $100",
        reasoning="Clear product search with multiple constraints",
        llm_provider="openai",
        model="gpt-4",
        processing_time_ms=150.5,
    )

    # Test model_dump for serialization (uses snake_case internally, camelCase via alias_generator)
    serialized = result.model_dump(exclude_none=True)

    assert serialized["intent"] == "product_search"
    assert serialized["confidence"] == 0.92
    assert serialized["entities"]["category"] == "shoes"
    assert serialized["entities"]["budget"] == 100.0
    assert serialized["entities"]["budget_currency"] == "USD"  # Default currency
    assert serialized["entities"]["size"] == "8"
    assert serialized["entities"]["color"] == "red"
    assert serialized["raw_message"] == "red Nike running shoes size 8 under $100"
    assert serialized["reasoning"] is not None
    assert serialized["llm_provider"] == "openai"
    assert serialized["model"] == "gpt-4"
    assert serialized["processing_time_ms"] == 150.5


@pytest.mark.asyncio
async def test_extracted_entities_optional_fields():
    """Test ExtractedEntities handles all optional fields correctly."""
    # All None
    entities_empty = ExtractedEntities()
    assert entities_empty.category is None
    assert entities_empty.budget is None
    assert entities_empty.size is None
    assert entities_empty.color is None
    assert entities_empty.brand is None
    assert entities_empty.constraints == {}
    assert entities_empty.budget_currency == "USD"  # Default

    # All populated
    entities_full = ExtractedEntities(
        category="electronics",
        budget=500.0,
        size="large",
        color="black",
        brand="Sony",
        constraints={"type": "wireless", "feature": "noise_canceling"}
    )
    assert entities_full.category == "electronics"
    assert entities_full.budget == 500.0
    assert entities_full.size == "large"
    assert entities_full.color == "black"
    assert entities_full.brand == "Sony"
    assert entities_full.constraints["type"] == "wireless"


@pytest.mark.asyncio
async def test_intent_type_enum_coverage():
    """Test IntentType enum covers all required shopping scenarios."""
    # Verify all expected intents are present
    expected_intents = {
        "product_search",
        "greeting",
        "clarification",
        "cart_view",
        "cart_add",
        "checkout",
        "order_tracking",
        "human_handoff",
        "unknown",
    }

    actual_intents = {intent.value for intent in IntentType}

    assert actual_intents == expected_intents
    assert len(IntentType) == 9  # Verify exact count
