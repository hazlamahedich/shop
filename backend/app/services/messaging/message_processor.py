"""Message processing orchestrator for webhook → classify → respond flow.

Coordinates intent classification, context management, and response
routing for incoming Facebook Messenger messages.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog

from app.schemas.messaging import (
    ConversationContext,
    FacebookWebhookPayload,
    MessengerResponse,
)
from app.services.intent import IntentClassifier, IntentType
from app.services.messaging.conversation_context import ConversationContextManager


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
                "entities": classification.entities.model_dump(exclude_none=True, exclude_defaults=True),
                "raw_message": classification.raw_message,
            }
            await self.context_manager.update_classification(psid, classification_dict)

            # Route to appropriate handler based on intent
            response = await self._route_response(classification, context)

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

    async def _route_response(
        self,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Route classification result to appropriate response.

        Args:
            classification: Intent classification result
            context: Conversation context

        Returns:
            Messenger response
        """
        intent = classification.intent

        # Check for low confidence - trigger clarification
        if classification.needs_clarification:
            return MessengerResponse(
                text="I'm not sure what you're looking for. Could you provide more details?",
                recipient_id=context.get("psid", ""),
            )

        # Route based on intent
        if intent == IntentType.PRODUCT_SEARCH:
            # Placeholder for product search (Story 2.2)
            entities = classification.entities.model_dump(exclude_none=True, exclude_defaults=True)
            response_text = "Searching for products"
            if entities.get("category"):
                response_text += f" in {entities['category']}"
            if entities.get("budget"):
                response_text += f" under ${entities['budget']}"
            response_text += ". This feature will be implemented in Story 2.2."

            return MessengerResponse(
                text=response_text,
                recipient_id=context.get("psid", ""),
            )

        elif intent == IntentType.GREETING:
            return MessengerResponse(
                text="Hi! How can I help you today?",
                recipient_id=context.get("psid", ""),
            )

        elif intent == IntentType.CART_VIEW:
            return MessengerResponse(
                text="Your cart is empty. This feature will be implemented in Story 2.6.",
                recipient_id=context.get("psid", ""),
            )

        elif intent == IntentType.CHECKOUT:
            return MessengerResponse(
                text="Checkout feature will be implemented in Story 2.8.",
                recipient_id=context.get("psid", ""),
            )

        elif intent == IntentType.ORDER_TRACKING:
            return MessengerResponse(
                text="Order tracking feature will be implemented in Story 4.1.",
                recipient_id=context.get("psid", ""),
            )

        elif intent == IntentType.HUMAN_HANDOFF:
            return MessengerResponse(
                text="Connecting you to a human agent...",
                recipient_id=context.get("psid", ""),
            )

        else:  # UNKNOWN or unhandled
            return MessengerResponse(
                text="I'm not sure what you're looking for. Could you provide more details?",
                recipient_id=context.get("psid", ""),
            )
