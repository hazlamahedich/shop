"""Message processing orchestrator for webhook → classify → respond flow.

Coordinates intent classification, context management, and response
routing for incoming Facebook Messenger messages.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog

from app.core.errors import APIError
from app.schemas.messaging import (
    ConversationContext,
    FacebookWebhookPayload,
    MessengerResponse,
)
from app.services.clarification import ClarificationService
from app.services.clarification.question_generator import QuestionGenerator
from app.services.intent import IntentClassifier, IntentType
from app.services.messaging.conversation_context import ConversationContextManager
from app.services.messenger import CartFormatter, MessengerProductFormatter, MessengerSendService
from app.services.shopify import ProductSearchService
from app.services.cart import CartService


logger = structlog.get_logger(__name__)


class MessageProcessor:
    """Orchestrates message processing: webhook → classify → respond."""

    def __init__(
        self,
        classifier: Optional[IntentClassifier] = None,
        context_manager: Optional[ConversationContextManager] = None,
    ) -> None:
        """Initialize message processor.

        Args:
            classifier: Intent classifier (uses default if not provided)
            context_manager: Conversation context manager (uses default if not provided)
        """
        self.classifier = classifier or IntentClassifier()
        self.context_manager = context_manager or ConversationContextManager()
        self.logger = structlog.get_logger(__name__)

    async def process_message(
        self,
        webhook_payload: FacebookWebhookPayload,
    ) -> MessengerResponse:
        """Process incoming Facebook Messenger message.

        Args:
            webhook_payload: Parsed Facebook webhook payload

        Returns:
            Messenger response to send to user
        """
        psid = webhook_payload.sender_id
        message = webhook_payload.message_text or ""

        self.logger.info("message_processing_start", psid=psid, message=message)

        try:
            # Load conversation context
            context = await self.context_manager.get_context(psid)

            # Classify intent
            classification = await self.classifier.classify(message, context)

            # Update context with classification
            classification_dict = {
                "intent": classification.intent.value,
                "entities": classification.entities.model_dump(
                    exclude_none=True, exclude_defaults=True
                ),
                "raw_message": classification.raw_message,
            }
            await self.context_manager.update_classification(psid, classification_dict)

            # Route to appropriate handler based on intent
            response = await self._route_response(
                psid, classification, context
            )

            self.logger.info(
                "message_processing_complete",
                psid=psid,
                intent=classification.intent.value,
                response_sent=response.text,
            )

            return response

        except Exception as e:
            self.logger.error("message_processing_failed", psid=psid, error=str(e))
            # Return friendly error message
            return MessengerResponse(
                text="Sorry, I encountered an error. Please try again or type 'human' for help.",
                recipient_id=psid,
            )

    async def process_postback(
        self,
        webhook_payload: FacebookWebhookPayload,
    ) -> MessengerResponse:
        """Process postback callback from button tap.

        Args:
            webhook_payload: Parsed Facebook webhook payload

        Returns:
            Messenger response to send to user
        """
        psid = webhook_payload.sender_id
        payload = webhook_payload.postback_payload or ""

        self.logger.info("postback_processing_start", psid=psid, payload=payload)

        try:
            # Load conversation context
            context = await self.context_manager.get_context(psid)

            # Parse postback payload: "ACTION:{param1}:{param2}"
            parts = payload.split(":")
            action = parts[0] if parts else ""

            # Cart management actions
            if action == "remove_item" and len(parts) == 2:
                variant_id = parts[1]
                return await self._handle_remove_item(psid, variant_id, context)

            elif action == "increase_quantity" and len(parts) == 2:
                variant_id = parts[1]
                return await self._handle_adjust_quantity(
                    psid, variant_id, "increase", context
                )

            elif action == "decrease_quantity" and len(parts) == 2:
                variant_id = parts[1]
                return await self._handle_adjust_quantity(
                    psid, variant_id, "decrease", context
                )

            # Continue shopping action
            elif action == "continue_shopping":
                return MessengerResponse(
                    text="What else can I help you find? Type a product or category.",
                    recipient_id=psid,
                )

            # Add to cart action (from Story 2.5)
            elif action == "ADD_TO_CART" and len(parts) == 3:
                product_id = parts[1]
                variant_id = parts[2]

                # Use unified add-to-cart helper
                return await self._perform_add_to_cart(
                    psid=psid,
                    product_id=product_id,
                    variant_id=variant_id,
                    context=context
                )

            # Browse/Search products (empty cart actions)
            elif action == "browse_products":
                return MessengerResponse(
                    text="What category of products are you interested in?",
                    recipient_id=psid,
                )

            elif action == "search_products":
                return MessengerResponse(
                    text="What would you like to search for?",
                    recipient_id=psid,
                )

            else:
                return MessengerResponse(
                    text="Sorry, I didn't understand that action. Please try again.",
                    recipient_id=psid,
                )

        except Exception as e:
            self.logger.error("postback_processing_failed", psid=psid, error=str(e))
            return MessengerResponse(
                text="Sorry, I encountered an error. Please try again.",
                recipient_id=psid,
            )

    async def _route_response(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Route classification result to appropriate response.

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification result
            context: Conversation context

        Returns:
            Messenger response
        """
        intent = classification.intent

        # Check for low confidence - trigger clarification flow for product search
        if intent == IntentType.PRODUCT_SEARCH:
            clarification_service = ClarificationService()
            needs_clarification = await clarification_service.needs_clarification(
                classification=classification,
                context=context,
            )

            if needs_clarification:
                return await self._handle_clarification_flow(
                    psid=psid,
                    classification=classification,
                    context=context,
                )

            # No clarification needed - proceed to product search
            return await self._proceed_to_search(psid, classification, context)

        elif intent == IntentType.GREETING:
            return MessengerResponse(
                text="Hi! How can I help you today?",
                recipient_id=psid,
            )

        elif intent == IntentType.CART_VIEW:
            return await self._handle_view_cart(psid, context)

        elif intent == IntentType.CART_ADD:
            return await self._handle_cart_add(psid, classification, context)

        elif intent == IntentType.CHECKOUT:
            return MessengerResponse(
                text="Checkout feature will be implemented in Story 2.8.",
                recipient_id=psid,
            )

        elif intent == IntentType.ORDER_TRACKING:
            return MessengerResponse(
                text="Order tracking feature will be implemented in Story 4.1.",
                recipient_id=psid,
            )

        elif intent == IntentType.HUMAN_HANDOFF:
            return MessengerResponse(
                text="Connecting you to a human agent...",
                recipient_id=psid,
            )

        else:  # UNKNOWN or unhandled
            return MessengerResponse(
                text="I'm not sure what you're looking for. Could you provide more details?",
                recipient_id=psid,
            )

    async def _handle_clarification_flow(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle the clarification flow for low-confidence intents.

        CRITICAL FIX: This method only returns MessengerResponse.
        The webhook handler (facebook.py) handles sending - we do NOT send here.

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification
            context: Conversation context

        Returns:
            Messenger response (to be sent by webhook handler)
        """
        clarification_service = ClarificationService()

        # Check if this is a clarification response
        clarification_state = context.get("clarification", {})
        is_clarification_response = clarification_state.get("active", False)

        if is_clarification_response:
            # FIRST: Check if confidence improved after clarification response
            if (
                classification.confidence
                >= ClarificationService.CONFIDENCE_THRESHOLD
            ):
                # Confidence improved, proceed to search
                await self.context_manager.update_clarification_state(
                    psid, {"active": False}
                )
                return await self._proceed_to_search(psid, classification, context)
            # SECOND: If still low confidence, check if we should fallback to assumptions
            elif await clarification_service.should_fallback_to_assumptions(context):
                # Fallback to assumptions
                message, assumed = await clarification_service.generate_assumption_message(
                    classification=classification,
                    context=context,
                )

                # Clear clarification state
                await self.context_manager.update_clarification_state(psid, {"active": False})

                # Proceed to search with suppressed summary (sends carousel only)
                await self._proceed_to_search(psid, classification, context, suppress_summary=True)

                # Return assumption message for webhook handler to send
                return MessengerResponse(
                    text=message,
                    recipient_id=psid,
                )
            else:
                # Still low confidence, ask another question
                return await self._ask_next_clarification_question(
                    psid=psid,
                    classification=classification,
                    context=context,
                )
        else:
            # First clarification question
            return await self._ask_next_clarification_question(
                psid=psid,
                classification=classification,
                context=context,
            )

    async def _ask_next_clarification_question(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Ask the next clarification question.

        CRITICAL FIX: This method only returns MessengerResponse.
        The webhook handler (facebook.py) handles sending - we do NOT send here.

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification
            context: Conversation context

        Returns:
            Messenger response (to be sent by webhook handler)
        """
        # Generate next question (returns tuple of question and constraint)
        generator = QuestionGenerator()
        clarification_state = context.get("clarification", {})
        questions_asked = clarification_state.get("questions_asked", [])

        question, constraint_asked = await generator.generate_next_question(
            classification=classification,
            questions_asked=questions_asked,
        )

        # Update clarification state
        attempt_count = clarification_state.get("attempt_count", 0)

        await self.context_manager.update_clarification_state(
            psid,
            {
                "active": True,
                "attempt_count": attempt_count + 1,
                "questions_asked": questions_asked + [constraint_asked],
                "last_question": question,
            },
        )

        # Return response for webhook handler to send (NOT sending here)
        return MessengerResponse(
            text=question,
            recipient_id=psid,
        )

    async def _proceed_to_search(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
        suppress_summary: bool = False,
    ) -> MessengerResponse:
        """Proceed to product search after clarification.

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification
            context: Conversation context
            suppress_summary: If True, return empty response (for fallback flow)

        Returns:
            Messenger response (empty if suppress_summary=True)
        """
        # Clear clarification state if active
        if context.get("clarification", {}).get("active", False):
            await self.context_manager.update_clarification_state(psid, {"active": False})

        # Search for products
        search_service = ProductSearchService()
        search_result = await search_service.search_products(classification.entities)

        # Update context
        await self.context_manager.update_search_results(
            psid,
            {
                "products": [
                    p.model_dump(exclude_none=True, exclude_defaults=True)
                    for p in search_result.products
                ],
                "total_count": search_result.total_count,
                "search_params": search_result.search_params,
                "searched_at": search_result.search_time_ms,
            },
        )

        # Format and send
        formatter = MessengerProductFormatter()
        message_payload = formatter.format_product_results(search_result)

        send_service = MessengerSendService()
        await send_service.send_message(psid, message_payload)
        await send_service.close()

        # Return empty response if suppressing summary (e.g., fallback flow)
        if suppress_summary:
            return MessengerResponse(
                text="",
                recipient_id=psid,
            )

        return MessengerResponse(
            text=f"Found {search_result.total_count} product(s) for you!",
            recipient_id=psid,
        )

    async def _perform_add_to_cart(
        self,
        psid: str,
        product_id: str,
        variant_id: str,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Unified add-to-cart logic for button taps and natural language.

        Handles product lookup, availability checking, and cart addition.

        Args:
            psid: Facebook Page-Scoped ID
            product_id: Shopify product ID
            variant_id: Shopify variant ID
            context: Conversation context with product search results

        Returns:
            Messenger response with confirmation or error
        """
        # Get cart service using shared Redis client from context manager
        cart_service = CartService(redis_client=self.context_manager.redis)

        # Extract product info from context (last viewed products)
        last_search = context.get("last_search_results", {})
        products = last_search.get("products", [])

        if not products:
            self.logger.warning("cart_add_no_products", psid=psid)
            return MessengerResponse(
                text="Sorry, I don't know which product to add. Please search for products first.",
                recipient_id=psid,
            )

        # Find the product in last search results
        product_data = None
        variant_data = None

        for p in products:
            if p.get("id") == product_id:
                product_data = p
                # Find variant
                for v in p.get("variants", []):
                    if v.get("id") == variant_id:
                        variant_data = v
                        break
                break

        if not product_data:
            self.logger.warning("cart_add_product_not_found", psid=psid, product_id=product_id)
            return MessengerResponse(
                text="Sorry, I couldn't find that product. Please search again.",
                recipient_id=psid,
            )

        if not variant_data:
            self.logger.warning("cart_add_variant_not_found", psid=psid, variant_id=variant_id)
            return MessengerResponse(
                text="Sorry, that product variant is not available.",
                recipient_id=psid,
            )

        # Check availability
        if not variant_data.get("available_for_sale", False):
            self.logger.info(
                "cart_add_out_of_stock",
                psid=psid,
                product_id=product_id,
                variant_id=variant_id
            )
            return MessengerResponse(
                text=f"Sorry, '{product_data.get('title')}' is currently out of stock.",
                recipient_id=psid,
            )

        # Add to cart
        try:
            cart = await cart_service.add_item(
                psid=psid,
                product_id=product_id,
                variant_id=variant_id,
                title=product_data.get("title"),
                price=variant_data.get("price"),
                image_url=product_data.get("images", [{}])[0].get("url", ""),
                currency_code=variant_data.get("currency_code", "USD"),
                quantity=1
            )

            self.logger.info(
                "cart_add_success",
                psid=psid,
                product_id=product_id,
                variant_id=variant_id,
                item_count=cart.item_count
            )

            return MessengerResponse(
                text=f"Added {product_data.get('title')} (${variant_data.get('price')}) to your cart. View cart: [View Cart] button or type 'cart'",
                recipient_id=psid,
            )

        except Exception as e:
            self.logger.error("cart_add_failed", psid=psid, product_id=product_id, error=str(e))
            return MessengerResponse(
                text="Sorry, I encountered an error adding that item to your cart. Please try again.",
                recipient_id=psid,
            )

    async def _handle_cart_add(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle cart add intent (natural language "add to cart").

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification
            context: Conversation context

        Returns:
            Messenger response
        """
        # Extract product info from context (last viewed products)
        last_search = context.get("last_search_results", {})
        products = last_search.get("products", [])

        if not products:
            return MessengerResponse(
                text="Sorry, I don't know which product to add. Please search for products first.",
                recipient_id=psid,
            )

        # Get first product from last search (or extract from entities)
        entities = classification.entities.model_dump()
        product_id = entities.get("product_id", products[0].get("id"))
        variant_id = entities.get("variant_id", products[0].get("variants", [{}])[0].get("id"))

        # Use unified add-to-cart helper
        return await self._perform_add_to_cart(
            psid=psid,
            product_id=product_id,
            variant_id=variant_id,
            context=context
        )

    async def _handle_view_cart(
        self,
        psid: str,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle cart view intent.

        Args:
            psid: Facebook Page-Scoped ID
            context: Conversation context

        Returns:
            Messenger response with cart display
        """
        # Get cart service
        cart_service = CartService(redis_client=self.context_manager.redis)

        # Get cart
        try:
            cart = await cart_service.get_cart(psid)

            # Format cart for display
            from app.core.config import settings
            config = settings()
            shop_domain = config.get("STORE_URL", "https://shop.example.com").replace("https://", "").replace("http://", "")
            formatter = CartFormatter(shop_domain=shop_domain)
            message_payload = formatter.format_cart(cart, psid)

            # Send the formatted cart message
            send_service = MessengerSendService()
            await send_service.send_message(psid, message_payload)
            await send_service.close()

            # Return empty text response (attachment already sent)
            return MessengerResponse(text="", recipient_id=psid)

        except Exception as e:
            self.logger.error("view_cart_failed", psid=psid, error=str(e))
            return MessengerResponse(
                text="Sorry, I couldn't retrieve your cart. Please try again.",
                recipient_id=psid,
            )

    async def _handle_remove_item(
        self,
        psid: str,
        variant_id: str,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle remove item from cart.

        Args:
            psid: Facebook Page-Scoped ID
            variant_id: Variant ID to remove
            context: Conversation context

        Returns:
            Messenger response with updated cart display
        """
        cart_service = CartService(redis_client=self.context_manager.redis)

        try:
            # Get cart before removal (for product name)
            cart = await cart_service.get_cart(psid)
            removed_item = None
            for item in cart.items:
                if item.variant_id == variant_id:
                    removed_item = item
                    break

            # Remove item
            cart = await cart_service.remove_item(psid, variant_id)

            # Format updated cart for display
            from app.core.config import settings
            config = settings()
            shop_domain = config.get("STORE_URL", "https://shop.example.com").replace("https://", "").replace("http://", "")
            formatter = CartFormatter(shop_domain=shop_domain)
            message_payload = formatter.format_cart(cart, psid)

            # Send updated cart display
            send_service = MessengerSendService()
            await send_service.send_message(psid, message_payload)
            await send_service.close()

            # Log removal
            self.logger.info(
                "cart_item_removed",
                psid=psid,
                variant_id=variant_id,
                item_title=removed_item.title if removed_item else "unknown"
            )

            # Return text message with confirmation
            prefix = f"Removed {removed_item.title if removed_item else 'item'} from cart. "
            if not cart.items:
                prefix += "Your cart is now empty. Let's find some more products!"

            return MessengerResponse(text=prefix, recipient_id=psid)

        except Exception as e:
            self.logger.error("remove_item_failed", psid=psid, variant_id=variant_id, error=str(e))
            return MessengerResponse(
                text="Sorry, I couldn't remove that item. Please try again.",
                recipient_id=psid,
            )

    async def _handle_adjust_quantity(
        self,
        psid: str,
        variant_id: str,
        adjustment: str,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle quantity adjustment.

        Args:
            psid: Facebook Page-Scoped ID
            variant_id: Variant ID to adjust
            adjustment: "increase" or "decrease"
            context: Conversation context

        Returns:
            Messenger response with updated cart display
        """
        cart_service = CartService(redis_client=self.context_manager.redis)

        try:
            # Get current cart
            cart = await cart_service.get_cart(psid)

            # Find item and calculate new quantity
            current_quantity = 1
            for item in cart.items:
                if item.variant_id == variant_id:
                    current_quantity = item.quantity
                    break

            # Calculate new quantity
            if adjustment == "increase":
                new_quantity = min(current_quantity + 1, CartService.MAX_QUANTITY)
            else:  # decrease
                new_quantity = max(current_quantity - 1, 1)

            # Update quantity
            cart = await cart_service.update_quantity(psid, variant_id, new_quantity)

            # Format updated cart for display
            from app.core.config import settings
            config = settings()
            shop_domain = config.get("STORE_URL", "https://shop.example.com").replace("https://", "").replace("http://", "")
            formatter = CartFormatter(shop_domain=shop_domain)
            message_payload = formatter.format_cart(cart, psid)

            # Send updated cart display
            send_service = MessengerSendService()
            await send_service.send_message(psid, message_payload)
            await send_service.close()

            # Log adjustment
            self.logger.info(
                "cart_quantity_adjusted",
                psid=psid,
                variant_id=variant_id,
                adjustment=adjustment,
                new_quantity=new_quantity
            )

            # Return empty response (attachment sent)
            return MessengerResponse(text="", recipient_id=psid)

        except Exception as e:
            self.logger.error(
                "adjust_quantity_failed",
                psid=psid,
                variant_id=variant_id,
                adjustment=adjustment,
                error=str(e)
            )
            return MessengerResponse(
                text="Sorry, I couldn't update the quantity. Please try again.",
                recipient_id=psid,
            )
