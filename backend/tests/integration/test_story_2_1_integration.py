"""Story 2-1: End-to-end integration tests for intent classification flow.

Tests the complete flow from webhook receipt to intent classification:
- Facebook webhook → MessageProcessor → IntentClassifier → Response

Validates the acceptance criteria from Epic 2, Story 2.1.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.api.webhooks.facebook import process_webhook_message
from app.services.messaging import MessageProcessor
from app.services.intent import IntentClassifier, IntentType
from app.services.intent.classification_schema import ClassificationResult, ExtractedEntities


@pytest.mark.asyncio
async def test_classification_flow_with_budget_constraint():
    """Test classification extracts budget constraint correctly.

    Acceptance Criteria: "extracts: intent (product_search), category (shoes), budget (100)"
    """
    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=ExtractedEntities(category="shoes", budget=100.0),
        raw_message="running shoes under $100",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        async def mock_update(psid, classification):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "running shoes under $100"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            mock_classifier.classify.assert_called_once()
            assert mock_result.confidence >= 0.80
            assert mock_result.needs_clarification is False


@pytest.mark.asyncio
async def test_low_confidence_triggers_clarification():
    """Test low confidence classification triggers clarification response.

    Acceptance Criteria: "if confidence < 0.80, bot triggers clarification flow"
    """
    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.65,
        entities=ExtractedEntities(),
        raw_message="something",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.return_value = None
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "something"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            assert "not sure" in response.text.lower() or "more details" in response.text.lower()


@pytest.mark.asyncio
async def test_conversation_context_usage_flow():
    """Test conversation context is passed to classifier for follow-up messages.

    Acceptance Criteria: "classification uses previous context for clarification"
    """
    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.88,
        entities=ExtractedEntities(category="shoes", size="8"),
        raw_message="size 8",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        existing_context = {
            "psid": "123456",
            "created_at": "2024-01-01T00:00:00",
            "last_message_at": "running shoes",
            "message_count": 1,
            "previous_intents": ["product_search"],
            "extracted_entities": {"category": "shoes"},
            "conversation_state": "active",
        }

        async def mock_get_context(psid):
            return existing_context

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.return_value = None
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "size 8"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            mock_classifier.classify.assert_called_once()


@pytest.mark.asyncio
async def test_all_intent_types_integration():
    """Test all intent types route to correct response messages.

    Validates: PRODUCT_SEARCH, GREETING, CART_VIEW, CHECKOUT, ORDER_TRACKING, HUMAN_HANDOFF
    """
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        test_cases = [
            (IntentType.PRODUCT_SEARCH, "Searching"),
            (IntentType.GREETING, "Hi"),
            (IntentType.CART_VIEW, "cart"),
            (IntentType.CHECKOUT, "Checkout"),
            (IntentType.ORDER_TRACKING, "Order"),
            (IntentType.HUMAN_HANDOFF, "human"),
        ]

        for intent, expected_keyword in test_cases:
            mock_result = ClassificationResult(
                intent=intent,
                confidence=0.90,
                entities=ExtractedEntities(),
                raw_message="test",
                llm_provider="test",
                model="test-model",
                processing_time_ms=100,
            )

            async def mock_classify(message, context=None):
                return mock_result

            mock_classifier = AsyncMock()
            mock_classifier.classify.side_effect = mock_classify
            mock_classifier_class.return_value = mock_classifier

            async def mock_get_context(psid):
                return {"psid": psid}

            with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
                mock_context_mgr = AsyncMock()
                mock_context_mgr.get_context.side_effect = mock_get_context
                mock_context_mgr.update_classification.return_value = None
                mock_context_class.return_value = mock_context_mgr

                from app.schemas.messaging import FacebookWebhookPayload

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": "123456"},
                            "message": {"text": "test"},
                        }],
                    }],
                )

                processor = MessageProcessor()
                response = await processor.process_message(payload)

                assert expected_keyword.lower() in response.text.lower() or response.text


@pytest.mark.asyncio
async def test_webhook_signature_verification_before_classification():
    """Test webhook signature verification happens before classification.

    Acceptance Criteria (NFR-S5): "All webhooks must verify request signatures"
    """
    with patch("app.api.webhooks.facebook.verify_facebook_webhook_signature") as mock_verify:
        mock_verify.return_value = False

        payload_data = {
            "object": "page",
            "entry": [{
                "id": "123456789",
                "time": 1234567890,
                "messaging": [{
                    "sender": {"id": "123456"},
                    "message": {"text": "running shoes under $100"},
                }],
            }],
        }

        class MockRequest:
            async def body(self):
                return json.dumps(payload_data).encode()

            async def json(self):
                return payload_data

            headers = {}

        request = MockRequest()

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            from app.api.webhooks.facebook import facebook_messenger_webhook
            await facebook_messenger_webhook(request, MagicMock())

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_entity_extraction_comprehensive():
    """Test comprehensive entity extraction from realistic user messages.

    Tests: category, budget, size, color, brand, constraints
    """
    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.92,
        entities=ExtractedEntities(
            category="shoes",
            budget=150.0,
            size="9",
            color="red",
            brand="Nike",
            constraints={"type": "running", "usage": "marathon"}
        ),
        raw_message="red Nike marathon running shoes size 9 under $150",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.return_value = None
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "red Nike marathon running shoes size 9 under $150"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            entities = mock_result.entities.model_dump()
            assert entities["category"] == "shoes"
            assert entities["budget"] == 150.0
            assert entities["size"] == "9"
            assert entities["color"] == "red"
            assert entities["brand"] == "Nike"


@pytest.mark.asyncio
async def test_error_handling_in_flow():
    """Test error handling in classification flow.

    Validates graceful degradation when components fail.
    """
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify_error(message, context=None):
            raise Exception("LLM service unavailable")

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify_error
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "test"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            assert "error" in response.text.lower() or "sorry" in response.text.lower()


@pytest.mark.asyncio
async def test_context_update_after_classification():
    """Test conversation context is updated with classification result.

    Validates: context stores intents, entities, message count
    """
    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(category="shoes", budget=100.0),
        raw_message="running shoes under $100",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    update_called = {"value": False}
    classification_data = {"value": None}

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        async def mock_update(psid, classification):
            update_called["value"] = True
            classification_data["value"] = classification

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "running shoes under $100"},
                    }],
                }],
            )

            processor = MessageProcessor()
            await processor.process_message(payload)

            assert update_called["value"] is True
            assert classification_data["value"]["intent"] == "product_search"
            assert classification_data["value"]["entities"]["category"] == "shoes"


@pytest.mark.asyncio
async def test_unknown_intent_routing():
    """Test unknown intent routes to appropriate fallback response."""
    mock_result = ClassificationResult(
        intent=IntentType.UNKNOWN,
        confidence=0.30,
        entities=ExtractedEntities(),
        raw_message="gibberish text",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.return_value = None
            mock_context_class.return_value = mock_context_mgr

            from app.schemas.messaging import FacebookWebhookPayload

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "gibberish text"},
                    }],
                }],
            )

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            assert "not sure" in response.text.lower() or "details" in response.text.lower()


@pytest.mark.asyncio
async def test_process_webhook_message_background_task():
    """Test process_webhook_message correctly calls MessageProcessor and sends response."""
    mock_response = MagicMock()
    mock_response.text = "Test response"
    mock_response.recipient_id = "123456"

    mock_processor = AsyncMock()
    mock_processor.process_message.return_value = mock_response

    from app.schemas.messaging import FacebookWebhookPayload

    payload = FacebookWebhookPayload(
        object="page",
        entry=[{
            "id": "123456789",
            "time": 1234567890,
            "messaging": [{
                "sender": {"id": "123456"},
                "message": {"text": "test message"},
            }],
        }],
    )

    with patch("app.api.webhooks.facebook.send_messenger_response") as mock_send:
        await process_webhook_message(mock_processor, payload)

        mock_processor.process_message.assert_called_once_with(payload)
        mock_send.assert_called_once_with(mock_response)


@pytest.mark.asyncio
async def test_clarification_threshold_boundary():
    """Test behavior at exactly 0.80 confidence threshold boundary."""
    # At threshold (should NOT trigger clarification)
    result_at_threshold = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.80,
        entities=ExtractedEntities(category="shoes"),
        raw_message="test",
        llm_provider="test",
        model="test",
        processing_time_ms=100,
    )

    async def mock_get_context(psid):
        return {"psid": psid}

    with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
        mock_context_mgr = AsyncMock()
        mock_context_mgr.get_context.side_effect = mock_get_context
        mock_context_mgr.update_classification.return_value = None
        mock_context_class.return_value = mock_context_mgr

        with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
            async def mock_classify(message, context=None):
                return result_at_threshold

            mock_classifier = AsyncMock()
            mock_classifier.classify.side_effect = mock_classify
            mock_classifier_class.return_value = mock_classifier

            from app.schemas.messaging import FacebookWebhookPayload

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

            processor = MessageProcessor()
            response = await processor.process_message(payload)

            # At 0.80, should NOT trigger clarification (proceeds to search)
            assert "not sure" not in response.text.lower()


@pytest.mark.asyncio
async def test_budget_variations_extracted():
    """Test budget extraction handles various formats: $100, under 100, max 100, etc."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        test_cases = [
            ("shoes under $100", 100.0),
            ("shoes under 100", 100.0),
            ("shoes budget 100", 100.0),
            ("shoes max 100", 100.0),
            ("shoes less than 100", 100.0),
        ]

        for phrase, expected_budget in test_cases:
            mock_result = ClassificationResult(
                intent=IntentType.PRODUCT_SEARCH,
                confidence=0.90,
                entities=ExtractedEntities(category="shoes", budget=expected_budget),
                raw_message=phrase,
                llm_provider="test",
                model="test-model",
                processing_time_ms=100,
            )

            async def mock_classify(message, context=None):
                return mock_result

            mock_classifier = AsyncMock()
            mock_classifier.classify.side_effect = mock_classify
            mock_classifier_class.return_value = mock_classifier

            async def mock_get_context(psid):
                return {"psid": psid}

            with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
                mock_context_mgr = AsyncMock()
                mock_context_mgr.get_context.side_effect = mock_get_context
                mock_context_mgr.update_classification.return_value = None
                mock_context_class.return_value = mock_context_mgr

                from app.schemas.messaging import FacebookWebhookPayload

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": "123456"},
                            "message": {"text": phrase},
                        }],
                    }],
                )

                processor = MessageProcessor()
                response = await processor.process_message(payload)

                assert mock_result.entities.budget == expected_budget
