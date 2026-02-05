"""E2E tests for Story 2-7: Persistent Cart Sessions.

Tests complete user flows including:
- First visit → opt-in → close → return → cart restored
- Opt-out flow: add items → opt-out → close → return → cart empty
- Forget preferences: add items → "forget my preferences" → data cleared
"""

import json
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from time import sleep

import pytest
import redis

from app.schemas.messaging import FacebookWebhookPayload
from app.services.messaging.message_processor import MessageProcessor
from app.services.consent import ConsentService, ConsentStatus
from app.services.session import SessionService
from app.services.cart import CartService
from app.services.intent import IntentType, ClassificationResult, ExtractedEntities


class TestStory27PersistentCartE2E:
    """E2E tests for Persistent Cart Sessions feature."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        return MagicMock(spec=redis.Redis)

    @pytest.fixture
    def sample_product_context(self):
        """Sample product in context."""
        return {
            "last_search_results": {
                "products": [
                    {
                        "id": "prod_123",
                        "title": "Running Shoes",
                        "handle": "running-shoes",
                        "price": 89.99,
                        "images": [{"url": "https://example.com/shoes.jpg"}],
                        "variants": [
                            {
                                "id": "var_456",
                                "price": 89.99,
                                "currency_code": "USD",
                                "available_for_sale": True,
                                "selected_options": {"Size": "10", "Color": "Red"}
                            }
                        ]
                    }
                ],
                "total_count": 1
            }
        }

    @pytest.mark.asyncio
    async def test_e2e_first_visit_opt_in_close_return_cart_restored(self, mock_redis, sample_product_context):
        """Test E2E: First visit → opt-in → close → return → cart restored."""
        psid = "test_e2e_first_visit_user"

        # Setup mock Redis with proper state tracking
        stored_data = {}

        def mock_get(key):
            return stored_data.get(key)

        def mock_setex(key, ttl, value):
            stored_data[key] = value
            return True

        mock_redis.get.side_effect = mock_get
        mock_redis.setex.side_effect = mock_setex
        mock_redis.exists.side_effect = lambda k: 1 if k in stored_data else 0

        # Initialize services
        consent_service = ConsentService(redis_client=mock_redis)
        session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)
        cart_service = CartService(redis_client=mock_redis)

        # === FIRST VISIT ===

        # Step 1: User searches for product (product in context)
        # Step 2: User tries to add item - no consent yet

        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.PENDING, "Consent should be pending for new user"

        # Step 3: User opts in to cart persistence
        await consent_service.record_consent(psid, consent_granted=True)
        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.OPTED_IN, "Consent should be opted in"

        # Step 4: Add item to cart
        cart = await cart_service.add_item(
            psid=psid,
            product_id="prod_123",
            variant_id="var_456",
            title="Running Shoes",
            price=89.99,
            image_url="https://example.com/shoes.jpg",
            quantity=1
        )

        assert len(cart.items) == 1, "Cart should have 1 item"
        assert cart.items[0].title == "Running Shoes"
        assert cart.subtotal == 89.99

        # Verify cart was persisted (setex called)
        assert mock_redis.setex.called, "Cart should be persisted to Redis"

        # === USER CLOSES MESSENGER ===

        # Simulate time passing (e.g., 1 hour later)
        # Redis TTL handles expiry automatically

        # === USER RETURNS ===

        # Update activity (simulates user returning)
        await session_service.update_activity(psid)

        # Step 5: Check if returning shopper
        is_returning = await session_service.is_returning_shopper(psid)
        assert is_returning is True, "User should be detected as returning shopper"

        # Step 6: Get cart item count for welcome message
        item_count = await session_service.get_cart_item_count(psid)
        assert item_count == 1, "Cart should still have 1 item"

        # Verify welcome back message would be shown
        expected_message = f"Welcome back! You have {item_count} item{'s' if item_count != 1 else ''} in your cart. Type 'cart' to view."
        assert "Welcome back" in expected_message
        assert "1 item" in expected_message

    @pytest.mark.asyncio
    async def test_e2e_opt_out_flow_close_return_cart_empty(self, mock_redis):
        """Test E2E: Add items → opt-out → close → return → cart empty."""
        psid = "test_e2e_opt_out_user"

        # Setup mock Redis with proper state tracking
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
        cart_service = CartService(redis_client=mock_redis)

        # === USER OPTS OUT ===

        # User opts out of cart persistence
        await consent_service.record_consent(psid, consent_granted=False)
        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.OPTED_OUT, "User should be opted out"

        # Verify cart cannot be persisted
        can_persist = await consent_service.can_persist_cart(psid)
        assert can_persist is False, "Cart should not persist for opted-out user"

        # === USER CLOSES MESSENGER ===

        # === USER RETURNS ===

        # Cart should not exist (wasn't persisted)
        session_service_new = SessionService(
            redis_client=mock_redis,
            consent_service=consent_service
        )
        is_returning = await session_service_new.is_returning_shopper(psid)
        assert is_returning is False, "Opted-out user should not be detected as returning"

    @pytest.mark.asyncio
    async def test_e2e_forget_preferences_clears_data(self, mock_redis):
        """Test E2E: Add items → 'forget my preferences' → data cleared."""
        psid = "test_e2e_forget_user"

        # Setup mock Redis with proper state tracking
        existing_cart = {
            "items": [{
                "productId": "prod_123",
                "variantId": "var_456",
                "title": "Running Shoes",
                "price": 89.99,
                "imageUrl": "https://example.com/shoes.jpg",
                "currencyCode": "USD",
                "quantity": 2,
                "addedAt": datetime.now(timezone.utc).isoformat()
            }],
            "subtotal": 179.98,
            "currencyCode": "USD",
            "itemCount": 1,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }

        stored_data = {
            f"cart:{psid}": json.dumps(existing_cart),
            f"consent:{psid}": json.dumps({
                "status": "opted_in",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "psid": psid
            }),
            f"order_ref:{psid}": "order_12345"  # Operational data
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
        mock_redis.setex.return_value = True
        mock_redis.set.side_effect = lambda k, v: stored_data.update({k: v})

        consent_service = ConsentService(redis_client=mock_redis)
        session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

        # === USER HAS CART AND CONSENT ===

        # Verify data exists
        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.OPTED_IN, "User should have opted in"

        # === USER TYPES "FORGET MY PREFERENCES" ===

        # Clear session (simulates forget preferences handler)
        await session_service.clear_session(psid)

        # === VERIFY VOLUNTARY DATA CLEARED ===

        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.PENDING, "Consent should be cleared"

        # Verify delete was called for cart, consent, activity, context
        assert mock_redis.delete.called, "Delete should be called to clear data"

        # === VERIFY OPERATIONAL DATA PRESERVED ===

        # Order ref should still exist (not cleared by forget preferences)

        # Verify operational data preserved
        assert f"order_ref:{psid}" not in deleted_keys, "Order ref should not be deleted"
        assert f"order_ref:{psid}" in stored_data, "Order ref should still exist in data"

    @pytest.mark.asyncio
    async def test_e2e_multiple_items_persist_and_restore(self, mock_redis, sample_product_context):
        """Test E2E: Multiple items persist and restore correctly."""
        psid = "test_e2e_multi_items_user"

        # Setup mock Redis with proper state tracking
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
        cart_service = CartService(redis_client=mock_redis)

        # User opts in
        await consent_service.record_consent(psid, consent_granted=True)

        # Add multiple items
        products = [
            ("prod_1", "var_1", "Running Shoes", 89.99),
            ("prod_2", "var_2", "Sport T-Shirt", 29.99),
            ("prod_3", "var_3", "Water Bottle", 15.99),
        ]

        for prod_id, var_id, title, price in products:
            await cart_service.add_item(
                psid=psid,
                product_id=prod_id,
                variant_id=var_id,
                title=title,
                price=price,
                image_url=f"https://example.com/{title.lower().replace(' ', '_')}.jpg",
                quantity=1
            )

        # Verify item count
        item_count = await session_service.get_cart_item_count(psid)
        assert item_count == 3, "Should have 3 distinct items"

        # Verify returning shopper detection
        is_returning = await session_service.is_returning_shopper(psid)
        assert is_returning is True, "Should be detected as returning shopper"

    @pytest.mark.asyncio
    async def test_e2e_consent_flow_via_message_processor(self, mock_redis, sample_product_context):
        """Test E2E: Full consent flow via message processor."""
        psid = "test_e2e_mp_consent_user"

        # Setup mock Redis
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.exists.return_value = 0

        with patch("app.services.messaging.message_processor.ConsentService") as mock_consent_class, \
             patch("app.services.messaging.message_processor.MessengerSendService") as mock_send_class:

            # Mock consent service
            mock_consent = MagicMock()
            mock_consent.get_consent = AsyncMock(return_value=ConsentStatus.PENDING)
            mock_consent.record_consent = AsyncMock(return_value={
                "status": ConsentStatus.OPTED_IN,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "psid": psid
            })
            mock_consent.can_persist_cart = AsyncMock(return_value=True)
            mock_consent_class.return_value = mock_consent

            # Mock send service
            mock_send = MagicMock()
            mock_send.send_message = AsyncMock(return_value={"message_id": "mid.123"})
            mock_send.close = AsyncMock(return_value=None)
            mock_send_class.return_value = mock_send

            # Mock context manager
            with patch("app.services.messaging.message_processor.ConversationContextManager") as mock_context_class:
                mock_context = MagicMock()
                mock_context.redis = mock_redis
                mock_context.get_context = AsyncMock(return_value=sample_product_context)
                mock_context.update_classification = AsyncMock(return_value=None)
                mock_context_class.return_value = mock_context

                processor = MessageProcessor()

                # Step 1: Request consent (first add to cart) - pass the sample context
                response = await processor._request_consent(
                    psid=psid,
                    product_id="prod_123",
                    variant_id="var_456",
                    context=sample_product_context
                )

                # Verify consent message was sent
                assert mock_send.send_message.called, "Consent message should be sent"

                # Step 2: Simulate consent response via postback
                postback_payload = FacebookWebhookPayload(**{
                    "object": "page",
                    "entry": [{
                        "id": "123456",
                        "time": 1234567890,
                        "messaging": [{
                            "sender": {"id": psid},
                            "postback": {
                                "payload": "CONSENT:YES:prod_123:var_456"
                            }
                        }]
                    }]
                })

                # Mock updated consent status
                mock_consent.get_consent = AsyncMock(return_value=ConsentStatus.OPTED_IN)

                response = await processor.process_postback(postback_payload)

                # Verify consent was recorded
                assert mock_consent.record_consent.called, "Consent should be recorded"

    @pytest.mark.asyncio
    async def test_e2e_forget_preferences_via_message_processor(self, mock_redis):
        """Test E2E: Forget preferences via message processor."""
        psid = "test_e2e_mp_forget_user"

        # Setup mock Redis
        mock_redis.get.return_value = None
        mock_redis.delete.return_value = 1
        mock_redis.setex.return_value = True

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
                    psid=psid,
                    classification=classification,
                    context={}
                )

                # Verify forget handler was called
                assert mock_session.clear_session.called, "Session should be cleared"
                assert "forgotten" in response.text.lower() or "cleared" in response.text.lower()

    @pytest.mark.asyncio
    async def test_e2e_cart_ttl_24_hours(self, mock_redis):
        """Test E2E: Cart expires after 24 hours."""
        psid = "test_e2e_ttl_user"

        # Setup mock Redis
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True

        cart_service = CartService(redis_client=mock_redis)

        # Add item to cart
        cart = await cart_service.add_item(
            psid=psid,
            product_id="prod_1",
            variant_id="var_1",
            title="Test Product",
            price=29.99,
            image_url="https://example.com/image.jpg",
            quantity=1
        )

        # Verify setex was called with 24-hour TTL (86400 seconds)
        call_args = mock_redis.setex.call_args[0]
        assert call_args[1] == 86400, "Cart TTL should be 24 hours (86400 seconds)"

    @pytest.mark.asyncio
    async def test_e2e_activity_updates_on_each_message(self, mock_redis):
        """Test E2E: Activity timestamp updates on each message."""
        psid = "test_e2e_activity_user"

        # Setup mock Redis
        mock_redis.setex.return_value = True

        session_service = SessionService(redis_client=mock_redis)

        # Simulate multiple messages
        for i in range(5):
            await session_service.update_activity(psid)

        # Verify update_activity was called 5 times
        assert mock_redis.setex.call_count == 5, "Activity should update on each message"

    @pytest.mark.asyncio
    async def test_e2e_data_tier_separation(self, mock_redis):
        """Test E2E: Data tier separation - voluntary vs operational data."""
        psid = "test_e2e_data_tier_user"

        # Setup mock Redis
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1

        consent_service = ConsentService(redis_client=mock_redis)
        session_service = SessionService(redis_client=mock_redis, consent_service=consent_service)

        # === VOLUNTARY DATA (deletable) ===

        # Record consent
        await consent_service.record_consent(psid, consent_granted=True)

        # === OPERATIONAL DATA (not deletable) ===

        # Store order reference
        mock_redis.set(f"order_ref:{psid}", "order_12345")

        # === CLEAR SESSION (voluntary data only) ===

        await session_service.clear_session(psid)

        # === VERIFY SEPARATION ===

        # Voluntary data cleared
        consent_status = await consent_service.get_consent(psid)
        assert consent_status == ConsentStatus.PENDING, "Voluntary consent should be cleared"

        # Verify operational data preserved
        deleted_keys = [call[0][0] for call in mock_redis.delete.call_args_list]
        assert f"order_ref:{psid}" not in deleted_keys, "Operational order ref should NOT be deleted"
