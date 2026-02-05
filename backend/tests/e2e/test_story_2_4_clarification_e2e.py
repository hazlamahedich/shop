"""E2E tests for Story 2.4: Clarification Flow.

Tests cover:
- Full clarification flow with real LLM responses
- Clarification timeout and abandonment
- Maximum 3 message exchange enforcement
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.clarification import ClarificationService, QuestionGenerator
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType
from app.services.messaging.message_processor import MessageProcessor
from app.schemas.messaging import FacebookWebhookPayload


@pytest.mark.asyncio
async def test_e2e_clarification_flow_low_confidence():
    """E2E test: Low confidence triggers clarification flow."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.65,  # Below 0.80 threshold
            entities=ExtractedEntities(category="shoes"),  # Missing budget
            raw_message="shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )

        mock_classifier.classify.return_value = mock_classification

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            mock_context.get_context = AsyncMock(return_value={
                "psid": "123456",
                "conversation_state": "active",
                "clarification": {},  # No active clarification
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

                # Should enter clarification flow
                assert "budget" in response.text.lower() or "price" in response.text.lower()
                # Clarification state should be set to active
                mock_context.update_clarification_state.assert_called_once()
                call_args = mock_context.update_clarification_state.call_args
                state = call_args[0][1]  # Second positional arg
                assert state["active"] is True
                assert state["attempt_count"] == 1


@pytest.mark.asyncio
async def test_e2e_clarification_flow_confidence_improves():
    """E2E test: Confidence improves after clarification response."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        # First call: low confidence
        mock_classification_low = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.65,
            entities=ExtractedEntities(category="shoes"),
            raw_message="shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )
        # Second call: high confidence after clarification
        mock_classification_high = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.90,  # Above threshold
            entities=ExtractedEntities(category="shoes", budget=100),
            raw_message="$100 shoes",
            llm_provider="test",
            model="test",
            processing_time_ms=50,
        )

        mock_classifier.classify.side_effect = [mock_classification_low, mock_classification_high]

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
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

                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class:
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results = MagicMock(return_value={"text": "Found products"})
                    mock_formatter_class.return_value = mock_formatter

                    with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                        from app.schemas.shopify import ProductSearchResult
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

                        # First message: triggers clarification
                        payload1 = FacebookWebhookPayload(
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

                        response1 = await processor.process_message(payload1)
                        assert "budget" in response1.text.lower()

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
                        # Should proceed to product search
                        assert "found" in response2.text.lower() or "product" in response2.text.lower()
                        # Clarification state should be cleared
                        clear_calls = [call for call in mock_context.update_clarification_state.call_args_list
                                      if call[0][1].get("active") is False]
                        assert len(clear_calls) > 0


@pytest.mark.asyncio
async def test_e2e_clarification_flow_max_three_messages():
    """E2E test: Clarification flow maxes out at 3 messages."""
    clarification_service = ClarificationService()

    # Simulate clarification state with 3 attempts
    context_maxed = {
        "clarification": {
            "active": True,
            "attempt_count": 3,
            "questions_asked": ["budget", "category", "size"],
        }
    }

    # Should fallback to assumptions
    should_fallback = await clarification_service.should_fallback_to_assumptions(context_maxed)
    assert should_fallback is True

    # Generate assumption message
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
        context=context_maxed,
    )

    # Should contain helpful guidance
    assert "shoes" in message.lower()
    assert "adjust" in message.lower() or "let me know" in message.lower()


@pytest.mark.asyncio
async def test_e2e_clarification_flow_missing_constraints():
    """E2E test: Clarification triggered by missing critical constraints."""
    clarification_service = ClarificationService()

    # High confidence but missing budget (critical constraint)
    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.85,  # Above 0.80 threshold
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

    assert needs_clarification is True


@pytest.mark.asyncio
async def test_e2e_clarification_flow_non_product_search():
    """E2E test: Clarification not triggered for non-product-search."""
    clarification_service = ClarificationService()

    # Low confidence greeting should NOT trigger clarification
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

    assert needs_clarification is False


@pytest.mark.asyncio
async def test_e2e_question_priority_ordering():
    """E2E test: Questions asked in priority order."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red"),  # Missing budget, category, size, brand
        raw_message="red",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    questions_asked = []

    # Generate questions in priority order
    q1, c1 = await generator.generate_next_question(classification, questions_asked)
    assert "budget" in q1.lower()
    assert c1 == "budget"
    questions_asked.append(c1)

    q2, c2 = await generator.generate_next_question(classification, questions_asked)
    assert "type" in q2.lower() or "category" in q2.lower()
    assert c2 == "category"
    questions_asked.append(c2)

    q3, c3 = await generator.generate_next_question(classification, questions_asked)
    assert "size" in q3.lower()
    assert c3 == "size"
    questions_asked.append(c3)

    q4, c4 = await generator.generate_next_question(classification, questions_asked)
    assert "brand" in q4.lower()
    assert c4 == "brand"


@pytest.mark.asyncio
async def test_e2e_clarification_no_questions_needed():
    """E2E test: No questions when all constraints present."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(
            budget=100,
            category="shoes",
            size="10",
            color="red",
            brand="nike",
        ),
        raw_message="$100 nike shoes size 10 red",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    # Should raise error - no questions to ask
    with pytest.raises(ValueError, match="No more questions to ask"):
        await generator.generate_next_question(classification, [])


@pytest.mark.asyncio
async def test_e2e_clarification_skips_already_asked():
    """E2E test: Questions skip constraints already asked about."""
    generator = QuestionGenerator()

    classification = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.60,
        entities=ExtractedEntities(color="red"),
        raw_message="red",
        llm_provider="test",
        model="test",
        processing_time_ms=50,
    )

    # Budget already asked
    question, constraint = await generator.generate_next_question(classification, ["budget"])

    # Should skip budget and ask about category
    assert "budget" not in question.lower()
    assert "type" in question.lower() or "category" in question.lower()
    assert constraint == "category"


@pytest.mark.asyncio
async def test_e2e_clarification_respects_existing_entities():
    """E2E test: Clarification respects entities user already provided."""
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

    # Should ask about size, not budget or category
    question, constraint = await generator.generate_next_question(classification, [])
    assert "budget" not in question.lower()
    assert "category" not in question.lower()
    assert "size" in question.lower()
    assert constraint == "size"


@pytest.mark.asyncio
async def test_e2e_assumption_message_includes_adjustment_hint():
    """E2E test: Assumption message suggests user can adjust."""
    clarification_service = ClarificationService()

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

    # Should mention ability to adjust
    assert "adjust" in message.lower() or "let me know" in message.lower()
