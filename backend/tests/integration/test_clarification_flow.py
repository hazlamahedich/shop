"""Integration tests for clarification flow.

Tests cover:
- Low confidence → Clarification → Product search
- Multiple clarification exchanges
- Fallback to assumptions after max attempts
- State management across exchanges
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.clarification import ClarificationService, QuestionGenerator
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.messaging import FacebookWebhookPayload
from app.schemas.shopify import ProductSearchResult


@pytest.mark.asyncio
async def test_clarification_flow_full_cycle():
    """Test full clarification flow from low confidence to product search."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        # First classification: low confidence, no constraints
        mock_classifier = AsyncMock()
        mock_classification_low = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.65,
            entities=ExtractedEntities(),  # No constraints
            raw_message="shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )

        # Second classification: after clarification, high confidence
        mock_classification_high = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.90,
            entities=ExtractedEntities(category="shoes", budget=100),
            raw_message="$100 shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )

        # Return low confidence first, then high confidence
        mock_classifier.classify.side_effect = [mock_classification_low, mock_classification_high]

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            # First call: no active clarification
            # Second call: active clarification with 1 attempt
            mock_context.get_context = AsyncMock(side_effect=[
                {
                    "psid": "123456",
                    "conversation_state": "active",
                    "clarification": {},
                },
                {
                    "psid": "123456",
                    "conversation_state": "active",
                    "clarification": {
                        "active": True,
                        "attempt_count": 1,
                        "questions_asked": ["budget"],
                    },
                },
            ])
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context.update_clarification_state = AsyncMock(return_value=None)
            mock_context.update_search_results = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            with patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_service_class:
                mock_send_service = MagicMock()
                mock_send_service.send_message = AsyncMock(return_value=None)
                mock_send_service.close = AsyncMock(return_value=None)
                mock_send_service_class.return_value = mock_send_service

                # Mock product formatter to avoid formatting issues
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class:
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results = MagicMock(return_value={"text": "Found products"})
                    mock_formatter_class.return_value = mock_formatter

                    with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                        mock_search_service = MagicMock()
                        mock_search_service.search_products = AsyncMock(
                            return_value=ProductSearchResult(
                                products=[],
                                total_count=0,
                                search_params={},
                                search_time_ms=100,
                            )
                        )
                        mock_search_service_class.return_value = mock_search_service

                        processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

                        # First message: low confidence triggers clarification
                        payload = FacebookWebhookPayload(
                            object="page",
                            entry=[{
                                "id": "123456789",
                                "time": 1234567890,
                                "messaging": [{
                                    "sender": {"id": "123456"},
                                    "message": {"text": "shoes"},
                                }],
                            }],
                        )

                        response1 = await processor.process_message(payload)

                        # Should ask about budget
                        assert "budget" in response1.text.lower()
                        # FIX: send_message is NO LONGER called here - the response is returned
                        # for the webhook handler to send. This prevents double-message bug.

                        # Second message: clarification response with high confidence
                        payload2 = FacebookWebhookPayload(
                            object="page",
                            entry=[{
                                "id": "123456789",
                                "time": 1234567890,
                                "messaging": [{
                                    "sender": {"id": "123456"},
                                    "message": {"text": "$100 shoes"},
                                }],
                            }],
                        )

                        response2 = await processor.process_message(payload2)

                        # Should proceed to search since confidence improved
                        # Response is the product search summary
                        assert "found" in response2.text.lower() or "product" in response2.text.lower()


