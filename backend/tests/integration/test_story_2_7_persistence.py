"""Integration tests for Story 2-7: Persistent Cart Sessions.

Tests full consent flow, returning shopper detection, forget preferences,
session-only storage for opted-out shoppers, and Redis TTL expiry behavior.
"""

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis

from app.api.webhooks.facebook import process_webhook_message
from app.schemas.messaging import FacebookWebhookPayload
from app.services.messaging.message_processor import MessageProcessor
from app.services.consent import ConsentService, ConsentStatus
from app.services.session import SessionService
from app.services.cart import CartService


@pytest.mark.asyncio
async def test_full_consent_flow_first_add_opt_in_persistence():
    """Test complete consent flow from first add → opt-in → persistence."""
    # Setup: Mock Redis client with proper state tracking
    mock_redis = MagicMock(spec=redis.Redis)

    # Track stored data to maintain mock state
    stored_data = {}

    def mock_get(key):
        return stored_data.get(key)

    def mock_setex(key, ttl, value):
        stored_data[key] = value
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.exists.side_effect = lambda k: 1 if k in stored_data else 0
    mock_redis.delete.side_effect = lambda k: stored_data.pop(k, None)

    # Initialize services
    consent_service = ConsentService(redis_client=mock_redis)
    session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)
    cart_service = CartService(redis_client=mock_redis)

    psid = "test_user_consent_flow"

    # Step 1: Verify consent is pending for new user
    consent_status = await consent_service.get_consent(psid)
    assert consent_status == ConsentStatus.PENDING

    # Step 2: User opts in
    await consent_service.record_consent(psid, consent_granted=True)
    consent_status = await consent_service.get_consent(psid)
    assert consent_status == ConsentStatus.OPTED_IN

    # Step 3: Add item to cart (should persist)
    cart = await cart_service.add_item(
        psid=psid,
        product_id="prod_1",
        variant_id="var_1",
        title="Test Product",
        price=29.99,
        image_url="https://example.com/image.jpg",
        quantity=1
    )

    assert len(cart.items) == 1
    assert cart.items[0].title == "Test Product"

    # Verify Redis setex was called (cart persistence)
    assert mock_redis.setex.called

    # Step 4: Verify returning shopper detection
    is_returning = await session_service.is_returning_shopper(psid)
    assert is_returning is True


