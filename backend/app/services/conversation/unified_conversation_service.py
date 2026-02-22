"""Unified Conversation Service for cross-channel message processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Provides a single service for all chat channels (Widget, Messenger, Preview)
to ensure consistent behavior and feature parity.

Story 5-10 Code Review Fix:
- C7: Added BudgetAwareLLMWrapper for cost tracking
- C8: Added conversation persistence for widget channel
- C9: Added HandoffHandler for human handoff intent
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import APIError, ErrorCode
from app.models.merchant import Merchant
from sqlalchemy.orm import selectinload
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
    IntentType,
)
from app.services.conversation.handlers import (
    GreetingHandler,
    LLMHandler,
    SearchHandler,
    CartHandler,
    CheckoutHandler,
    OrderHandler,
    HandoffHandler,
    ClarificationHandler,
)
from app.services.intent.intent_classifier import IntentClassifier
from app.services.intent.classification_schema import (
    ClassificationResult,
    IntentType as ClassifierIntentType,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.cost_tracking.budget_aware_llm_wrapper import BudgetAwareLLMWrapper


logger = structlog.get_logger(__name__)


class UnifiedConversationService:
    """Single service for all chat channels.

    Provides unified message processing with:
    - Merchant-specific LLM configuration
    - Intent classification with confidence thresholds
    - Handler routing based on intent
    - Consistent behavior across Widget, Messenger, and Preview
    - Cost tracking via BudgetAwareLLMWrapper (C7 fix)
    - Conversation persistence to database (C8 fix)
    - Human handoff support (C9 fix)
    """

    INTENT_CONFIDENCE_THRESHOLD = 0.5

    INTENT_TO_HANDLER_MAP = {
        "product_search": "search",
        "greeting": "greeting",
        "cart_view": "cart",
        "cart_add": "cart",
        "cart_remove": "cart",
        "cart_clear": "cart",
        "checkout": "checkout",
        "order_tracking": "order",
        "human_handoff": "handoff",
        "clarification": "clarification",
        "forget_preferences": "llm",
        "general": "llm",
        "unknown": "llm",
    }

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        track_costs: bool = True,
    ) -> None:
        """Initialize unified conversation service.

        Args:
            db: Database session for loading merchant config
            track_costs: Whether to track LLM costs (default True)
        """
        self.db = db
        self.track_costs = track_costs
        self.logger = structlog.get_logger(__name__)

        self._handlers = {
            "greeting": GreetingHandler(),
            "llm": LLMHandler(),
            "search": SearchHandler(),
            "cart": CartHandler(),
            "checkout": CheckoutHandler(),
            "order": OrderHandler(),
            "handoff": HandoffHandler(),
            "clarification": ClarificationHandler(),
        }

    async def process_message(
        self,
        db: AsyncSession,
        context: ConversationContext,
        message: str,
    ) -> ConversationResponse:
        """Process a message and return a response.

        This is the main entry point for all channel message processing.

        Args:
            db: Database session
            context: Conversation context with channel info
            message: User's message text

        Returns:
            ConversationResponse with message and metadata

        Raises:
            APIError: If processing fails
        """
        start_time = time.time()

        try:
            merchant = await self._load_merchant(db, context.merchant_id)
            if not merchant:
                raise APIError(
                    ErrorCode.MERCHANT_NOT_FOUND,
                    f"Merchant {context.merchant_id} not found",
                )

            llm_service = await self._get_merchant_llm(merchant, db, context)

            classification = await self._classify_intent(
                llm_service=llm_service,
                message=message,
                context=context,
            )

            intent_name = classification.intent.value if classification.intent else "unknown"
            confidence = classification.confidence

            self.logger.info(
                "unified_conversation_classified",
                merchant_id=merchant.id,
                channel=context.channel,
                intent=intent_name,
                confidence=confidence,
            )

            if confidence < self.INTENT_CONFIDENCE_THRESHOLD:
                self.logger.debug(
                    "unified_conversation_low_confidence_fallback",
                    merchant_id=merchant.id,
                    confidence=confidence,
                    threshold=self.INTENT_CONFIDENCE_THRESHOLD,
                )
                handler = self._handlers["llm"]
                response = await handler.handle(
                    db=db,
                    merchant=merchant,
                    llm_service=llm_service,
                    message=message,
                    context=context,
                    entities=None,
                )
            else:
                handler_name = self.INTENT_TO_HANDLER_MAP.get(intent_name, "llm")
                handler = self._handlers.get(handler_name, self._handlers["llm"])

                entities = None
                if classification.entities:
                    entities = classification.entities.model_dump(exclude_none=True)

                if handler_name == "cart":
                    entities = entities or {}
                    cart_action = self._determine_cart_action(intent_name)
                    entities["cart_action"] = cart_action

                response = await handler.handle(
                    db=db,
                    merchant=merchant,
                    llm_service=llm_service,
                    message=message,
                    context=context,
                    entities=entities,
                )

            processing_time_ms = (time.time() - start_time) * 1000
            response.metadata["processing_time_ms"] = round(processing_time_ms, 2)
            response.intent = intent_name
            response.confidence = confidence

            # Capture merchant_id before persistence (which may rollback and expire objects)
            merchant_id_for_log = context.merchant_id

            await self._persist_conversation_message(
                db=db,
                context=context,
                merchant_id=context.merchant_id,
                user_message=message,
                bot_response=response.message,
                intent=intent_name,
                confidence=confidence,
            )

            self.logger.info(
                "unified_conversation_complete",
                merchant_id=merchant_id_for_log,
                channel=context.channel,
                intent=intent_name,
                confidence=confidence,
                processing_time_ms=processing_time_ms,
            )

            return response

        except APIError:
            raise
        except Exception as e:
            self.logger.error(
                "unified_conversation_failed",
                merchant_id=context.merchant_id,
                channel=context.channel,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise APIError(
                ErrorCode.LLM_PROVIDER_ERROR,
                f"Failed to process message: {str(e)}",
            )

    async def _load_merchant(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> Optional[Merchant]:
        """Load merchant from database with eager-loaded relationships.

        Args:
            db: Database session
            merchant_id: Merchant ID

        Returns:
            Merchant model or None
        """
        result = await db.execute(
            select(Merchant)
            .where(Merchant.id == merchant_id)
            .options(selectinload(Merchant.llm_configuration))
        )
        return result.scalars().first()

    async def _get_merchant_llm(
        self,
        merchant: Merchant,
        db: AsyncSession,
        context: Optional[ConversationContext] = None,
    ) -> BaseLLMService:
        """Get LLM service for merchant's configuration.

        Story 5-10 Code Review Fix (C7):
        - Wraps LLM with BudgetAwareLLMWrapper for cost tracking

        Args:
            merchant: Merchant model
            db: Database session
            context: Optional conversation context for cost tracking

        Returns:
            BaseLLMService configured for the merchant (wrapped with budget awareness)
        """
        base_llm = None

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
                        from app.core.security import decrypt_access_token

                        config["api_key"] = decrypt_access_token(llm_config.api_key_encrypted)

                base_llm = LLMProviderFactory.create_provider(
                    provider_name=provider_name,
                    config=config,
                )
        except Exception as e:
            self.logger.warning(
                "merchant_llm_config_failed",
                merchant_id=merchant.id,
                error=str(e),
            )

        if base_llm is None:
            base_llm = LLMProviderFactory.create_provider(
                provider_name="ollama",
                config={"model": "llama3.2"},
            )

        if self.track_costs and context:
            conversation_id = context.session_id
            return BudgetAwareLLMWrapper(
                llm_service=base_llm,
                db=db,
                merchant_id=merchant.id,
                conversation_id=conversation_id,
                track_costs=True,
            )

        return base_llm

    async def _classify_intent(
        self,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
    ) -> ClassificationResult:
        """Classify user intent using pattern matching first, then LLM fallback.

        Story 5-10 Code Review Fix (C2):
        Uses IntentClassifier.with_external_llm() factory method.

        Args:
            llm_service: LLM service for classification
            message: User's message
            context: Conversation context

        Returns:
            ClassificationResult with intent and entities
        """
        # First try pattern-based classification (fast, free, reliable)
        pattern_result = self._classify_by_patterns(message)
        if pattern_result and pattern_result.confidence >= 0.9:
            return pattern_result

        # Fall back to LLM classification for ambiguous queries
        try:
            classifier = IntentClassifier.with_external_llm(llm_service)

            conversation_context = {
                "channel": context.channel,
                "history": context.conversation_history[-3:],
            }

            return await classifier.classify(
                message=message,
                conversation_context=conversation_context,
            )

        except Exception as e:
            self.logger.warning(
                "intent_classification_failed",
                error=str(e),
                message=message,
            )
            from app.services.intent.classification_schema import ExtractedEntities

            return ClassificationResult(
                intent=ClassifierIntentType.UNKNOWN,
                confidence=0.0,
                entities=ExtractedEntities(),
                raw_message=message,
                llm_provider="error",
                model="error",
                processing_time_ms=0,
            )

    def _classify_by_patterns(self, message: str) -> Optional[ClassificationResult]:
        """Fast pattern-based intent classification.

        Args:
            message: User's message

        Returns:
            ClassificationResult if pattern matches, None otherwise
        """
        from app.services.intent.classification_schema import (
            ExtractedEntities,
            IntentType as ClassifierIntentType,
        )
        import re

        lower_msg = message.lower().strip()

        # Greeting patterns
        greeting_patterns = [
            r"^(hi|hello|hey|howdy|greetings|good\s*(morning|afternoon|evening))\s*[!?.]*$",
            r"^(hi|hello|hey)\s+there\s*[!?.]*$",
        ]
        for pattern in greeting_patterns:
            if re.match(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.GREETING,
                    confidence=0.98,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Add to cart patterns - must be BEFORE cart_view to avoid matching
        add_cart_patterns = [
            r"(add\s+(this|that|it|these)\s+to\s+(my\s+)?cart)",
            r"(put\s+(this|that|it)\s+in\s+(my\s+)?cart)",
            r"(i\s+want\s+to\s+add\s+.*(to\s+cart)?)",
            r"^(add\s+to\s+cart)$",
        ]
        for pattern in add_cart_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.CART_ADD,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Cart view patterns - more specific to avoid matching add-to-cart
        cart_view_patterns = [
            r"(show|view|see|what\'?s?\s+in|check)\s+(my\s+)?cart",
            r"^cart$",
            r"^(my\s+)?cart\s*(contents)?$",
            r"what\s+(is\s+)?(in\s+)?(my\s+)?cart",
        ]
        for pattern in cart_view_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.CART_VIEW,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Cart clear/empty patterns
        cart_clear_patterns = [
            r"(empty|clear)\s+(my\s+)?cart",
            r"(remove\s+all|delete\s+all)\s+(from\s+)?(my\s+)?cart",
            r"^(clear\s+cart|empty\s+cart)$",
            r"(i\s+want\s+to\s+(empty|clear)\s+(my\s+)?cart)",
        ]
        for pattern in cart_clear_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.CART_CLEAR,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Checkout patterns - must be more specific to avoid matching product searches
        checkout_patterns = [
            r"^(checkout|check\s*out)$",
            r"(i\s+want\s+to\s+(checkout|check\s*out)|proceed\s+to\s+checkout)",
            r"(complete\s+(my\s+)?(purchase|order|checkout))",
            r"(buy\s+these\s*(items|products|now)?)",
            r"(take\s+me\s+to\s+checkout)",
        ]
        for pattern in checkout_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.CHECKOUT,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Order tracking patterns
        order_patterns = [
            r"(where\s+is\s+my|track\s+my|check\s+my)\s+order",
            r"(order\s+status|shipping\s+status)",
            r"^order$",
        ]
        for pattern in order_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.ORDER_TRACKING,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Human handoff patterns
        handoff_patterns = [
            r"(talk\s+to|speak\s+with|connect\s+me\s+to)\s+(a\s+)?(person|human|agent|representative)",
            r"(human|agent|representative|customer\s+service)",
            r"(i\s+need\s+help\s+from\s+a\s+person)",
        ]
        for pattern in handoff_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.HUMAN_HANDOFF,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Product search with price constraint
        price_patterns = [
            r"(products?|items?|things?)\s+(under|below|less\s+than|cheaper\s+than)\s*\$?(\d+)",
            r"(under|below)\s*\$?(\d+)",
            r"(products?|items?)\s+(for|at|under)\s*\$?(\d+)",
        ]
        for pattern in price_patterns:
            match = re.search(pattern, lower_msg)
            if match:
                # Extract budget from last group
                groups = match.groups()
                budget = float(groups[-1]) if groups else None
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.95,
                    entities=ExtractedEntities(budget=budget),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Most expensive / highest price
        expensive_patterns = [
            r"(most\s+expensive|highest\s+priced?|priciest|costliest)",
            r"(what\'?s?\s+the\s+)?(most\s+expensive|highest\s+price)",
        ]
        for pattern in expensive_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.95,
                    entities=ExtractedEntities(
                        constraints={"sort_by": "price", "sort_order": "desc", "limit": 3}
                    ),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Cheapest / lowest price
        cheap_patterns = [
            r"(cheapest|lowest\s+priced?|least\s+expensive|most\s+affordable)",
            r"(what\'?s?\s+the\s+)?(cheapest|lowest\s+price)",
        ]
        for pattern in cheap_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.95,
                    entities=ExtractedEntities(
                        constraints={"sort_by": "price", "sort_order": "asc", "limit": 3}
                    ),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Recommendations / featured / pinned products
        recommend_patterns = [
            r"(what\s+do\s+you\s+recommend|recommendations?|suggested|suggestions)",
            r"(featured|highlighted|pinned|top\s+picks?|best\s+sellers?)",
            r"(what\'?s?\s+(your\s+)?(best|top|popular|trending))",
            r"(popular|trending|hot\s+items?|best\s+selling)",
            r"(must\s+have|essential|should\s+i\s+(get|buy))",
        ]
        for pattern in recommend_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.92,
                    entities=ExtractedEntities(
                        constraints={"pinned": True, "sort_by": "relevance"}
                    ),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Category/product search patterns - extract any product term dynamically
        # The pattern detects intent, Shopify determines what's available
        category_patterns = [
            (
                r"(show\s+me|find|looking\s+for|do\s+you\s+have|have\s+you\s+got)\s+(any\s+)?(\w+)\s*(?:products?|items?)?",
                3,
            ),
            (r"(find\s+me|get\s+me)\s+(\w+)", 2),
            (r"(\w+)\s+(?:products?|items?|collection)", 1),
            (r"i\s+want\s+(?:to\s+buy\s+(?:a\s+)?|a\s+|an\s+)(\w+)", 1),
            (r"i\s+(?:want\s+to\s+buy|need|am\s+looking\s+for)\s+(?:a\s+)?(\w+)", 1),
        ]
        skip_words = {
            "the",
            "a",
            "an",
            "any",
            "some",
            "me",
            "my",
            "for",
            "to",
            "and",
            "or",
            "in",
            "on",
            "at",
            "is",
            "are",
            "do",
            "does",
            "have",
            "has",
            "can",
            "could",
            "would",
            "should",
            "will",
        }

        for pattern, group_idx in category_patterns:
            match = re.search(pattern, lower_msg)
            if match:
                groups = match.groups()
                if len(groups) >= group_idx:
                    category = groups[group_idx - 1] if group_idx > 0 else None
                    if category and category.lower() not in skip_words:
                        return ClassificationResult(
                            intent=ClassifierIntentType.PRODUCT_SEARCH,
                            confidence=0.90,
                            entities=ExtractedEntities(category=category.lower()),
                            raw_message=message,
                            llm_provider="pattern",
                            model="regex",
                            processing_time_ms=0,
                        )

        # Standalone product term (e.g., "shoes", "coffee", "laptop")
        # Only match single words that look like product searches
        words = lower_msg.replace("?", "").split()
        if len(words) == 1 and len(words[0]) > 2 and words[0] not in skip_words:
            word = words[0]
            if not word.isdigit():
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.80,
                    entities=ExtractedEntities(category=word),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Generic product search
        product_patterns = [
            r"(show\s+me|find|search\s+for|look\s+for|do\s+you\s+have|have\s+you\s+got)\s+(any\s+)?(products?|items?)",
            r"what\s+(products?|items?|things?)\s+do\s+you\s+have",
            r"(products?|items?)\s+(available|in\s+stock)",
            r"^(products?|items?|catalog|inventory)$",
        ]
        for pattern in product_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.PRODUCT_SEARCH,
                    confidence=0.92,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        # Forget preferences / clear data
        forget_patterns = [
            r"(forget|clear|reset|delete)\s+(my\s+)?(preferences?|data|cart|memory)",
            r"(start\s+over|start\s+again|fresh\s+start)",
        ]
        for pattern in forget_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.FORGET_PREFERENCES,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        return None

    def _determine_cart_action(self, intent_name: str) -> str:
        """Determine cart action from intent name.

        Args:
            intent_name: Intent name

        Returns:
            Cart action: 'view', 'add', 'remove', or 'clear'
        """
        if intent_name == "cart_add":
            return "add"
        elif intent_name == "cart_remove":
            return "remove"
        elif intent_name == "cart_clear":
            return "clear"
        return "view"

    async def _persist_conversation_message(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant_id: int,
        user_message: str,
        bot_response: str,
        intent: str,
        confidence: float,
    ) -> Optional[int]:
        """Persist conversation and messages to database.

        Story 5-10 Code Review Fix (C8):
        - Creates/updates Conversation record
        - Creates Message records for user and bot
        - Enables widget conversations to appear in conversation page

        Args:
            db: Database session
            context: Conversation context
            merchant_id: Merchant ID
            user_message: User's message
            bot_response: Bot's response
            intent: Classified intent
            confidence: Classification confidence

        Returns:
            Conversation ID if persisted, None on failure
        """
        try:
            from app.models.conversation import Conversation
            from app.models.message import Message

            result = await db.execute(
                select(Conversation).where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.platform_sender_id == context.session_id,
                )
            )
            conversation = result.scalars().first()

            if not conversation:
                conversation = Conversation(
                    merchant_id=merchant_id,
                    platform=context.channel,
                    platform_sender_id=context.session_id,
                    status="active",
                    handoff_status="none",
                )
                db.add(conversation)
                await db.flush()

            user_msg = Message(
                conversation_id=conversation.id,
                sender="customer",
                content=user_message,
                message_type="text",
            )
            user_msg.set_encrypted_content(user_message, "customer")
            db.add(user_msg)

            bot_msg = Message(
                conversation_id=conversation.id,
                sender="bot",
                content=bot_response,
                message_type="text",
                message_metadata={
                    "intent": intent,
                    "confidence": confidence,
                    "channel": context.channel,
                },
            )
            db.add(bot_msg)

            conversation.updated_at = datetime.utcnow()

            await db.commit()

            self.logger.debug(
                "conversation_persisted",
                merchant_id=merchant_id,
                conversation_id=conversation.id,
                session_id=context.session_id,
                channel=context.channel,
            )

            return conversation.id

        except Exception as e:
            self.logger.warning(
                "conversation_persist_failed",
                merchant_id=merchant_id,
                session_id=context.session_id,
                error=str(e),
            )
            await db.rollback()
            return None
