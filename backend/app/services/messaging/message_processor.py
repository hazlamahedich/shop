"""Message processing orchestrator for webhook → classify → respond flow.

.. deprecated:: 5-11
    MessageProcessor is deprecated. Use UnifiedConversationService via
    MessengerAdapter for new implementations. This class is kept for
    backward compatibility during the transition period.

    Migration guide:
        - Replace MessageProcessor.process_message() with UnifiedConversationService.process_message()
        - Use MessengerAdapter for Facebook Messenger integration
        - See Story 5-11 for full migration details

Coordinates intent classification, context management, and response
routing for incoming Facebook Messenger messages.
"""

from __future__ import annotations

import warnings
from datetime import UTC
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.messaging import (
    FacebookWebhookPayload,
    MessengerResponse,
)
from app.services.cart import CartService
from app.services.checkout import CheckoutService
from app.services.checkout.checkout_schema import CheckoutStatus
from app.services.clarification import ClarificationService
from app.services.clarification.question_generator import QuestionGenerator
from app.services.consent import ConsentService, ConsentStatus
from app.services.cost_tracking.budget_alert_service import BudgetAlertService
from app.services.faq import match_faq, rephrase_faq_with_personality
from app.services.handoff import HandoffDetector
from app.services.handoff.business_hours_handoff_service import BusinessHoursHandoffService
from app.services.intent import IntentClassifier, IntentType
from app.services.messaging.conversation_context import ConversationContextManager
from app.services.messenger import CartFormatter, MessengerProductFormatter, MessengerSendService
from app.services.order_tracking import OrderLookupType, OrderTrackingService
from app.models.merchant import PersonalityType
from app.services.personality import BotResponseService
from app.services.personality.messenger_templates import register_messenger_templates
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.session import SessionService

register_messenger_templates()
from app.services.shopify import ProductSearchService
from app.services.shopify_storefront import ShopifyStorefrontClient

logger = structlog.get_logger(__name__)