@pytest.mark.asyncio
async def test_returning_shopper_welcome_message():
    """Test welcome back message for returning shoppers."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Setup: User with existing cart and consent
    existing_cart = {
        "items": [{
            "productId": "prod_1",
            "variantId": "var_1",
            "title": "Running Shoes",
            "price": 89.99,
            "imageUrl": "https://example.com/shoes.jpg",
            "currencyCode": "USD",
            "quantity": 2,
            "addedAt": datetime.now(timezone.utc).isoformat()
        }],
        "subtotal": 179.98,
        "currencyCode": "USD",
        "itemCount": 2,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    # Track stored data to maintain mock state
    stored_data = {}

    def mock_get(key):
        if "cart:" in key:
            return json.dumps(existing_cart)
        return stored_data.get(key)

    def mock_setex(key, ttl, value):
        stored_data[key] = value
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.exists.side_effect = lambda k: 1 if "cart:" in k or k in stored_data else 0

    consent_service = ConsentService(redis_client=mock_redis)
    session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

    psid = "test_returning_user"

    # Record consent
    await consent_service.record_consent(psid, consent_granted=True)

    # Verify returning shopper detection
    is_returning = await session_service.is_returning_shopper(psid)
    assert is_returning is True

    # Get cart item count for welcome message
    item_count = await session_service.get_cart_item_count(psid)
    assert item_count == 1  # 1 distinct item (quantity 2)


@pytest.mark.asyncio
async def test_forget_preferences_clears_voluntary_only():
    """Test forget preferences clears cart but not order refs (operational data)."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Setup: Cart and consent
    existing_cart = {
        "items": [{
            "productId": "prod_1",
            "variantId": "var_1",
            "title": "Test Product",
            "price": 29.99,
            "imageUrl": "https://example.com/image.jpg",
            "currencyCode": "USD",
            "quantity": 1,
            "addedAt": datetime.now(timezone.utc).isoformat()
        }],
        "subtotal": 29.99,
        "currencyCode": "USD",
        "itemCount": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    # Track stored data and deleted keys
    stored_data = {
        f"cart:test_forget_user": json.dumps(existing_cart),
        f"consent:test_forget_user": json.dumps({
            "status": "opted_in",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "psid": "test_forget_user"
        }),
        f"order_ref:test_forget_user": "order_12345"  # Operational data
    }
    deleted_keys = []

    def mock_get(key):
        return stored_data.get(key)

    def mock_delete(key):
        deleted_keys.append(key)
        if key in stored_data:
            del stored_data[key]
        return 1

    mock_redis.get.side_effect = mock_get
    mock_redis.delete.side_effect = mock_delete
    mock_redis.exists.side_effect = lambda k: 1 if k in stored_data else 0
    mock_redis.setex.return_value = True

    consent_service = ConsentService(redis_client=mock_redis)
    session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

    psid = "test_forget_user"

    # Clear session (voluntary data only)
    await session_service.clear_session(psid)

    # Verify voluntary data cleared
    consent_status = await consent_service.get_consent(psid)
    assert consent_status == ConsentStatus.PENDING

    # Verify delete was called for cart, consent, activity, context
    assert mock_redis.delete.called

    # Verify operational data (order_ref) was NOT deleted
    assert f"order_ref:{psid}" not in deleted_keys
    assert f"order_ref:{psid}" in stored_data  # Still exists


@pytest.mark.asyncio
async def test_session_only_storage_for_opted_out_shoppers():
    """Test session-only storage for shoppers who opt out."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Track stored data to maintain mock state
    stored_data = {}

    def mock_get(key):
        return stored_data.get(key)

    def mock_setex(key, ttl, value):
        stored_data[key] = value
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex

    consent_service = ConsentService(redis_client=mock_redis)
    cart_service = CartService(redis_client=mock_redis)

    psid = "test_opt_out_user"

    # User opts out
    await consent_service.record_consent(psid, consent_granted=False)
    consent_status = await consent_service.get_consent(psid)
    assert consent_status == ConsentStatus.OPTED_OUT

    # Verify cart cannot be persisted
    can_persist = await consent_service.can_persist_cart(psid)
    assert can_persist is False


@pytest.mark.asyncio
async def test_consent_revocation():
    """Test consent can be revoked via forget preferences."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Track stored data to maintain mock state
    stored_data = {}

    def mock_get(key):
        return stored_data.get(key)

    def mock_setex(key, ttl, value):
        stored_data[key] = value
        return True

    def mock_delete(key):
        if key in stored_data:
            del stored_data[key]
        return 1

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.delete.side_effect = mock_delete

    consent_service = ConsentService(redis_client=mock_redis)

    psid = "test_revoke_user"

    # Opt in first
    await consent_service.record_consent(psid, consent_granted=True)
    assert await consent_service.get_consent(psid) == ConsentStatus.OPTED_IN

    # Revoke consent
    await consent_service.revoke_consent(psid)

    # Verify consent is pending again
    assert await consent_service.get_consent(psid) == ConsentStatus.PENDING


@pytest.mark.asyncio
async def test_returning_shopper_without_consent():
    """Test returning shopper without consent is not detected."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Cart exists but no consent
    mock_redis.exists.return_value = 1
    mock_redis.get.return_value = None  # No consent record

    consent_service = ConsentService(redis_client=mock_redis)
    session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

    psid = "test_no_consent_user"

    # Has cart but no consent
    is_returning = await session_service.is_returning_shopper(psid)
    assert is_returning is False


@pytest.mark.asyncio
async def test_returning_shopper_without_cart():
    """Test returning shopper without cart is not detected."""
    mock_redis = MagicMock(spec=redis.Redis)

    # Track stored data to maintain mock state
    stored_data = {}

    def mock_get(key):
        return stored_data.get(key)

    def mock_setex(key, ttl, value):
        stored_data[key] = value
        return True

    mock_redis.get.side_effect = mock_get
    mock_redis.setex.side_effect = mock_setex
    mock_redis.exists.side_effect = lambda k: 1 if k in stored_data else 0

    consent_service = ConsentService(redis_client=mock_redis)
    session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

    psid = "test_no_cart_user"

    # Has consent but no cart
    await consent_service.record_consent(psid, consent_granted=True)

    is_returning = await session_service.is_returning_shopper(psid)
    assert is_returning is False


@pytest.mark.asyncio
async def test_redis_ttl_expiry_behavior():
    """Test Redis TTL is set correctly for cart and consent."""
    mock_redis = MagicMock(spec=redis.Redis)
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True

    from app.services.consent.consent_service import ConsentService as CS
    from app.services.session.session_service import SessionService as SS

    consent_service = CS(redis_client=mock_redis)
    session_service = SS(redis_client=mock_redis, consent_service=consent_service)

    psid = "test_ttl_user"

    # Record consent - should have 30-day TTL
    await consent_service.record_consent(psid, consent_granted=True)

    # Check setex was called with 30-day TTL (2,592,000 seconds)
    consent_ttl_call = None
    for call in mock_redis.setex.call_args_list:
        args = call[0]
        if "consent:" in args[0]:
            consent_ttl_call = args
            break

    assert consent_ttl_call is not None
    assert consent_ttl_call[1] == 30 * 24 * 60 * 60  # 30 days in seconds


@pytest.mark.asyncio
async def test_activity_tracking_for_returning_shoppers():
    """Test activity tracking for returning shoppers."""
    mock_redis = MagicMock(spec=redis.Redis)
    mock_redis.setex.return_value = True

    session_service = SessionService(redis_client=mock_redis)

    psid = "test_activity_user"

    # Update activity
    await session_service.update_activity(psid)

    # Verify setex was called with 24-hour TTL
    activity_ttl_call = None
    for call in mock_redis.setex.call_args_list:
        args = call[0]
        if "last_activity:" in args[0]:
            activity_ttl_call = args
            break

    assert activity_ttl_call is not None
    assert activity_ttl_call[1] == 24 * 60 * 60  # 24 hours in seconds


@pytest.mark.asyncio
async def test_consent_message_integration():
    """Test consent message is sent via MessengerSendService."""
    with patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class, \
         patch("app.services.messaging.message_processor.ConsentService") as mock_consent_class:

        # Mock consent service - pending consent
        mock_consent = MagicMock()
        mock_consent.get_consent = AsyncMock(return_value=ConsentStatus.PENDING)
        mock_consent_class.return_value = mock_consent

        # Mock send service
        mock_send = MagicMock()
        mock_send.send_message = AsyncMock(return_value={"message_id": "mid.123"})
        mock_send.close = AsyncMock(return_value=None)
        mock_send_class.return_value = mock_send

        # Mock context manager
        mock_redis = MagicMock()
        mock_redis.setex.return_value = True

        # Prepare context with product data
        context_with_product = {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_1",
                        "title": "Test Product",
                        "images": [{"url": "https://example.com/product.jpg"}],
                        "variants": [
                            {
                                "id": "var_1",
                                "price": 29.99,
                                "currency_code": "USD",
                                "available_for_sale": True
                            }
                        ]
                    }
                ],
                "total_count": 1
            }
        }

        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            mock_context.redis = mock_redis
            mock_context.get_context = AsyncMock(return_value=context_with_product)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor()

            # Trigger consent request
            response = await processor._request_consent(
                psid="test_consent_msg",
                product_id="prod_1",
                variant_id="var_1",
                context=context_with_product
            )

            # Verify send_message was called with quick replies
            assert mock_send.send_message.called
            call_args = mock_send.send_message.call_args[0]
            assert call_args[0] == "test_consent_msg"
            message_payload = call_args[1]
            assert "quick_replies" in message_payload
            assert len(message_payload["quick_replies"]) == 2


@pytest.mark.asyncio
async def test_forget_preferences_intent_routing():
    """Test FORGET_PREFERENCES intent routes to forget handler."""
    from app.services.intent import IntentType, ClassificationResult, ExtractedEntities

    with patch("app.services.messaging.message_processor.SessionService") as mock_session_class, \
         patch("app.services.messaging.message_processor.ConsentService") as mock_consent_class:

        # Mock session service
        mock_session = MagicMock()
        mock_session.clear_session = AsyncMock(return_value=None)
        mock_session.update_activity = AsyncMock(return_value=None)
        mock_session.is_returning_shopper = AsyncMock(return_value=False)
        mock_session_class.return_value = mock_session

        # Mock consent service
        mock_consent = MagicMock()
        mock_consent.get_consent = AsyncMock(return_value=ConsentStatus.PENDING)
        mock_consent_class.return_value = mock_consent

        # Mock context manager
        mock_redis = MagicMock()
        with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
            mock_context = MagicMock()
            mock_context.redis = mock_redis
            mock_context.get_context = AsyncMock(return_value={})
            mock_context.update_classification = AsyncMock(return_value=None)
            mock_context_class.return_value = mock_context

            processor = MessageProcessor()

            # Create classification with FORGET_PREFERENCES intent
            classification = ClassificationResult(
                intent=IntentType.FORGET_PREFERENCES,
                entities=ExtractedEntities(),
                confidence=0.99,
                raw_message="forget my preferences",
                llm_provider="test",
                model="test",
                processing_time_ms=50
            )

            # Route to response
            response = await processor._route_response(
                psid="test_forget_intent",
                classification=classification,
                context={}
            )

            # Verify forget handler was called
            assert mock_session.clear_session.called
            assert "forgotten" in response.text.lower() or "cleared" in response.text.lower()
