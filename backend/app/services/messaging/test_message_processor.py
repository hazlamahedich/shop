"""Tests for message processor.

Unit tests for end-to-end message processing and routing logic.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.messaging import FacebookWebhookPayload, MessengerResponse
from app.services.intent import ClassificationResult, ExtractedEntities, IntentType
from app.services.messaging.message_processor import MessageProcessor


@pytest.mark.asyncio
async def test_process_message_product_search():
    """Test processing product search message."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        # Mock classifier
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.95,
            entities=ExtractedEntities(category="shoes", budget=100.0),
            raw_message="running shoes under $100",
            llm_provider="test",
            model="test",
            processing_time_ms=100,
        )

        mock_classifier.classify.return_value = mock_classification

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            mock_context.get_context = AsyncMock(return_value={
                "psid": "123456",
                "created_at": None,
                "last_message_at": None,
                "message_count": 0,
                "previous_intents": [],
                "extracted_entities": {},
                "conversation_state": "active",
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

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

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert response.recipient_id == "123456"
            assert "Searching for products" in response.text
            assert "shoes" in response.text


@pytest.mark.asyncio
async def test_process_message_greeting():
    """Test processing greeting message."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.GREETING,
            confidence=0.98,
            entities=ExtractedEntities(),
            raw_message="Hi there",
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
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "Hi there"},
                    }],
                }],
            )

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert response.text == "Hi! How can I help you today?"


@pytest.mark.asyncio
async def test_process_message_low_confidence():
    """Test processing message with low confidence (clarification)."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.PRODUCT_SEARCH,
            confidence=0.65,
            entities=ExtractedEntities(),
            raw_message="something",
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
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

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

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert "not sure" in response.text.lower() or "more details" in response.text.lower()


@pytest.mark.asyncio
async def test_process_message_cart_view():
    """Test processing cart view request."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.CART_VIEW,
            confidence=0.99,
            entities=ExtractedEntities(),
            raw_message="Show me my cart",
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
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "Show me my cart"},
                    }],
                }],
            )

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert "cart" in response.text.lower()


@pytest.mark.asyncio
async def test_process_message_human_handoff():
    """Test processing human handoff request."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.HUMAN_HANDOFF,
            confidence=0.99,
            entities=ExtractedEntities(),
            raw_message="Talk to a person",
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
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "Talk to a person"},
                    }],
                }],
            )

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert "human agent" in response.text.lower() or "human" in response.text.lower()


@pytest.mark.asyncio
async def test_process_message_error_handling():
    """Test error handling in message processing."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        # Make classifier raise exception
        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = Exception("Classification failed")

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            mock_context.get_context = AsyncMock(return_value={
                "psid": "123456",
                "conversation_state": "active",
            })
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

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

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert "error" in response.text.lower()


@pytest.mark.asyncio
async def test_process_message_unknown_intent():
    """Test processing unknown intent."""
    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        mock_classifier = AsyncMock()
        mock_classification = ClassificationResult(
            intent=IntentType.UNKNOWN,
            confidence=0.0,
            entities=ExtractedEntities(),
            raw_message="xyzabc",
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
            })
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor(classifier=mock_classifier, context_manager=mock_context)

            payload = FacebookWebhookPayload(
                object="page",
                entry=[{
                    "id": "123456789",
                    "time": 1234567890,
                    "messaging": [{
                        "sender": {"id": "123456"},
                        "message": {"text": "xyzabc"},
                    }],
                }],
            )

            response = await processor.process_message(payload)

            assert isinstance(response, MessengerResponse)
            assert "not sure" in response.text.lower() or "more details" in response.text.lower()
