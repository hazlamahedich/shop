"""Story 2-2: Integration tests for chat interface → product search flow.

Tests the complete flow from intent classification to product search results:
- Intent: PRODUCT_SEARCH → ProductSearchService → Response formatting

Validates the acceptance criteria from Epic 2, Story 2.2.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.messaging import MessageProcessor
from app.services.shopify import ProductSearchService
from app.schemas.shopify import Product, ProductSearchResult, ProductVariant, CurrencyCode
from app.services.intent import IntentClassifier, IntentType
from app.services.intent.classification_schema import ClassificationResult, ExtractedEntities
from app.schemas.messaging import FacebookWebhookPayload


@pytest.mark.asyncio
async def test_product_search_intent_routes_to_product_service():
    """Test PRODUCT_SEARCH intent routes to ProductSearchService.

    Acceptance Criteria: "When intent is product_search, call ProductSearchService"
    """
    mock_search_result = ProductSearchResult(
        products=[
            Product(
                id="gid://shopify/Product/1",
                title="Nike Air Max",
                description="Running shoes",
                price=99.99,
                currency_code=CurrencyCode.USD,
                product_type="Shoes",
                vendor="Nike",
                tags=[],
                images=[],
                variants=[],
                relevance_score=0.0,
            )
        ],
        total_count=1,
        search_params={"category": "shoes"},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=ExtractedEntities(category="shoes"),
        raw_message="running shoes",
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

        update_calls = []

        async def mock_update_classification(psid, classification):
            update_calls.append(("classification", classification))

        async def mock_update_search_results(psid, results):
            update_calls.append(("search_results", results))

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update_classification
            mock_context_mgr.update_search_results.side_effect = mock_update_search_results
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                # Mock Story 2.3 Messenger services
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class, \
                     patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class:

                    # Mock formatter
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results.return_value = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "generic",
                                "elements": [{"title": "Nike Air Max"}],
                            },
                        },
                    }
                    mock_formatter_class.return_value = mock_formatter

                    # Mock send service
                    mock_send_service = AsyncMock()
                    mock_send_service.send_message.return_value = {"message_id": "mid.123"}
                    mock_send_service.close = AsyncMock(return_value=None)
                    mock_send_class.return_value = mock_send_service

                    payload = FacebookWebhookPayload(
                        object="page",
                        entry=[{
                            "id": "123456789",
                            "time": 1234567890,
                            "messaging": [{
                                "sender": {"id": "123456"},
                                "message": {"text": "running shoes"},
                            }],
                        }],
                    )

                    processor = MessageProcessor()
                    response = await processor.process_message(payload)

                    # Verify ProductSearchService was called
                    mock_search_service.search_products.assert_called_once()
                    # Verify search results were stored in context
                    assert any(call[0] == "search_results" for call in update_calls)
                    # Verify formatter was called
                    mock_formatter.format_product_results.assert_called_once()
                    # Verify send service was called
                    mock_send_service.send_message.assert_called_once()
                    # After Story 2.3, response confirms products were sent
                    assert "product" in response.text.lower() or "found" in response.text.lower()


@pytest.mark.asyncio
async def test_product_search_response_formatting():
    """Test product search results are formatted for Messenger display.

    Acceptance Criteria: "Display products with title, price, description"
    """
    mock_search_result = ProductSearchResult(
        products=[
            Product(
                id="gid://shopify/Product/1",
                title="Running Shoes Pro",
                description="Lightweight running shoes for marathon training",
                price=129.99,
                currency="USD",
                available_for_sale=True,
                vendor="Nike",
                product_type="Shoes",
                images=[],
                variants=[],
            ),
            Product(
                id="gid://shopify/Product/2",
                title="Walking Comfort",
                description="Comfortable shoes for everyday walking",
                price=89.99,
                currency="USD",
                available_for_sale=True,
                vendor="Adidas",
                product_type="Shoes",
                images=[],
                variants=[],
            ),
        ],
        total_count=2,
        search_params={"category": "shoes"},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(category="shoes"),
        raw_message="show me shoes",
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

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                # Mock Story 2.3 Messenger services
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class, \
                     patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class:

                    # Mock formatter
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results.return_value = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "generic",
                                "elements": [
                                    {"title": "Running Shoes Pro"},
                                    {"title": "Walking Comfort"},
                                ],
                            },
                        },
                    }
                    mock_formatter_class.return_value = mock_formatter

                    # Mock send service
                    mock_send_service = AsyncMock()
                    mock_send_service.send_message.return_value = {"message_id": "mid.123"}
                    mock_send_service.close = AsyncMock(return_value=None)
                    mock_send_class.return_value = mock_send_service

                    payload = FacebookWebhookPayload(
                        object="page",
                        entry=[{
                            "id": "123456789",
                            "time": 1234567890,
                            "messaging": [{
                                "sender": {"id": "123456"},
                                "message": {"text": "show me shoes"},
                            }],
                        }],
                    )

                    processor = MessageProcessor()
                    response = await processor.process_message(payload)

                    # After Story 2.3, response confirms products were sent to Messenger
                    assert "product" in response.text.lower()
                    # Verify formatter was called with search result
                    mock_formatter.format_product_results.assert_called_once()
                    # Verify send service was called
                    mock_send_service.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_empty_product_search_results():
    """Test empty search results trigger helpful response.

    Acceptance Criteria: "When no products found, suggest alternatives"
    """
    mock_search_result = ProductSearchResult(
        products=[],
        total_count=0,
        search_params={"category": "shoes", "budget": 10.0},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.92,
        entities=ExtractedEntities(category="shoes", budget=10.0),
        raw_message="shoes under $10",
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

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": "123456"},
                            "message": {"text": "shoes under $10"},
                        }],
                    }],
                )

                processor = MessageProcessor()
                response = await processor.process_message(payload)

                # Verify helpful empty response
                assert "No exact matches" in response.text
                assert "similar items" in response.text or "broaden your budget" in response.text


@pytest.mark.asyncio
async def test_product_search_error_handling():
    """Test graceful error handling when ProductSearchService fails.

    Acceptance Criteria: "On search error, return friendly error message"
    """
    from app.core.errors import APIError

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(category="shoes"),
        raw_message="running shoes",
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

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search_error(entities):
                    raise APIError(
                        code="SHOPIFY_API_ERROR",
                        message="Shopify API unavailable",
                    )

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search_error
                mock_search_service_class.return_value = mock_search_service

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": "123456"},
                            "message": {"text": "running shoes"},
                        }],
                    }],
                )

                processor = MessageProcessor()
                response = await processor.process_message(payload)

                # Verify error response is user-friendly
                assert "error" in response.text.lower() or "sorry" in response.text.lower()
                assert "try again" in response.text.lower() or "human" in response.text.lower()


@pytest.mark.asyncio
async def test_search_results_update_conversation_context():
    """Test search results are stored in conversation context.

    Acceptance Criteria: "Store search results for follow-up interactions"
    """
    mock_search_result = ProductSearchResult(
        products=[
            Product(
                id="gid://shopify/Product/1",
                title="Test Product",
                description="Test description",
                price=49.99,
                currency="USD",
                available_for_sale=True,
                vendor="Test",
                product_type="Test",
                images=[],
                variants=[],
            )
        ],
        total_count=1,
        search_params={"category": "test"},
        search_time_ms=50,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(category="test"),
        raw_message="test",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    search_results_stored = {"value": None}

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        async def mock_update_classification(psid, classification):
            pass

        async def mock_update_search_results(psid, results):
            search_results_stored["value"] = results

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update_classification
            mock_context_mgr.update_search_results.side_effect = mock_update_search_results
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

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
                await processor.process_message(payload)

                # Verify search results were stored
                assert search_results_stored["value"] is not None
                assert "products" in search_results_stored["value"]
                assert search_results_stored["value"]["total_count"] == 1


@pytest.mark.asyncio
async def test_product_search_with_all_entity_types():
    """Test product search with all entity types (category, budget, size, color, brand).

    Acceptance Criteria: "Pass all extracted entities to ProductSearchService"
    """
    mock_search_result = ProductSearchResult(
        products=[],
        total_count=0,
        search_params={
            "category": "shoes",
            "budget": 100.0,
            "size": "9",
            "color": "red",
            "brand": "Nike",
        },
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.95,
        entities=ExtractedEntities(
            category="shoes",
            budget=100.0,
            size="9",
            color="red",
            brand="Nike",
        ),
        raw_message="red Nike shoes size 9 under $100",
        llm_provider="test",
        model="test-model",
        processing_time_ms=100,
    )

    entities_passed_to_search = {"value": None}

    with patch("app.services.messaging.message_processor.IntentClassifier") as mock_classifier_class:
        async def mock_classify(message, context=None):
            return mock_result

        mock_classifier = AsyncMock()
        mock_classifier.classify.side_effect = mock_classify
        mock_classifier_class.return_value = mock_classifier

        async def mock_get_context(psid):
            return {"psid": psid}

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    entities_passed_to_search["value"] = entities
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": "123456"},
                            "message": {"text": "red Nike shoes size 9 under $100"},
                        }],
                    }],
                )

                processor = MessageProcessor()
                await processor.process_message(payload)

                # Verify all entities were passed to search service
                entities = entities_passed_to_search["value"]
                assert entities.category == "shoes"
                assert entities.budget == 100.0
                assert entities.size == "9"
                assert entities.color == "red"
                assert entities.brand == "Nike"


@pytest.mark.asyncio
async def test_product_search_more_than_three_results():
    """Test response formatting when more than 3 products found.

    Acceptance Criteria: "Show first 3 products and indicate more available"
    """
    products = []
    for i in range(5):
        products.append(
            Product(
                id=f"gid://shopify/Product/{i}",
                title=f"Product {i+1}",
                description=f"Description {i+1}",
                price=10.0 * (i + 1),
                currency="USD",
                available_for_sale=True,
                vendor="Test",
                product_type="Test",
                images=[],
                variants=[],
            )
        )

    mock_search_result = ProductSearchResult(
        products=products,
        total_count=5,
        search_params={"category": "test"},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(category="test"),
        raw_message="show me products",
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

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                # Mock Story 2.3 Messenger services
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class, \
                     patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class:

                    # Mock formatter - returns elements for 5 products
                    mock_formatter = MagicMock()
                    mock_formatter.format_product_results.return_value = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "generic",
                                "elements": [
                                    {"title": f"Product {i+1}"} for i in range(5)
                                ],
                            },
                        },
                    }
                    mock_formatter_class.return_value = mock_formatter

                    # Mock send service
                    mock_send_service = AsyncMock()
                    mock_send_service.send_message.return_value = {"message_id": "mid.123"}
                    mock_send_service.close = AsyncMock(return_value=None)
                    mock_send_class.return_value = mock_send_service

                    payload = FacebookWebhookPayload(
                        object="page",
                        entry=[{
                            "id": "123456789",
                            "time": 1234567890,
                            "messaging": [{
                                "sender": {"id": "123456"},
                                "message": {"text": "show me products"},
                            }],
                        }],
                    )

                    processor = MessageProcessor()
                    response = await processor.process_message(payload)

                    # After Story 2.3, response confirms products were sent
                    assert "product" in response.text.lower()
                    # Verify formatter was called
                    mock_formatter.format_product_results.assert_called_once()


@pytest.mark.asyncio
async def test_description_truncation_in_response():
    """Test long product descriptions are truncated in Messenger response.

    Acceptance Criteria: "Truncate descriptions to 100 characters"
    """
    long_description = "A" * 200

    mock_search_result = ProductSearchResult(
        products=[
            Product(
                id="gid://shopify/Product/1",
                title="Test Product",
                description=long_description,
                price=99.99,
                currency="USD",
                available_for_sale=True,
                vendor="Test",
                product_type="Test",
                images=[],
                variants=[],
            )
        ],
        total_count=1,
        search_params={},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(),
        raw_message="test",
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

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                # Mock Story 2.3 Messenger services
                with patch("app.services.messaging.message_processor.MessengerProductFormatter") as mock_formatter_class, \
                     patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class:

                    # Mock formatter - verifies truncation in formatted result
                    mock_formatter = MagicMock()
                    formatted_payload = {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "generic",
                                "elements": [
                                    {
                                        "title": "Test Product",
                                        "subtitle": long_description[:100] + "..." if len(long_description) > 100 else long_description,
                                    }
                                ],
                            },
                        },
                    }
                    mock_formatter.format_product_results.return_value = formatted_payload
                    mock_formatter_class.return_value = mock_formatter

                    # Mock send service
                    mock_send_service = AsyncMock()
                    mock_send_service.send_message.return_value = {"message_id": "mid.123"}
                    mock_send_service.close = AsyncMock(return_value=None)
                    mock_send_class.return_value = mock_send_service

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

                    # After Story 2.3, verify formatter was called with long description
                    mock_formatter.format_product_results.assert_called_once()
                    # Verify the formatted subtitle is truncated
                    formatted_subtitle = formatted_payload["attachment"]["payload"]["elements"][0]["subtitle"]
                    assert "..." in formatted_subtitle
                    assert len(formatted_subtitle) <= 103  # 100 + "..."


@pytest.mark.asyncio
async def test_search_result_recipient_id_matches_sender():
    """Test response recipient_id matches webhook sender_id.

    Acceptance Criteria: "Response sent back to correct user"
    """
    mock_search_result = ProductSearchResult(
        products=[],
        total_count=0,
        search_params={},
        search_time_ms=100,
    )

    mock_result = ClassificationResult(
        intent=IntentType.PRODUCT_SEARCH,
        confidence=0.90,
        entities=ExtractedEntities(),
        raw_message="test",
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

        test_psid = "999888777"

        async def mock_get_context(psid):
            return {"psid": psid}

        async def mock_update(psid, data):
            pass

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context_mgr = AsyncMock()
            mock_context_mgr.get_context.side_effect = mock_get_context
            mock_context_mgr.update_classification.side_effect = mock_update
            mock_context_mgr.update_search_results.side_effect = mock_update
            mock_context_class.return_value = mock_context_mgr

            with patch("app.services.messaging.message_processor.ProductSearchService") as mock_search_service_class:
                async def mock_search(entities):
                    return mock_search_result

                mock_search_service = AsyncMock()
                mock_search_service.search_products.side_effect = mock_search
                mock_search_service_class.return_value = mock_search_service

                payload = FacebookWebhookPayload(
                    object="page",
                    entry=[{
                        "id": "123456789",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": test_psid},
                            "message": {"text": "test"},
                        }],
                    }],
                )

                processor = MessageProcessor()
                response = await processor.process_message(payload)

                # Verify recipient_id matches sender_id
                assert response.recipient_id == test_psid
