"""Unified Conversation Service for cross-channel message processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Provides a single service for all chat channels (Widget, Messenger, Preview)
to ensure consistent behavior and feature parity.

Story 5-10 Code Review Fix:
- C7: Added BudgetAwareLLMWrapper for cost tracking
- C8: Added conversation persistence for widget channel
- C9: Added HandoffHandler for human handoff intent

Story 5-11: Messenger Unified Service Migration
- GAP-1: Handoff Detection (Low Confidence + Clarification Loop)
- GAP-5: Hybrid Mode Detection
- GAP-6: Budget Alert (Bot Pausing)
- GAP-7: Returning Shopper Welcome
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
    - Handoff detection via HandoffDetector (Story 5-11 GAP-1)
    - Hybrid mode detection (Story 5-11 GAP-5)
    - Budget pause check (Story 5-11 GAP-6)
    - Returning shopper welcome (Story 5-11 GAP-7)
    """

    INTENT_CONFIDENCE_THRESHOLD = 0.5
    HANDOFF_CONFIDENCE_THRESHOLD = 0.50
    HANDOFF_CONFIDENCE_TRIGGER_COUNT = 3
    RETURNING_SHOPPER_THRESHOLD_SECONDS = 1800

    INTENT_TO_HANDLER_MAP = {
        "product_search": "search",
        "product_inquiry": "search",
        "product_comparison": "search",
        "greeting": "greeting",
        "cart_view": "cart",
        "cart_add": "cart",
        "cart_remove": "cart",
        "cart_clear": "cart",
        "add_last_viewed": "cart",
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

        Story 5-11: Added pre-processing checks:
        - GAP-6: Budget pause check
        - GAP-5: Hybrid mode detection
        - GAP-1: Handoff detection
        - GAP-7: Returning shopper welcome

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

            # GAP-6: Check if bot is paused due to budget limit
            budget_paused_response = await self._check_budget_pause(db, context, merchant)
            if budget_paused_response:
                return budget_paused_response

            # GAP-5: Check hybrid mode - if active, only respond to @bot mentions
            hybrid_mode_response = await self._check_hybrid_mode(db, context, message)
            if hybrid_mode_response:
                return hybrid_mode_response

            # GAP-7: Check for returning shopper and send welcome
            await self._check_returning_shopper(db, context)

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

            # GAP-1: Check for handoff triggers (low confidence + clarification loop)
            handoff_response = await self._check_handoff(
                db=db,
                context=context,
                merchant=merchant,
                message=message,
                confidence=confidence,
                intent_name=intent_name,
            )
            if handoff_response:
                return handoff_response

            if confidence < self.INTENT_CONFIDENCE_THRESHOLD:
                self.logger.debug(
                    "unified_conversation_low_confidence_fallback",
                    merchant_id=merchant.id,
                    confidence=confidence,
                    threshold=self.INTENT_CONFIDENCE_THRESHOLD,
                )
                handler = self._handlers["llm"]
                entities = None
                response = await handler.handle(
                    db=db,
                    merchant=merchant,
                    llm_service=llm_service,
                    message=message,
                    context=context,
                    entities=entities,
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

            if response.products:
                response.products = self._deduplicate_products(response.products)

            self._update_shopping_state(context, response, intent_name, entities)

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
                cart=response.cart,
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
            r"(talk\s+to|speak\s+with|speak\s+to|connect\s+me\s+to)\s+(a\s+|your\s+)?(person|human|agent|representative|manager|supervisor)",
            r"(human|agent|representative|customer\s+service|manager|supervisor)",
            r"(i\s+need\s+help\s+from\s+a\s+person)",
            r"(i\s+want\s+to\s+speak\s+to\s+(a\s+|the\s+|your\s+)?manager)",
            r"(let\s+me\s+speak\s+to\s+(a\s+)?manager)",
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

        # Payment/billing/order issues - trigger handoff (require human support)
        payment_handoff_patterns = [
            r"(i\s+need\s+help\s+(with|on|about)\s+(my\s+)?payment)",
            r"(payment\s+(issue|problem|help|question|error|failed))",
            r"(problem\s+with\s+(my\s+)?payment)",
            r"(billing\s+(issue|problem|help|question|error|dispute))",
            r"(charge\s+(issue|problem|dispute|error))",
            r"(refund\s+(request|issue|problem|help))",
            r"(i\s+want\s+(a\s+)?refund)",
            r"(money\s+back)",
            r"(dispute\s+(my\s+)?(charge|payment|order))",
            r"(can'?t\s+(pay|checkout|complete\s+payment))",
            r"(payment\s+(didn'?t|did\s+not)\s+(go\s+through|work))",
        ]
        for pattern in payment_handoff_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.HUMAN_HANDOFF,
                    confidence=0.90,
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
        if intent_name in ("cart_add", "add_last_viewed"):
            return "add"
        elif intent_name == "cart_remove":
            return "remove"
        elif intent_name == "cart_clear":
            return "clear"
        return "view"

    def _deduplicate_products(self, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate products by product_id.

        Defense-in-depth deduplication to ensure no duplicate product cards
        are ever returned to the frontend.

        Args:
            products: List of product dicts

        Returns:
            Deduplicated list of products
        """
        seen_ids = set()
        unique_products = []

        for product in products:
            product_id = str(product.get("product_id") or product.get("id") or "")
            if product_id and product_id not in seen_ids:
                seen_ids.add(product_id)
                unique_products.append(product)
            elif product_id:
                self.logger.debug(
                    "response_dedup_skipped_duplicate",
                    product_id=product_id,
                )

        if len(unique_products) != len(products):
            self.logger.info(
                "response_products_deduplicated",
                original_count=len(products),
                deduplicated_count=len(unique_products),
            )

        return unique_products

    def _update_shopping_state(
        self,
        context: ConversationContext,
        response: ConversationResponse,
        intent_name: str,
        entities: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update shopping state based on response.

        Tracks viewed products for anaphoric reference resolution.

        Args:
            context: Conversation context with shopping_state
            response: Handler response
            intent_name: Classified intent
            entities: Extracted entities from classification
        """
        if response.products:
            for product in response.products[:5]:
                context.shopping_state.add_viewed_product(product)
            self.logger.debug(
                "shopping_state_updated",
                intent=intent_name,
                products_added=len(response.products),
                total_viewed=len(context.shopping_state.last_viewed_products),
            )

        if entities:
            category = entities.get("category")
            if category:
                context.shopping_state.last_search_category = category

            if intent_name in ("product_search", "product_inquiry"):
                raw_message = entities.get("raw_message")
                if raw_message:
                    context.shopping_state.last_search_query = raw_message[:100]

        if response.cart:
            context.shopping_state.last_cart_item_count = response.cart.get("item_count", 0)

    async def _persist_conversation_message(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant_id: int,
        user_message: str,
        bot_response: str,
        intent: str,
        confidence: float,
        cart: Optional[dict] = None,
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
            cart: Optional cart state to persist

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

            if cart is not None:
                if conversation.conversation_data is None:
                    conversation.conversation_data = {}
                conversation.conversation_data["cart"] = cart

            conversation.updated_at = datetime.now(timezone.utc)

            # Track customer message time for handoff resolution
            from app.services.handoff.resolution_service import HandoffResolutionService

            resolution_service = HandoffResolutionService(db)

            # Check if conversation is in active handoff - update customer message time
            if conversation.status == "handoff" and conversation.handoff_status in (
                "active",
                "pending",
                "resolved",
                "escalated",
                "reopened",
            ):
                await resolution_service.update_customer_message_time(conversation.id)
            elif conversation.status == "active" and conversation.handoff_status == "none":
                # Check if this is a recently resolved handoff that should be reopened
                reopenable = await resolution_service.get_reopenable_handoff(
                    context.session_id, merchant_id
                )
                if reopenable and reopenable.id == conversation.id:
                    await resolution_service.reopen_handoff(conversation, user_message)
                    self.logger.info(
                        "handoff_reopened_by_customer",
                        conversation_id=conversation.id,
                        merchant_id=merchant_id,
                    )

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

    async def _check_budget_pause(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
    ) -> Optional[ConversationResponse]:
        """Check if bot is paused due to budget limit.

        Story 5-11: GAP-6 - Budget Alert (Bot Pausing)

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model

        Returns:
            ConversationResponse if bot is paused, None otherwise
        """
        try:
            from app.services.cost_tracking.budget_alert_service import BudgetAlertService

            budget_service = BudgetAlertService(db=db)
            is_paused, pause_reason = await budget_service.get_bot_paused_state(merchant.id)

            if is_paused:
                self.logger.info(
                    "bot_paused_budget_exceeded",
                    merchant_id=merchant.id,
                    session_id=context.session_id,
                    pause_reason=pause_reason,
                )
                return ConversationResponse(
                    message="I'm currently unavailable. Please contact support or try again later.",
                    intent="bot_paused",
                    confidence=1.0,
                    metadata={"bot_paused": True, "reason": pause_reason},
                )
        except Exception as e:
            self.logger.warning(
                "budget_pause_check_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
        return None

    async def _check_hybrid_mode(
        self,
        db: AsyncSession,
        context: ConversationContext,
        message: str,
    ) -> Optional[ConversationResponse]:
        """Check if hybrid mode is active - only respond to @bot mentions.

        Story 5-11: GAP-5 - Hybrid Mode Detection

        Args:
            db: Database session
            context: Conversation context
            message: User's message

        Returns:
            ConversationResponse (empty) if should stay silent, None to proceed
        """
        if not context.hybrid_mode_enabled:
            return None

        if context.hybrid_mode_expires_at:
            try:
                expires_dt = datetime.fromisoformat(
                    context.hybrid_mode_expires_at.replace("Z", "+00:00")
                )
                if datetime.now(timezone.utc) > expires_dt:
                    self.logger.info(
                        "hybrid_mode_expired",
                        session_id=context.session_id,
                    )
                    return None
            except (ValueError, TypeError) as e:
                self.logger.warning(
                    "hybrid_mode_malformed_expiry",
                    session_id=context.session_id,
                    error=str(e),
                )
                return None

        if "@bot" in message.lower():
            self.logger.info(
                "hybrid_mode_bot_mention",
                session_id=context.session_id,
            )
            return None

        self.logger.info(
            "hybrid_mode_active_silent",
            session_id=context.session_id,
        )
        return ConversationResponse(
            message="",
            intent="hybrid_mode_silent",
            confidence=1.0,
            metadata={"hybrid_mode": True, "silent": True},
        )

    async def _check_returning_shopper(
        self,
        db: AsyncSession,
        context: ConversationContext,
    ) -> None:
        """Check for returning shopper and update state.

        Story 5-11: GAP-7 - Returning Shopper Welcome

        Note: This method only updates the context. The actual welcome message
        is sent by the channel-specific adapter (MessengerSendService for Messenger).

        Args:
            db: Database session
            context: Conversation context (will be updated in-place)
        """
        now = datetime.now(timezone.utc)
        context.last_activity_at = now.isoformat()

        if context.is_returning_shopper:
            return

        last_activity_str = context.metadata.get("last_activity_at")
        if last_activity_str:
            try:
                last_activity = datetime.fromisoformat(last_activity_str.replace("Z", "+00:00"))
                diff = (now - last_activity).total_seconds()
                if diff > self.RETURNING_SHOPPER_THRESHOLD_SECONDS:
                    context.is_returning_shopper = True
                    self.logger.info(
                        "returning_shopper_detected",
                        session_id=context.session_id,
                        inactive_seconds=diff,
                    )
            except (ValueError, TypeError):
                pass

    async def _check_handoff(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
        message: str,
        confidence: float,
        intent_name: str,
    ) -> Optional[ConversationResponse]:
        """Check for handoff triggers (low confidence + clarification loop).

        Story 5-11: GAP-1 - Handoff Detection

        Checks for:
        1. Keyword detection (human, agent, etc.)
        2. Low confidence scores (3 consecutive < 0.50)
        3. Clarification loops (3 same-type questions)

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model
            message: User's message
            confidence: Classification confidence
            intent_name: Classified intent

        Returns:
            ConversationResponse with handoff message if triggered, None otherwise
        """
        redis_client = None
        try:
            from app.services.handoff.detector import HandoffDetector
            from app.core.config import settings

            config = settings()
            redis_url = config.get("REDIS_URL", "redis://localhost:6379/0")
            import redis.asyncio as redis

            redis_client = redis.from_url(redis_url, decode_responses=True)
            detector = HandoffDetector(redis_client=redis_client)

            conversation = await self._get_conversation(db, context.session_id, merchant.id)
            conversation_id = conversation.id if conversation else merchant.id

            clarification_type = None
            if context.clarification_state.active:
                clarification_type = context.clarification_state.last_type

            result = await detector.detect(
                message=message,
                conversation_id=conversation_id,
                confidence_score=confidence,
                clarification_type=clarification_type,
            )

            if confidence < self.HANDOFF_CONFIDENCE_THRESHOLD:
                context.handoff_state.consecutive_low_confidence += 1
            else:
                context.handoff_state.consecutive_low_confidence = 0

            if result.should_handoff:
                self.logger.info(
                    "handoff_triggered_unified",
                    merchant_id=merchant.id,
                    session_id=context.session_id,
                    reason=result.reason.value if result.reason else None,
                    confidence_count=result.confidence_count,
                    matched_keyword=result.matched_keyword,
                    loop_count=result.loop_count,
                )

                await self._update_conversation_handoff_status(
                    db=db,
                    context=context,
                    merchant=merchant,
                    reason=result.reason.value if result.reason else "unknown",
                    confidence_count=result.confidence_count,
                )

                handoff_message = await self._get_handoff_message(merchant)
                return ConversationResponse(
                    message=handoff_message,
                    intent="human_handoff",
                    confidence=1.0,
                    metadata={
                        "handoff_triggered": True,
                        "reason": result.reason.value if result.reason else None,
                    },
                )

            if context.handoff_state.consecutive_low_confidence == 0:
                await detector.reset_state(conversation_id)

        except Exception as e:
            self.logger.warning(
                "handoff_check_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
        finally:
            if redis_client:
                await redis_client.close()
        return None

    async def _get_conversation(
        self,
        db: AsyncSession,
        session_id: str,
        merchant_id: int,
    ) -> Optional[Any]:
        """Get conversation for a session.

        Args:
            db: Database session
            session_id: Session identifier
            merchant_id: Merchant ID

        Returns:
            Conversation model or None
        """
        try:
            from app.models.conversation import Conversation

            result = await db.execute(
                select(Conversation)
                .where(
                    Conversation.merchant_id == merchant_id,
                    Conversation.platform_sender_id == session_id,
                )
                .order_by(Conversation.updated_at.desc())
                .limit(1)
            )
            return result.scalars().first()
        except Exception as e:
            self.logger.warning(
                "get_conversation_failed",
                session_id=session_id,
                error=str(e),
            )
            return None

    async def _update_conversation_handoff_status(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
        reason: str,
        confidence_count: int = 0,
    ) -> None:
        """Update conversation status to handoff in database.

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model
            reason: Handoff reason
            confidence_count: Consecutive low confidence count
        """
        try:
            from app.models.conversation import Conversation

            conversation = await self._get_conversation(db, context.session_id, merchant.id)

            if conversation:
                conversation.status = "handoff"
                conversation.handoff_status = "pending"
                conversation.handoff_triggered_at = datetime.now(timezone.utc)
                conversation.handoff_reason = reason
                conversation.consecutive_low_confidence_count = confidence_count
                await db.flush()

                self.logger.info(
                    "handoff_status_updated_unified",
                    conversation_id=conversation.id,
                    session_id=context.session_id,
                    reason=reason,
                    confidence_count=confidence_count,
                )
        except Exception as e:
            self.logger.error(
                "handoff_status_update_failed_unified",
                session_id=context.session_id,
                reason=reason,
                error=str(e),
            )

    async def _get_handoff_message(self, merchant: Merchant) -> str:
        """Get business hours-aware handoff message.

        Args:
            merchant: Merchant model

        Returns:
            Handoff message string
        """
        try:
            from app.services.handoff.business_hours_handoff_service import (
                BusinessHoursHandoffService,
            )

            service = BusinessHoursHandoffService()
            return service.build_handoff_message(merchant.business_hours_config)
        except Exception as e:
            self.logger.warning(
                "handoff_message_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            return "Connecting you to a human agent..."