@pytest.mark.asyncio
async def test_clarification_flow_max_attempts_fallback():
    """Test fallback to assumptions after max 3 attempts."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.70,
            entities=ExtractedEntities(category="shoes"),  # Still missing budget
            raw_message="shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )

        mock_classifier.classify.return_value = mock_classification

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            # Context shows 3 attempts already made
            mock_context.get_context = AsyncMock(return_value={
                "psid": "123456",
                "conversation_state": "active",
                "clarification": {
                    "active": True,
                    "attempt_count": 3,  # Max attempts reached
                    "questions_asked": ["budget", "category", "size"],
                },
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context.update_clarification_state = AsyncMock(return_value=None)
            mock_context.update_search_results = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            with patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_service_class:
                mock_send_service = MagicMock()
                mock_send_service.send_message = AsyncMock(return_value=None)
                mock_send_service.close = AsyncMock(return_value=None)
                mock_send_service_class.return_value = mock_send_service

                # Mock product formatter
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class:
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results = MagicMock(return_value={"text": "Found products"})
                    mock_formatter_class.return_value = mock_formatter

                    with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                        mock_search_service = MagicMock()
                        mock_search_service.search_products = AsyncMock(
                            return_value=ProductSearchResult(
                                products=[],
                                total_count=0,
                                search_params={},
                                search_time_ms=100,
                            )
                        )
                        mock_search_service_class.return_value = mock_search_service

                        processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

                        payload = FacebookWebhookPayload(
                            object="page",
                            entry=[{
                                "id": "123456789",
                                "time": 1234567890,
                                "messaging": [{
                                    "sender": {"id": "123456"},
                                    "message": {"text": "shoes"},
                                }],
                            }],
                        )

                        response = await processor.process_message(payload)

                        # FIX: Fallback flow now returns assumption message (not product search summary)
                        # The assumption message is sent by the webhook handler
                        # Product carousel was sent via _proceed_to_search with suppress_summary=True
                        assert "options" in response.text.lower() or "shoes" in response.text.lower()
                        # Verify product carousel was sent (via _proceed_to_search)
                        assert mock_send_service.send_message.call_count >= 1
                        # The call should be for the product carousel
                        first_call_args = mock_send_service.send_message.call_args_list[0]
                        first_message = first_call_args[0][1]  # Second positional arg is the message
                        if isinstance(first_message, dict):
                            message_text = first_message.get("text", "")
                        else:
                            message_text = str(first_message)
                        # Product carousel was sent (contains "Found products" from our mock)
                        assert "found products" in message_text.lower() or "shoes" in message_text.lower()
                        # Clarification state should be cleared
                        mock_context.update_clarification_state.assert_called()


@pytest.mark.asyncio
async def test_clarification_state_persistence():
    """Test clarification state is properly tracked across exchanges."""
    clarification_service = ClarificationService()
    question_generator = QuestionGenerator()

    # Initial classification
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red"),
        raw_message="red shoes",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    # Generate first question
    question1, constraint1 = await question_generator.generate_next_question(
        classification=classification,
        questions_asked=[],
    )
    assert "budget" in question1.lower()
    assert constraint1 == "budget"

    # Simulate state update
    state = {
        "active": True,
        "attempt_count": 1,
        "questions_asked": ["budget"],
    }

    # After user responds, still missing constraints
    assert await clarification_service.should_fallback_to_assumptions({"clarification": state}) is False

    # Update state for second question
    state["attempt_count"] = 2
    state["questions_asked"].append("category")

    # Still shouldn't fallback
    assert await clarification_service.should_fallback_to_assumptions({"clarification": state}) is False

    # Update state for third question
    state["attempt_count"] = 3
    state["questions_asked"].append("size")

    # Should fallback now
    assert await clarification_service.should_fallback_to_assumptions({"clarification": state}) is True


@pytest.mark.asyncio
async def test_clarification_skips_non_product_search():
    """Test clarification is not triggered for non-product-search intents."""
    clarification_service = ClarificationService()

    # Greeting intent with low confidence
    classification = ClassificationResult(
        intent=IntentType.GREETING,
        confidence=0.50,  # Low confidence
        entities=ExtractedEntities(),
        raw_message="hi",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    needs_clarification = await clarification_service.needs_clarification(
        classification=classification,
        context={},
    )

    # Should NOT trigger clarification for non-product-search
    assert needs_clarification is False


@pytest.mark.asyncio
async def test_question_priority_ordering():
    """Test questions are asked in correct priority order."""
    generator = QuestionGenerator()

    # Only color and brand provided, missing budget, category, size
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red", brand="nike"),
        raw_message="red nike",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    questions_asked = []

    # First question should be about budget
    q1, c1 = await generator.generate_next_question(classification, questions_asked)
    assert "budget" in q1.lower()
    assert c1 == "budget"
    questions_asked.append(c1)

    # Second question should be about category
    q2, c2 = await generator.generate_next_question(classification, questions_asked)
    assert "type" in q2.lower() or "category" in q2.lower()
    assert c2 == "category"
    questions_asked.append(c2)

    # Third question should be about size
    q3, c3 = await generator.generate_next_question(classification, questions_asked)
    assert "size" in q3.lower()
    assert c3 == "size"
    questions_asked.append(c3)

    # No more questions - color and brand are already provided
    with pytest.raises(ValueError, match="No more questions to ask"):
        await generator.generate_next_question(classification, questions_asked)


@pytest.mark.asyncio
async def test_clarification_respects_existing_constraints():
    """Test clarification doesn't ask about constraints that are already present."""
    generator = QuestionGenerator()

    # User provided budget and category
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.75,
        entities=ExtractedEntities(budget=100, category="shoes"),
        raw_message="$100 shoes",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    # First question should be about size, not budget or category
    question, constraint = await generator.generate_next_question(classification, questions_asked=[])
    assert "budget" not in question.lower()
    assert "category" not in question.lower()
    assert "size" in question.lower()
    assert constraint == "size"


@pytest.mark.asyncio
async def test_assumption_message_generation():
    """Test assumption message includes helpful guidance."""
    clarification_service = ClarificationService()

    # User only provided category
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.70,
        entities=ExtractedEntities(category="shoes"),
        raw_message="shoes",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    message, assumed = await clarification_service.generate_assumption_message(
        classification=classification,
        context={},
    )

    # Should mention shoes
    assert "shoes" in message.lower()
    # Should suggest adjustments
    assert "adjust" in message.lower() or "let me know" in message.lower()


@pytest.mark.asyncio
async def test_clarification_flow_with_missing_critical_constraints():
    """Test clarification is triggered when critical constraints are missing."""
    clarification_service = ClarificationService()

    # High confidence but missing budget
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.85,  # Above threshold
        entities=ExtractedEntities(category="shoes"),  # Missing budget
        raw_message="shoes",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    needs_clarification = await clarification_service.needs_clarification(
        classification=classification,
        context={},
    )

    # Should trigger clarification due to missing critical constraint
    assert needs_clarification is True