class MessageProcessor:
    """Orchestrates message processing: webhook → classify → respond.

    .. deprecated:: 5-11
        Use UnifiedConversationService via MessengerAdapter instead.
        This class is deprecated and will be removed in a future version.

        For Messenger integration:
            adapter = MessengerAdapter()
            context = adapter.create_context(psid, merchant_id)
            service = UnifiedConversationService(db=db)
            response = await service.process_message(db, context, message)

    Attributes:
        classifier: Intent classifier for message classification
        context_manager: Conversation context manager
        consent_service: Consent management service
        session_service: Session management service
        merchant_id: Merchant ID for personality-based responses
        db: Database session for credential lookup
    """

    def __init__(
        self,
        classifier: IntentClassifier | None = None,
        context_manager: ConversationContextManager | None = None,
        consent_service: ConsentService | None = None,
        session_service: SessionService | None = None,
        merchant_id: int | None = None,
        db: AsyncSession | None = None,
    ) -> None:
        """Initialize message processor.

        .. deprecated:: 5-11
            Use UnifiedConversationService via MessengerAdapter instead.

        Args:
            classifier: Intent classifier (uses default if not provided)
            context_manager: Conversation context manager (uses default if not provided)
            consent_service: Consent service (uses default if not provided)
            session_service: Session service (uses default if not provided)
            merchant_id: Merchant ID for personality-based responses (Story 1.10)
            db: Database session for Shopify credential lookup
        """
        warnings.warn(
            "MessageProcessor is deprecated. Use UnifiedConversationService via MessengerAdapter. "
            "See Story 5-11 for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.classifier = classifier or IntentClassifier()
        self.context_manager = context_manager or ConversationContextManager()
        self.logger = structlog.get_logger(__name__)
        self.merchant_id = merchant_id
        self.db = db

        redis_client = self.context_manager.redis
        self.consent_service = consent_service or ConsentService(redis_client=redis_client)
        self.session_service = session_service or SessionService(
            redis_client=redis_client, consent_service=self.consent_service
        )

        self._redis_client = redis_client
        self._checkout_service: CheckoutService | None = None
        self._shopify_client: ShopifyStorefrontClient | None = None

        self._bot_response_service: BotResponseService | None = None

        self._handoff_detector: HandoffDetector | None = None

        self._order_tracking_service: OrderTrackingService | None = None

        self._personality: PersonalityType | None = None

    async def _get_shopify_client(self) -> ShopifyStorefrontClient:
        """Get or create a Shopify client for the merchant.

        Returns:
            ShopifyStorefrontClient configured for the merchant's store
        """
        if self._shopify_client:
            return self._shopify_client

        if self.merchant_id and self.db:
            from sqlalchemy import select

            from app.core.security import decrypt_access_token
            from app.models.shopify_integration import ShopifyIntegration

            result = await self.db.execute(
                select(ShopifyIntegration).where(ShopifyIntegration.merchant_id == self.merchant_id)
            )
            integration = result.scalars().first()

            if (
                integration
                and integration.status == "active"
                and integration.storefront_token_encrypted
            ):
                storefront_token = decrypt_access_token(integration.storefront_token_encrypted)
                self._shopify_client = ShopifyStorefrontClient(
                    shop_domain=integration.shop_domain,
                    access_token=storefront_token,
                )
                self.logger.info(
                    "shopify_client_created_for_merchant",
                    merchant_id=self.merchant_id,
                    shop_domain=integration.shop_domain,
                )
                return self._shopify_client

        self._shopify_client = ShopifyStorefrontClient()
        return self._shopify_client

    async def _get_checkout_service(self) -> CheckoutService:
        """Get or create a checkout service with merchant-specific Shopify client."""
        if self._checkout_service:
            return self._checkout_service

        shopify_client = await self._get_shopify_client()
        cart_service = CartService(redis_client=self._redis_client)
        self._checkout_service = CheckoutService(
            redis_client=self._redis_client,
            shopify_client=shopify_client,
            cart_service=cart_service,
        )
        return self._checkout_service

    def _get_bot_response_service(self) -> BotResponseService:
        """Get or create bot response service (lazy initialization)."""
        if self._bot_response_service is None:
            self._bot_response_service = BotResponseService()
        return self._bot_response_service

    def _get_handoff_detector(self) -> HandoffDetector:
        """Get or create handoff detector (lazy initialization)."""
        if self._handoff_detector is None:
            self._handoff_detector = HandoffDetector(redis_client=self.context_manager.redis)
        return self._handoff_detector

    def _get_order_tracking_service(self) -> OrderTrackingService:
        """Get or create order tracking service (lazy initialization)."""
        if self._order_tracking_service is None:
            self._order_tracking_service = OrderTrackingService()
        return self._order_tracking_service

    async def _get_personality(self) -> PersonalityType:
        """Load merchant personality from DB (Story 11-5).

        Caches result per-instance since personality doesn't change
        during a processor's lifetime.

        Returns:
            PersonalityType for the merchant, defaults to FRIENDLY.
        """
        if self._personality is not None:
            return self._personality
        if not self.merchant_id:
            self._personality = PersonalityType.FRIENDLY
            return self._personality
        try:
            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.merchant import Merchant

            async with async_session()() as db:
                result = await db.execute(select(Merchant).where(Merchant.id == self.merchant_id))
                merchant = result.scalars().first()
                if merchant and merchant.personality:
                    self._personality = merchant.personality
                    return self._personality
        except Exception as e:
            self.logger.warning(
                "personality_load_failed", merchant_id=self.merchant_id, error=str(e)
            )
        self._personality = PersonalityType.FRIENDLY
        return self._personality

    def _fmt(self, key: str, personality: PersonalityType, **kwargs: Any) -> str:
        """Format a messenger template with personality (Story 11-5)."""
        return PersonalityAwareResponseFormatter.format_response(
            "messenger", key, personality, validate=True, **kwargs
        )

    async def _get_personality_greeting(self) -> str:
        """Get personality-based greeting message (Story 1.10, 11-5)."""
        personality = await self._get_personality()
        return self._fmt("greeting", personality)

    async def _get_personality_error(self) -> str:
        """Get personality-based error message (Story 1.10, 11-5)."""
        personality = await self._get_personality()
        return self._fmt("error", personality)

    async def _get_handoff_message(self) -> str:
        """Get business hours-aware handoff message (Stories 3.10, 4-12)."""
        personality = await self._get_personality()
        if not self.merchant_id:
            return self._fmt("handoff", personality)

        try:
            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.merchant import Merchant

            async with async_session()() as db:
                result = await db.execute(select(Merchant).where(Merchant.id == self.merchant_id))
                merchant = result.scalars().first()

                if not merchant:
                    return self._fmt("handoff", personality)

                service = BusinessHoursHandoffService()
                return service.build_handoff_message(merchant.business_hours_config)

        except Exception as e:
            self.logger.warning(
                "handoff_message_failed", merchant_id=self.merchant_id, error=str(e)
            )
            return self._fmt("handoff", personality)

    async def _check_handoff(
        self,
        message: str,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse | None:
        """Check if handoff should be triggered (Story 4-5).

        Checks for:
        1. Keyword detection (human, agent, etc.)
        2. Low confidence scores (3 consecutive < 0.50)
        3. Clarification loops (3 same-type questions)

        Args:
            message: Customer message
            psid: Facebook Page-Scoped ID
            classification: Intent classification result
            context: Conversation context

        Returns:
            MessengerResponse with handoff message if triggered, None otherwise
        """
        if not self.merchant_id:
            return None

        conversation = await self._get_conversation(psid)
        conversation_id = conversation.id if conversation else self.merchant_id

        detector = self._get_handoff_detector()
        clarification_type = None
        clarification_state = context.get("clarification", {})
        if clarification_state.get("active"):
            clarification_type = clarification_state.get("last_type")

        result = await detector.detect(
            message=message,
            conversation_id=conversation_id,
            confidence_score=getattr(classification, "confidence", None),
            clarification_type=clarification_type,
        )

        if result.should_handoff:
            self.logger.info(
                "handoff_triggered",
                psid=psid,
                conversation_id=conversation_id,
                reason=result.reason.value if result.reason else None,
                confidence_count=result.confidence_count,
                matched_keyword=result.matched_keyword,
                loop_count=result.loop_count,
            )

            await self._update_conversation_handoff_status(
                psid=psid,
                reason=result.reason.value if result.reason else "unknown",
                confidence_count=result.confidence_count,
            )

            handoff_msg = await self._get_handoff_message()
            return MessengerResponse(
                text=handoff_msg,
                recipient_id=psid,
            )

        if result.confidence_count == 0 and result.reason is None:
            await detector.reset_state(conversation_id)

        return None

    async def _get_conversation(self, psid: str) -> Any | None:
        """Get conversation for a PSID.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Conversation model or None
        """
        if not self.merchant_id:
            return None

        try:
            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.conversation import Conversation

            async with async_session()() as db:
                result = await db.execute(
                    select(Conversation)
                    .where(
                        Conversation.merchant_id == self.merchant_id,
                        Conversation.platform_sender_id == psid,
                    )
                    .order_by(Conversation.updated_at.desc())
                    .limit(1)
                )
                return result.scalars().first()
        except Exception as e:
            self.logger.warning("get_conversation_failed", psid=psid, error=str(e))
            return None

    async def _update_conversation_handoff_status(
        self,
        psid: str,
        reason: str,
        confidence_count: int = 0,
    ) -> None:
        """Update conversation status in database when handoff triggers.

        Args:
            psid: Facebook Page-Scoped ID
            reason: Handoff trigger reason
            confidence_count: Consecutive low confidence count at time of handoff
        """
        if not self.merchant_id:
            return

        try:
            from datetime import datetime

            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.conversation import Conversation

            async with async_session()() as db:
                result = await db.execute(
                    select(Conversation)
                    .where(
                        Conversation.merchant_id == self.merchant_id,
                        Conversation.platform_sender_id == psid,
                    )
                    .order_by(Conversation.updated_at.desc())
                    .limit(1)
                )
                conversation = result.scalars().first()

                if conversation:
                    conversation.status = "handoff"
                    conversation.handoff_status = "pending"
                    conversation.handoff_triggered_at = datetime.utcnow()
                    conversation.handoff_reason = reason
                    conversation.consecutive_low_confidence_count = confidence_count
                    await db.commit()

                    self.logger.info(
                        "handoff_status_updated",
                        conversation_id=conversation.id,
                        psid=psid,
                        reason=reason,
                        confidence_count=confidence_count,
                    )

        except Exception as e:
            self.logger.error(
                "handoff_status_update_failed",
                psid=psid,
                reason=reason,
                error=str(e),
            )

    async def _check_faq_match(
        self,
        message: str,
    ) -> MessengerResponse | None:
        """Check if message matches any FAQ (Story 1.11).

        Applies personality rephrasing to FAQ answers for consistent bot tone.

        Args:
            message: Customer's message

        Returns:
            MessengerResponse with FAQ answer if match found, None otherwise
        """
        if not self.merchant_id:
            return None

        try:
            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.merchant import Merchant, PersonalityType

            async with async_session()() as db:
                # Get merchant with personality and LLM config
                merchant_result = await db.execute(
                    select(Merchant).where(Merchant.id == self.merchant_id)
                )
                merchant = merchant_result.scalars().first()

                # Get merchant's FAQs
                result = await db.execute(
                    select(self._get_faq_model())
                    .where(self._get_faq_model().merchant_id == self.merchant_id)
                    .order_by(self._get_faq_model().order_index)
                )
                faqs = result.scalars().all()

                if not faqs:
                    return None

                # Try to match FAQ
                faq_match = await match_faq(message, list(faqs))

                if faq_match:
                    self.logger.info(
                        "faq_matched",
                        merchant_id=self.merchant_id,
                        faq_id=faq_match.faq.id,
                        confidence=faq_match.confidence,
                    )

                    # Get merchant details for personality rephrasing
                    business_name = merchant.business_name if merchant else None
                    bot_name = merchant.bot_name if merchant and merchant.bot_name else "Mantisbot"
                    personality_type = (
                        merchant.personality
                        if merchant and merchant.personality
                        else PersonalityType.FRIENDLY
                    )

                    # Get LLM service for rephrasing
                    faq_answer = faq_match.faq.answer
                    try:
                        llm_service = await self._get_llm_service_for_faq(merchant, db)
                        if llm_service:
                            faq_answer = await rephrase_faq_with_personality(
                                llm_service=llm_service,
                                faq_answer=faq_match.faq.answer,
                                personality_type=personality_type,
                                business_name=business_name or "our store",
                                bot_name=bot_name,
                            )
                            self.logger.info(
                                "faq_rephrased",
                                merchant_id=self.merchant_id,
                                faq_id=faq_match.faq.id,
                            )
                    except Exception as e:
                        self.logger.warning(
                            "faq_rephrase_failed_using_original",
                            merchant_id=self.merchant_id,
                            error=str(e),
                        )

                    # Include business name in response if available
                    if business_name:
                        return MessengerResponse(
                            text=f"{business_name}\n\n{faq_answer}",
                            recipient_id="",  # Will be set by caller
                        )
                    return MessengerResponse(
                        text=faq_answer,
                        recipient_id="",  # Will be set by caller
                    )
        except Exception as e:
            self.logger.warning("faq_match_failed", error=str(e))

        return None

    async def _get_llm_service_for_faq(self, merchant, db):
        """Get LLM service for FAQ rephrasing.

        Args:
            merchant: Merchant model with LLM configuration
            db: Database session

        Returns:
            LLM service instance or None if unavailable
        """
        from app.core.security import decrypt_access_token
        from app.services.llm.llm_factory import LLMProviderFactory

        try:
            if hasattr(merchant, "llm_configuration") and merchant.llm_configuration:
                llm_config = merchant.llm_configuration
                provider_name = llm_config.provider or "ollama"

                config = {
                    "model": llm_config.ollama_model or llm_config.cloud_model,
                }

                if provider_name == "ollama":
                    config["ollama_url"] = llm_config.ollama_url
                else:
                    if llm_config.api_key_encrypted:
                        config["api_key"] = decrypt_access_token(llm_config.api_key_encrypted)

                return LLMProviderFactory.create_provider(
                    provider_name=provider_name,
                    config=config,
                )
        except Exception as e:
            self.logger.warning(
                "faq_llm_service_failed",
                merchant_id=merchant.id if merchant else None,
                error=str(e),
            )

        # Fallback to default Ollama
        try:
            return LLMProviderFactory.create_provider(
                provider_name="ollama",
                config={"model": "llama3.2"},
            )
        except Exception:
            return None

    def _get_faq_model(self):
        """Get FAQ model (lazy import to avoid circular dependency)."""
        from app.models.faq import Faq

        return Faq

    async def _get_business_name(self, db) -> str | None:
        """Get business name for merchant (Story 1.11).

        Args:
            db: Database session

        Returns:
            Business name if set, None otherwise
        """
        if not self.merchant_id:
            return None

        try:
            from sqlalchemy import select

            from app.models.merchant import Merchant

            result = await db.execute(
                select(Merchant.business_name).where(Merchant.id == self.merchant_id)
            )
            business_name = result.scalar_one_or_none()
            return business_name
        except Exception as e:
            self.logger.warning("get_business_name_failed", error=str(e))
            return None

    def should_bot_respond(self, conversation, message: str) -> bool:
        """Determine if bot should respond based on hybrid mode state.

        Story 4-9: When hybrid mode is active, the bot only responds to
        @bot mentions. Otherwise, it responds normally.

        Args:
            conversation: Conversation model with conversation_data field
            message: Customer message text

        Returns:
            True if bot should respond, False to stay silent
        """
        from datetime import datetime

        conversation_data = conversation.conversation_data if conversation else {}
        hybrid_mode = conversation_data.get("hybrid_mode", {}) if conversation_data else {}

        if hybrid_mode.get("enabled"):
            expires_at = hybrid_mode.get("expires_at")
            if expires_at:
                try:
                    expires_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if datetime.now(UTC) > expires_dt:
                        self.logger.info(
                            "hybrid_mode_expired",
                            conversation_id=conversation.id if conversation else None,
                        )
                        return True
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        "hybrid_mode_malformed_expiry",
                        conversation_id=conversation.id if conversation else None,
                        expires_at=expires_at,
                        error=str(e),
                    )
                    return True

            if "@bot" in message.lower():
                self.logger.info(
                    "hybrid_mode_bot_mention",
                    conversation_id=conversation.id if conversation else None,
                )
                return True

            self.logger.info(
                "hybrid_mode_active_silent",
                conversation_id=conversation.id if conversation else None,
            )
            return False

        return True

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
            # Story 3-8: Check if bot is paused due to budget limit
            if self.merchant_id:
                budget_service = BudgetAlertService(
                    db=None,
                    redis_client=self.context_manager.redis,
                )
                is_paused, pause_reason = await budget_service.get_bot_paused_state(
                    self.merchant_id
                )
                if is_paused:
                    self.logger.info(
                        "bot_paused_budget_exceeded",
                        psid=psid,
                        merchant_id=self.merchant_id,
                        pause_reason=pause_reason,
                    )
                    personality = await self._get_personality()
                    return MessengerResponse(
                        text=self._fmt("unavailable", personality),
                        recipient_id=psid,
                    )

            # Check for returning shopper and welcome them if inactive (Story 2.7)
            # We get last activity BEFORE updating it to see if it's a "return"
            last_activity = await self.session_service.get_last_activity(psid)
            is_returning = await self.session_service.is_returning_shopper(psid)

            # Update activity timestamp (Story 2.7)
            await self.session_service.update_activity(psid)

            if is_returning:
                # Welcome back if last activity was > 30 mins ago or never recorded
                should_welcome = True
                if last_activity:
                    from datetime import datetime

                    diff = datetime.now(UTC) - last_activity
                    if diff.total_seconds() < 1800:  # 30 minutes
                        should_welcome = False

                if should_welcome:
                    item_count = await self.session_service.get_cart_item_count(psid)
                    self.logger.info("returning_shopper_welcome", psid=psid, item_count=item_count)
                    personality = await self._get_personality()
                    s = "s" if item_count != 1 else ""
                    welcome_back = self._fmt(
                        "welcome_back", personality, item_count=item_count, s=s
                    )
                    send_service = MessengerSendService()
                    await send_service.send_message(psid, {"text": welcome_back})
                    await send_service.close()

            # Load conversation context
            context = await self.context_manager.get_context(psid)

            # Story 4-9: Check hybrid mode - if active, only respond to @bot mentions
            conversation = await self._get_conversation(psid)
            if conversation:
                should_respond = self.should_bot_respond(conversation, message)
                if not should_respond:
                    self.logger.info(
                        "hybrid_mode_silent",
                        psid=psid,
                        conversation_id=conversation.id,
                    )
                    return MessengerResponse(
                        text="",
                        recipient_id=psid,
                    )

            # Story 1.11: Check for FAQ matches before intent classification
            # If FAQ matches with high confidence, return FAQ answer directly
            faq_response = await self._check_faq_match(message)
            if faq_response:
                self.logger.info(
                    "faq_match_found",
                    psid=psid,
                    message=message[:100],
                )
                return faq_response

            # Classify intent
            classification = await self.classifier.classify(message, context)

            # Story 4-5: Check for handoff triggers
            handoff_result = await self._check_handoff(
                message=message,
                psid=psid,
                classification=classification,
                context=context,
            )
            if handoff_result:
                return handoff_result

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
            response = await self._route_response(psid, classification, context)

            self.logger.info(
                "message_processing_complete",
                psid=psid,
                intent=classification.intent.value,
                response_sent=response.text,
            )

            return response

        except Exception as e:
            self.logger.error("message_processing_failed", psid=psid, error=str(e))
            # Return personality-based error message (Story 1.10)
            error_message = await self._get_personality_error()
            return MessengerResponse(
                text=error_message,
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
            personality = await self._get_personality()

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
                return await self._handle_adjust_quantity(psid, variant_id, "increase", context)

            elif action == "decrease_quantity" and len(parts) == 2:
                variant_id = parts[1]
                return await self._handle_adjust_quantity(psid, variant_id, "decrease", context)

            elif action == "continue_shopping":
                return MessengerResponse(
                    text=self._fmt("postback_continue", personality),
                    recipient_id=psid,
                )

            # Add to cart action (from Story 2.5)
            elif action == "ADD_TO_CART" and len(parts) == 3:
                product_id = parts[1]
                variant_id = parts[2]

                # Use unified add-to-cart helper
                return await self._perform_add_to_cart(
                    psid=psid, product_id=product_id, variant_id=variant_id, context=context
                )

            # Consent response handling (Story 2.7)
            elif action == "CONSENT" and len(parts) >= 3:
                return await self._handle_consent_response(psid, parts)

            # Browse/Search products (empty cart actions)
            elif action == "browse_products":
                return MessengerResponse(
                    text=self._fmt("postback_browse", personality),
                    recipient_id=psid,
                )

            elif action == "search_products":
                return MessengerResponse(
                    text=self._fmt("postback_search", personality),
                    recipient_id=psid,
                )

            else:
                return MessengerResponse(
                    text=self._fmt("postback_unknown", personality),
                    recipient_id=psid,
                )

        except Exception as e:
            self.logger.error("postback_processing_failed", psid=psid, error=str(e))
            return MessengerResponse(
                text=self._fmt("error", personality),
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
            # Use personality-based greeting (Story 1.10)
            greeting = await self._get_personality_greeting()
            return MessengerResponse(
                text=greeting,
                recipient_id=psid,
            )

        elif intent == IntentType.CART_VIEW:
            return await self._handle_view_cart(psid, context)

        elif intent == IntentType.CART_ADD:
            return await self._handle_cart_add(psid, classification, context)

        elif intent == IntentType.CHECKOUT:
            return await self._handle_checkout(psid)

        elif intent == IntentType.ORDER_TRACKING:
            return await self._handle_order_tracking(psid, classification, context)

        elif intent == IntentType.HUMAN_HANDOFF:
            handoff_msg = await self._get_handoff_message()
            return MessengerResponse(
                text=handoff_msg,
                recipient_id=psid,
            )

        elif intent == IntentType.FORGET_PREFERENCES:
            # Story 2.7: Handle forget preferences request
            return await self._handle_forget_preferences(psid)

        else:  # UNKNOWN or unhandled
            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("fallback", personality),
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
            if classification.confidence >= ClarificationService.CONFIDENCE_THRESHOLD:
                # Confidence improved, proceed to search
                await self.context_manager.update_clarification_state(psid, {"active": False})
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
        search_service = ProductSearchService(db=self.db)
        search_result = await search_service.search_products(
            entities=classification.entities,
            merchant_id=self.merchant_id,
        )

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

        Handles product lookup, availability checking, consent check, and cart addition.

        Args:
            psid: Facebook Page-Scoped ID
            product_id: Shopify product ID
            variant_id: Shopify variant ID
            context: Conversation context with product search results

        Returns:
            Messenger response with confirmation or error
        """
        personality = await self._get_personality()

        # Check consent status (Story 2.7: opt-in flow)
        consent_status = await self.consent_service.get_consent(psid)
        if consent_status == ConsentStatus.PENDING:
            return await self._request_consent(psid, product_id, variant_id, context)

        cart_service = CartService(redis_client=self.context_manager.redis)

        last_search = context.get("last_search_results", {})
        products = last_search.get("products", [])

        if not products:
            self.logger.warning("cart_add_no_products", psid=psid)
            return MessengerResponse(
                text=self._fmt("no_product", personality),
                recipient_id=psid,
            )

        product_data = None
        variant_data = None

        for p in products:
            if p.get("id") == product_id:
                product_data = p
                for v in p.get("variants", []):
                    if v.get("id") == variant_id:
                        variant_data = v
                        break
                break

        if not product_data:
            self.logger.warning("cart_add_product_not_found", psid=psid, product_id=product_id)
            return MessengerResponse(
                text=self._fmt("product_not_found", personality),
                recipient_id=psid,
            )

        if not variant_data:
            self.logger.warning("cart_add_variant_not_found", psid=psid, variant_id=variant_id)
            return MessengerResponse(
                text=self._fmt("variant_unavailable", personality),
                recipient_id=psid,
            )

        if not variant_data.get("available_for_sale", False):
            self.logger.info(
                "cart_add_out_of_stock", psid=psid, product_id=product_id, variant_id=variant_id
            )
            return MessengerResponse(
                text=self._fmt("out_of_stock", personality, title=product_data.get("title")),
                recipient_id=psid,
            )

        try:
            cart = await cart_service.add_item(
                psid=psid,
                product_id=product_id,
                variant_id=variant_id,
                title=product_data.get("title"),
                price=variant_data.get("price"),
                image_url=product_data.get("images", [{}])[0].get("url", ""),
                currency_code=variant_data.get("currency_code", "USD"),
                quantity=1,
            )

            self.logger.info(
                "cart_add_success",
                psid=psid,
                product_id=product_id,
                variant_id=variant_id,
                item_count=cart.item_count,
            )

            return MessengerResponse(
                text=self._fmt(
                    "cart_confirm",
                    personality,
                    title=product_data.get("title"),
                    price=variant_data.get("price"),
                ),
                recipient_id=psid,
            )

        except Exception as e:
            self.logger.error("cart_add_failed", psid=psid, product_id=product_id, error=str(e))
            return MessengerResponse(
                text=self._fmt("cart_add_error", personality),
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
            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("no_product", personality),
                recipient_id=psid,
            )

        # Get first product from last search (or extract from entities)
        entities = classification.entities.model_dump()
        product_id = entities.get("product_id", products[0].get("id"))
        variant_id = entities.get("variant_id", products[0].get("variants", [{}])[0].get("id"))

        # Use unified add-to-cart helper
        return await self._perform_add_to_cart(
            psid=psid, product_id=product_id, variant_id=variant_id, context=context
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
            shop_domain = (
                config.get("STORE_URL", "https://shop.example.com")
                .replace("https://", "")
                .replace("http://", "")
            )
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
            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("cart_view_error", personality),
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
            personality = await self._get_personality()
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
            shop_domain = (
                config.get("STORE_URL", "https://shop.example.com")
                .replace("https://", "")
                .replace("http://", "")
            )
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
                item_title=removed_item.title if removed_item else "unknown",
            )

            item_name = removed_item.title if removed_item else "item"
            if not cart.items:
                prefix = self._fmt("cart_removed_empty", personality, item=item_name)
            else:
                prefix = self._fmt("cart_removed", personality, item=item_name)

            return MessengerResponse(text=prefix, recipient_id=psid)

        except Exception as e:
            self.logger.error("remove_item_failed", psid=psid, variant_id=variant_id, error=str(e))
            return MessengerResponse(
                text=self._fmt("cart_remove_error", personality),
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
            shop_domain = (
                config.get("STORE_URL", "https://shop.example.com")
                .replace("https://", "")
                .replace("http://", "")
            )
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
                new_quantity=new_quantity,
            )

            # Return empty response (attachment sent)
            return MessengerResponse(text="", recipient_id=psid)

        except Exception as e:
            self.logger.error(
                "adjust_quantity_failed",
                psid=psid,
                variant_id=variant_id,
                adjustment=adjustment,
                error=str(e),
            )
            return MessengerResponse(
                text=self._fmt("cart_quantity_error", await self._get_personality()),
                recipient_id=psid,
            )

    async def _handle_forget_preferences(self, psid: str) -> MessengerResponse:
        """Handle forget preferences request.

        Clears voluntary data (cart, consent, context) while preserving
        operational data (order references) as per GDPR/CCPA requirements.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Messenger response confirming data deletion
        """
        try:
            # Clear voluntary session data (cart, consent, context, activity)
            await self.session_service.clear_session(psid)

            self.logger.info("forget_preferences_success", psid=psid, voluntary_data_cleared=True)

            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("forget_success", personality),
                recipient_id=psid,
            )

        except Exception as e:
            self.logger.error("forget_preferences_failed", psid=psid, error=str(e))
            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("forget_error", personality),
                recipient_id=psid,
            )

    async def _request_consent(
        self,
        psid: str,
        product_id: str,
        variant_id: str,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Request consent for cart persistence (Story 2.7).

        Stores product info temporarily and sends consent request with quick reply buttons.

        Args:
            psid: Facebook Page-Scoped ID
            product_id: Shopify product ID
            variant_id: Shopify variant ID
            context: Conversation context with product search results

        Returns:
            Messenger response with consent request (empty text, quick replies sent via service)
        """
        # Extract product info from context
        last_search = context.get("last_search_results", {})
        products = last_search.get("products", [])

        product_data = None
        variant_data = None

        for p in products:
            if p.get("id") == product_id:
                product_data = p
                for v in p.get("variants", []):
                    if v.get("id") == variant_id:
                        variant_data = v
                        break
                break

        if not product_data or not variant_data:
            self.logger.warning(
                "consent_request_product_not_found", psid=psid, product_id=product_id
            )
            return MessengerResponse(
                text=self._fmt("product_not_found", personality),
                recipient_id=psid,
            )

        # Store pending product temporarily for 5 minutes
        pending_key = f"pending_cart:{psid}"
        pending_data = {
            "product_id": product_id,
            "variant_id": variant_id,
            "title": product_data.get("title"),
            "price": variant_data.get("price"),
            "image_url": product_data.get("images", [{}])[0].get("url", ""),
            "currency_code": variant_data.get("currency_code", "USD"),
        }
        import json

        self.context_manager.redis.setex(
            pending_key,
            300,  # 5 minutes
            json.dumps(pending_data),
        )

        self.logger.info(
            "consent_request_sent", psid=psid, product_id=product_id, variant_id=variant_id
        )

        # Send consent request with quick reply buttons via MessengerSendService
        send_service = MessengerSendService()
        personality = await self._get_personality()
        consent_message = {
            "text": self._fmt("consent_prompt", personality),
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": self._fmt("consent_yes", personality),
                    "payload": f"CONSENT:YES:{product_id}:{variant_id}",
                },
                {
                    "content_type": "text",
                    "title": self._fmt("consent_no", personality),
                    "payload": f"CONSENT:NO:{product_id}:{variant_id}",
                },
            ],
        }
        await send_service.send_message(psid, consent_message)
        await send_service.close()

        # Return empty response (quick reply message already sent)
        return MessengerResponse(text="", recipient_id=psid)

    async def _handle_consent_response(
        self,
        psid: str,
        parts: list[str],
    ) -> MessengerResponse:
        """Handle consent response from quick reply buttons (Story 2.7).

        Args:
            psid: Facebook Page-Scoped ID
            parts: Payload parts ["CONSENT", "YES/NO", "product_id", "variant_id"]

        Returns:
            Messenger response with confirmation or next action
        """
        personality = await self._get_personality()

        # Parse consent response
        consent_choice = parts[1]  # YES or NO
        product_id = parts[2] if len(parts) > 2 else None
        variant_id = parts[3] if len(parts) > 3 else None

        consent_granted = consent_choice == "YES"

        # Record consent choice
        await self.consent_service.record_consent(psid, consent_granted=consent_granted)

        self.logger.info(
            "consent_response_handled",
            psid=psid,
            consent_granted=consent_granted,
            product_id=product_id,
            variant_id=variant_id,
        )

        # If user opted in and we have pending product, add to cart
        if consent_granted and product_id and variant_id:
            # Retrieve pending product from temp storage
            pending_key = f"pending_cart:{psid}"
            import json

            pending_data = self.context_manager.redis.get(pending_key)

            if pending_data:
                # Clear pending storage
                self.context_manager.redis.delete(pending_key)

                # Add item to cart
                cart_service = CartService(redis_client=self.context_manager.redis)
                pending = json.loads(pending_data)

                try:
                    cart = await cart_service.add_item(
                        psid=psid,
                        product_id=pending["product_id"],
                        variant_id=pending["variant_id"],
                        title=pending["title"],
                        price=pending["price"],
                        image_url=pending["image_url"],
                        currency_code=pending.get("currency_code", "USD"),
                        quantity=1,
                    )

                    self.logger.info(
                        "cart_add_after_consent",
                        psid=psid,
                        product_id=pending["product_id"],
                        item_count=cart.item_count,
                    )

                    return MessengerResponse(
                        text=self._fmt(
                            "consent_added",
                            personality,
                            title=pending["title"],
                            price=pending["price"],
                        ),
                        recipient_id=psid,
                    )

                except Exception as e:
                    self.logger.error("cart_add_after_consent_failed", psid=psid, error=str(e))
                    return MessengerResponse(
                        text=self._fmt("consent_add_error", personality),
                        recipient_id=psid,
                    )
            else:
                # Pending data expired - ask user to try again
                return MessengerResponse(
                    text=self._fmt("consent_expired", personality),
                    recipient_id=psid,
                )

        elif consent_granted:
            # User opted in but no pending product
            return MessengerResponse(
                text=self._fmt("consent_granted", personality),
                recipient_id=psid,
            )
        else:
            # User opted out
            return MessengerResponse(
                text=self._fmt("consent_denied", personality),
                recipient_id=psid,
            )

    async def _handle_checkout(self, psid: str) -> MessengerResponse:
        """Handle checkout intent (Story 2.8).

        Generates Shopify checkout URL from cart items and returns it to user.
        Retains local cart to support abandoned checkout recovery.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Messenger response with checkout URL or error message
        """
        try:
            checkout_service = await self._get_checkout_service()
            result = await checkout_service.generate_checkout_url(psid)

            # Handle different checkout statuses
            if result["status"] == CheckoutStatus.EMPTY_CART:
                return MessengerResponse(
                    text=result["message"],
                    recipient_id=psid,
                )

            elif result["status"] == CheckoutStatus.SUCCESS:
                self.logger.info(
                    "checkout_success",
                    psid=psid,
                    checkout_url=result["checkout_url"],
                    checkout_token=result["checkout_token"],
                )

                return MessengerResponse(
                    text=result["message"],
                    recipient_id=psid,
                )

            else:  # FAILED or RETRYING
                self.logger.error(
                    "checkout_failed",
                    psid=psid,
                    status=result["status"],
                    message=result["message"],
                    retry_count=result.get("retry_count", 0),
                )

                return MessengerResponse(
                    text=result["message"],
                    recipient_id=psid,
                )

        except Exception as e:
            self.logger.error(
                "checkout_handler_error",
                psid=psid,
                error=str(e),
            )
            return MessengerResponse(
                text=self._fmt("checkout_error", await self._get_personality()),
                recipient_id=psid,
            )

    async def _handle_order_tracking(
        self,
        psid: str,
        classification: Any,
        context: dict[str, Any],
    ) -> MessengerResponse:
        """Handle order tracking intent (Story 4-1).

        Tracks orders by customer (platform_sender_id) or order number.
        Uses conversation_data to manage pending order number input state.

        Flow:
        1. Check for pending state (waiting for order number)
        2. If pending: extract order number from message, lookup by number
        3. If not pending: lookup by customer (platform_sender_id)
        4. If found: return order status
        5. If not found by customer: set pending state, ask for order number
        6. If not found by number: keep pending state, suggest retry

        Args:
            psid: Facebook Page-Scoped ID
            classification: Intent classification result
            context: Conversation context

        Returns:
            Messenger response with order status or prompt for order number
        """
        if not self.merchant_id:
            personality = await self._get_personality()
            return MessengerResponse(
                text=self._fmt("unavailable", personality),
                recipient_id=psid,
            )

        try:
            from sqlalchemy import select

            from app.core.database import async_session
            from app.models.conversation import Conversation

            order_tracking = self._get_order_tracking_service()

            async with async_session()() as db:
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.merchant_id == self.merchant_id,
                        Conversation.platform_sender_id == psid,
                    )
                )
                conversation = result.scalars().first()

                conversation_data = None
                if conversation:
                    conversation_data = conversation.conversation_data

                pending_state = order_tracking.get_pending_state(conversation_data)

                if pending_state:
                    message_text = classification.get("raw_message", "")
                    order_number = message_text.strip()

                    tracking_result = await order_tracking.track_order_by_number(
                        db, self.merchant_id, order_number
                    )

                    if tracking_result.found and tracking_result.order:
                        updated_data = order_tracking.clear_pending_state(conversation_data)
                        if conversation:
                            conversation.conversation_data = updated_data
                            await db.commit()

                        response_text = order_tracking.format_order_response(tracking_result.order)
                        self.logger.info(
                            "order_tracking_success",
                            psid=psid,
                            order_number=tracking_result.order.order_number,
                            lookup_type="by_order_number",
                        )
                        return MessengerResponse(text=response_text, recipient_id=psid)

                    response_text = order_tracking.format_order_not_found_response(
                        OrderLookupType.BY_ORDER_NUMBER, order_number
                    )
                    self.logger.info(
                        "order_tracking_not_found",
                        psid=psid,
                        order_number=order_number,
                        lookup_type="by_order_number",
                    )
                    return MessengerResponse(text=response_text, recipient_id=psid)

                tracking_result = await order_tracking.track_order_by_customer(
                    db, self.merchant_id, psid
                )

                if tracking_result.found and tracking_result.order:
                    response_text = order_tracking.format_order_response(tracking_result.order)
                    self.logger.info(
                        "order_tracking_success",
                        psid=psid,
                        order_number=tracking_result.order.order_number,
                        lookup_type="by_customer",
                    )
                    return MessengerResponse(text=response_text, recipient_id=psid)

                updated_data = order_tracking.set_pending_state(conversation_data)
                if conversation:
                    conversation.conversation_data = updated_data
                    await db.commit()

                response_text = order_tracking.format_order_not_found_response(
                    OrderLookupType.BY_CUSTOMER
                )
                self.logger.info(
                    "order_tracking_not_found",
                    psid=psid,
                    lookup_type="by_customer",
                    pending_state_set=True,
                )
                return MessengerResponse(text=response_text, recipient_id=psid)

        except Exception as e:
            self.logger.error(
                "order_tracking_handler_error",
                psid=psid,
                error=str(e),
            )
            return MessengerResponse(
                text=self._fmt("order_error", await self._get_personality()),
                recipient_id=psid,
            )
