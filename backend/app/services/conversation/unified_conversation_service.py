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

import asyncio
import re
import time
from datetime import UTC, datetime
from typing import Any, ClassVar

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import APIError, ErrorCode
from app.core.input_sanitizer import sanitize_user_message_for_llm
from app.models.knowledge_base import KnowledgeDocument
from app.models.knowledge_gap import GapType, KnowledgeGap
from app.models.merchant import Merchant, PersonalityType
from app.models.conversation_context import ConversationTurn
from app.schemas.consent import ConsentStatus
from app.services.consent.extended_consent_service import ConversationConsentService
from app.services.conversation.handlers import (
    CartHandler,
    CheckConsentHandler,
    CheckoutHandler,
    ClarificationHandler,
    ForgetPreferencesHandler,
    GreetingHandler,
    HandoffHandler,
    LLMHandler,
    OrderHandler,
    RecommendationHandler,
    SearchHandler,
    SummarizeHandler,
)
from app.services.conversation.handlers.general_mode_fallback import (
    GeneralModeFallbackHandler,
)
from app.services.conversation.schemas import (
    Channel,
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.sentiment_adapter import (
    SentimentAdapterService,
    SentimentAdaptation,
    SentimentStrategy,
)
from app.services.cost_tracking.budget_aware_llm_wrapper import BudgetAwareLLMWrapper
from app.services.intent.classification_schema import (
    ClassificationResult,
)
from app.services.intent.classification_schema import (
    IntentType as ClassifierIntentType,
)
from app.services.intent.intent_classifier import IntentClassifier
from app.services.llm.base_llm_service import BaseLLMService
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.personality.clarification_question_templates import (
    register_natural_question_templates,
)
from app.services.personality.conversation_templates import (
    register_conversation_templates,
    register_sentiment_adaptive_templates,
    register_summarization_templates,
)
from app.services.personality.error_recovery_templates import register_error_recovery_templates
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter

register_conversation_templates()
register_error_recovery_templates()
register_summarization_templates()
register_sentiment_adaptive_templates()
register_natural_question_templates()

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
    _turn_write_metrics: ClassVar[dict[str, int]] = {"duplicate": 0, "unknown": 0}

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
        "forget_preferences": "forget_preferences",
        "check_consent_status": "check_consent",
        "product_recommendation": "recommendation",
        "summarize": "summarize",
        "general": "llm",
        "unknown": "llm",
    }

    def __init__(
        self,
        db: AsyncSession | None = None,
        track_costs: bool = True,
        rag_context_builder: RAGContextBuilder | None = None,
    ) -> None:
        """Initialize unified conversation service.

        Args:
            db: Database session for loading merchant config
            track_costs: Whether to track LLM costs (default True)
            rag_context_builder: RAG context builder for General mode (Story 8-5)
        """
        self.db = db
        self.track_costs = track_costs
        self.rag_context_builder = rag_context_builder
        self.logger = structlog.get_logger(__name__)

        self.general_mode_fallback_handler = GeneralModeFallbackHandler()

        self._handlers = {
            "greeting": GreetingHandler(),
            "llm": LLMHandler(),
            "order": OrderHandler(),
            "recommendation": RecommendationHandler(),
            "search": SearchHandler(),
            "cart": CartHandler(),
            "checkout": CheckoutHandler(),
            "order": OrderHandler(),
            "handoff": HandoffHandler(),
            "clarification": ClarificationHandler(),
            "forget_preferences": ForgetPreferencesHandler(),
            "check_consent": CheckConsentHandler(),
            "general_mode_fallback": self.general_mode_fallback_handler,
            "summarize": SummarizeHandler(),
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
        response = None
        intent_name = None
        confidence = None
        entities = None

        message = sanitize_user_message_for_llm(message)
        if not message:
            raise APIError(
                ErrorCode.VALIDATION_ERROR,
                "Message cannot be empty after sanitization",
            )

        try:
            merchant = await self._load_merchant(db, context.merchant_id)
            if not merchant:
                raise APIError(
                    ErrorCode.MERCHANT_NOT_FOUND,
                    f"Merchant {context.merchant_id} not found",
                )

            # Story 8-5: Build RAG context for both General and E-commerce modes
            # Enhanced: RAG now works for e-commerce mode as supplemental information
            # - General mode: RAG is primary knowledge source
            # - E-commerce mode: RAG supplements product catalog (policies, manuals, guides)
            rag_context = None
            rag_sources: list[str] = []
            rag_chunks: list[RetrievedChunk] = []
            rag_used_in_response = False
            if self.rag_context_builder and not self._is_simple_greeting(message):
                # Story 8-11 AC6: Construct embedding version for dimension consistency
                embedding_version = None
                if merchant.embedding_provider and merchant.embedding_model:
                    embedding_version = f"{merchant.embedding_provider}-{merchant.embedding_model}"

                (
                    rag_context,
                    rag_chunks,
                ) = await self.rag_context_builder.build_rag_context_with_chunks(
                    merchant_id=merchant.id,
                    user_query=message,
                    embedding_version=embedding_version,
                    conversation_history=context.conversation_history,
                )
                # Store in context for handlers to access
                if context.metadata is None:
                    context.metadata = {}
                context.metadata["rag_context"] = rag_context

                # Extract source document names from RAG context for tracking
                if rag_context:
                    # Extract document names from "From \"Document Name\":" pattern
                    import re

                    doc_names = re.findall(r'From "([^"]+)":', rag_context)
                    rag_sources = doc_names

            # GAP-6: Check if bot is paused due to budget limit
            budget_paused_response = await self._check_budget_pause(db, context, merchant)
            if budget_paused_response:
                response = budget_paused_response
                intent_name = response.intent or "bot_paused"
                confidence = response.confidence or 1.0

            # GAP-5: Check hybrid mode - if active, only respond to @bot mentions
            if response is None:
                hybrid_mode_response = await self._check_hybrid_mode(db, context, message)
                if hybrid_mode_response:
                    response = hybrid_mode_response
                    intent_name = response.intent or "hybrid_mode_silent"
                    confidence = response.confidence or 1.0

            # GAP-7: Check for returning shopper and send welcome
            if response is None:
                await self._check_returning_shopper(db, context)

            # Story 6-1: Check consent status and prompt if needed
            if response is None:
                await self._check_and_prompt_consent(db, context, merchant)

            # Story 4-13: Check for pending cross-device order lookup
            # If user is providing email/order number after being prompted, route to OrderHandler
            if response is None:
                from app.services.conversation.handlers.order_handler import (
                    PENDING_CROSS_DEVICE_KEY,
                    OrderHandler,
                )

                conversation_data = context.conversation_data or {}
                metadata = context.metadata or {}
                pending_lookup = conversation_data.get(PENDING_CROSS_DEVICE_KEY) or metadata.get(
                    PENDING_CROSS_DEVICE_KEY
                )

                if pending_lookup:
                    order_handler = OrderHandler()
                    normalized_email = order_handler._normalize_email(message)
                    if normalized_email or self._looks_like_order_number(message):
                        self.logger.info(
                            "pending_cross_device_lookup_routing_to_order_handler",
                            merchant_id=merchant.id,
                            message_preview=message[:20],
                            normalized_email=normalized_email,
                        )
                        handler = self._handlers["order"]
                        llm_service = await self._get_merchant_llm(merchant, db, context)
                        response = await handler.handle(
                            db=db,
                            merchant=merchant,
                            llm_service=llm_service,
                            message=message,
                            context=context,
                            entities=None,
                        )
                        intent_name = "order_tracking"
                        confidence = 1.0

            # Story 11-9: Early SUMMARIZE pattern pre-check
            # Must run BEFORE multi-turn check, FAQ check, proactive gathering, and general-mode bypass
            if response is None:
                summarize_intent = self._check_summarize_pattern(message)
                if summarize_intent:
                    intent_name = summarize_intent.value
                    confidence = 0.98
                    handler = self._handlers["summarize"]
                    llm_service = await self._get_merchant_llm(merchant, db, context)
                    response = await handler.handle(
                        db=db,
                        merchant=merchant,
                        llm_service=llm_service,
                        message=message,
                        context=context,
                        entities=None,
                    )

            # Story 11-2: Check multi-turn state before FAQ/intent classification
            # If in active multi-turn flow, route directly to multi-turn handler
            if response is None:
                mt_response = await self._check_multi_turn_state(
                    db=db,
                    context=context,
                    merchant=merchant,
                    message=message,
                )
                if mt_response:
                    response = mt_response
                    intent_name = response.intent or "clarification"
                    confidence = response.confidence or 0.8

            # Check for FAQ match before intent classification
            faq_matched = False
            if response is None:
                faq_response = await self._check_faq_match(db, context, merchant, message)
                if faq_response:
                    response = faq_response
                    intent_name = response.intent or "faq"
                    confidence = response.confidence or 1.0
                    faq_matched = True

            # Story 11-8: Proactive information gathering
            # After FAQ check, before intent classification
            # Check if active gathering state and handle response
            if response is None:
                response = await self._check_proactive_gathering(
                    db=db,
                    context=context,
                    merchant=merchant,
                    message=message,
                )
                if response:
                    intent_name = response.intent or "proactive_gathering"
                    confidence = response.confidence or 0.8

            # Normal flow: intent classification and handler routing
            if response is None:
                llm_service = await self._get_merchant_llm(merchant, db, context)

                # Skip intent classification in general mode - go straight to LLM handler
                # General mode doesn't need e-commerce intent routing
                if merchant.onboarding_mode == "general":
                    self.logger.info(
                        "general_mode_skipping_classification",
                        merchant_id=merchant.id,
                        channel=context.channel,
                    )
                    intent_name = "general"
                    confidence = 1.0  # No classification in general mode

                    # Story 11-10: Sentiment analysis for adaptive responses (general mode)
                    sentiment_adapter = SentimentAdapterService()
                    mode = getattr(merchant, "onboarding_mode", "general")
                    adaptation = sentiment_adapter.analyze_sentiment(message, mode=mode)

                    if adaptation.strategy != SentimentStrategy.NONE:
                        sentiment_adapter.track_sentiment(context, adaptation)
                        context.metadata["current_sentiment_adaptation"] = {
                            "strategy": adaptation.strategy.value,
                            "pre_phrase_key": adaptation.pre_phrase_key,
                            "post_phrase_key": adaptation.post_phrase_key,
                            "mode": adaptation.mode,
                            "confidence": adaptation.original_score.confidence,
                        }

                    if sentiment_adapter.should_escalate(context, adaptation):
                        intent_name = "human_handoff"
                        self.logger.info(
                            "sentiment_escalation_triggered",
                            merchant_id=merchant.id,
                            strategy=adaptation.strategy.value,
                        )

                    # Check for handoff triggers (keyword detection works without confidence)
                    handoff_response = await self._check_handoff(
                        db=db,
                        context=context,
                        merchant=merchant,
                        message=message,
                        confidence=confidence,
                        intent_name=intent_name,
                    )
                    if handoff_response:
                        response = handoff_response
                        intent_name = response.intent or "human_handoff"
                        confidence = response.confidence or 1.0
                    elif intent_name == "human_handoff":
                        handler_name = self.INTENT_TO_HANDLER_MAP.get(intent_name, "llm")
                        handler = self._handlers.get(handler_name, self._handlers["llm"])
                        response = await handler.handle(
                            db=db,
                            merchant=merchant,
                            llm_service=llm_service,
                            message=message,
                            context=context,
                            entities=None,
                        )
                    else:
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
                    classification = await self._classify_intent(
                        llm_service=llm_service,
                        message=message,
                        context=context,
                    )

                    intent_name = (
                        classification.intent.value if classification.intent else "unknown"
                    )
                    confidence = classification.confidence

                    # Story 11-10: Sentiment analysis for adaptive responses
                    sentiment_adapter = SentimentAdapterService()
                    mode = getattr(merchant, "onboarding_mode", "general")
                    adaptation = sentiment_adapter.analyze_sentiment(message, mode=mode)

                    if adaptation.strategy != SentimentStrategy.NONE:
                        sentiment_adapter.track_sentiment(context, adaptation)
                        context.metadata["current_sentiment_adaptation"] = {
                            "strategy": adaptation.strategy.value,
                            "pre_phrase_key": adaptation.pre_phrase_key,
                            "post_phrase_key": adaptation.post_phrase_key,
                            "mode": adaptation.mode,
                            "confidence": adaptation.original_score.confidence,
                        }

                    # Story 11-10: Escalation check
                    if sentiment_adapter.should_escalate(context, adaptation):
                        intent_name = "human_handoff"
                        self.logger.info(
                            "sentiment_escalation_triggered",
                            merchant_id=merchant.id,
                            strategy=adaptation.strategy.value,
                        )

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
                        response = handoff_response
                        intent_name = response.intent or "human_handoff"
                        confidence = response.confidence or 1.0

                    if response is None:
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
                        # Story 8-5: Check for e-commerce intent in General mode
                        if (
                            merchant.onboarding_mode == "general"
                            and intent_name.upper() in GeneralModeFallbackHandler.ECOMMERCE_INTENTS
                        ):
                            self.logger.info(
                                "general_mode_ecommerce_fallback",
                                merchant_id=merchant.id,
                                intent=intent_name,
                            )
                            handler = self.general_mode_fallback_handler
                            entities = None
                            if classification.entities:
                                entities = classification.entities.model_dump(exclude_none=True)
                                entities["original_intent"] = intent_name
                            response = await handler.handle(
                                db=db,
                                merchant=merchant,
                                llm_service=llm_service,
                                message=message,
                                context=context,
                                entities=entities,
                            )
                            intent_name = "general_mode_fallback"
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

            # Single exit point: ALWAYS persist and return
            processing_time_ms = (time.time() - start_time) * 1000
            if response.metadata is None:
                response.metadata = {}
            response.metadata["processing_time_ms"] = round(processing_time_ms, 2)
            response.intent = intent_name
            response.confidence = confidence

            # Story 6-1: Add consent_prompt_required for widget channel
            # Signal frontend to show consent prompt when status is pending and not yet shown
            if (
                context.channel == Channel.WIDGET
                and context.consent_state.status == ConsentStatus.PENDING
                and not context.consent_state.prompt_shown
            ):
                response.metadata["consent_prompt_required"] = True
                self.logger.info(
                    "consent_prompt_required_set",
                    session_id=context.session_id,
                    visitor_id=context.consent_state.visitor_id,
                    consent_status=context.consent_state.status,
                    prompt_shown=context.consent_state.prompt_shown,
                )

            # Story 8-5: Include RAG enabled flag in response metadata
            # Story 10-1: Include source citations for RAG responses
            if rag_context:
                response.metadata["rag_enabled"] = True
                if rag_sources:
                    response.metadata["rag_sources"] = rag_sources

            # Story 10-1: Map RetrievedChunk to dict for widget schema compatibility
            # Only include sources if:
            # 1. RAG context was actually used in the response
            # 2. The message is a question (not a greeting or statement)
            source_citations = []
            is_question = self._is_question(message)
            if rag_context and rag_chunks and is_question:
                for chunk in rag_chunks:
                    doc = await db.get(KnowledgeDocument, chunk.document_id)
                    if doc:
                        source_citations.append(
                            {
                                "documentId": chunk.document_id,
                                "title": chunk.document_name,
                                "filename": doc.filename,
                                "documentType": doc.file_type,  # type: ignore
                                "relevanceScore": chunk.similarity,
                                "url": doc.source_url,
                                "chunkIndex": chunk.chunk_index,
                            }
                        )
            if source_citations:
                # Hide sources if LLM explicitly says it couldn't find information
                # This prevents showing misleading citations when the sources weren't actually used
                if self._indicates_no_information_found(response.message):
                    self.logger.debug(
                        "rag_sources_hidden_no_info",
                        merchant_id=merchant.id,
                        source_count=len(source_citations),
                    )
                else:
                    response.sources = source_citations
                    self.logger.debug(
                        "rag_sources_attached",
                        merchant_id=merchant.id,
                        source_count=len(source_citations),
                        is_question=is_question,
                    )

            # Story 10-3: Generate suggested replies from RAG context
            if rag_chunks:
                llm_service = await self._get_merchant_llm(merchant, db, context)
                from app.services.rag.suggestion_generator import SuggestionGenerator

                suggestion_generator = SuggestionGenerator(llm_service=llm_service)
                suggestions = await suggestion_generator.generate_suggestions(
                    query=message,
                    chunks=rag_chunks,
                )
                if suggestions:
                    response.suggested_replies = suggestions

            if response.products:
                response.products = self._deduplicate_products(response.products)

            self._update_shopping_state(context, response, intent_name, entities)

            # Story 11-10: Apply sentiment adaptation to post-processing layer
            sentiment_data = context.metadata.get("current_sentiment_adaptation")
            if sentiment_data and sentiment_data.get("strategy") != "none" and response:
                try:
                    personality = merchant.personality
                    mode = sentiment_data.get("mode", "ecommerce")
                    pre_key = sentiment_data["pre_phrase_key"]
                    post_key = sentiment_data["post_phrase_key"]

                    def _get_sentiment_phrase(rtype: str, key: str, p: str, m: str) -> str | None:
                        mode_key = f"{key}_{m}"
                        try:
                            result = PersonalityAwareResponseFormatter.format_response(
                                rtype, mode_key, p, mode=m
                            )
                            if result:
                                return result
                        except (KeyError, ValueError):
                            pass
                        return PersonalityAwareResponseFormatter.format_response(
                            rtype, key, p, mode=m
                        )

                    pre_phrase = _get_sentiment_phrase(
                        "sentiment_adaptive",
                        pre_key,
                        personality,
                        mode,
                    )
                    post_phrase = _get_sentiment_phrase(
                        "sentiment_adaptive",
                        post_key,
                        personality,
                        mode,
                    )

                    # H2: Transition suppression (anti double-acknowledgment per AC2)
                    msg = response.message
                    from app.services.personality.transition_phrases import TRANSITION_PHRASES

                    transition_suppressed = False
                    all_phrases: list[str] = []
                    for cat_phrases in TRANSITION_PHRASES.values():
                        all_phrases.extend(cat_phrases.get(personality, []))
                    for phrase in sorted(all_phrases, key=len, reverse=True):
                        prefix = phrase.rstrip(".")
                        if prefix and msg.startswith(prefix):
                            msg = msg[len(prefix) :].lstrip()
                            transition_suppressed = True
                            break

                    if pre_phrase and post_phrase:
                        response.message = f"{pre_phrase}\n\n{msg}\n\n{post_phrase}"

                    elif pre_phrase:
                        response.message = f"{pre_phrase}\n\n{msg}"
                    elif post_phrase:
                        response.message = f"{msg}\n\n{post_phrase}"

                    response.metadata["sentiment_adapted"] = True
                    response.metadata["sentiment_strategy"] = sentiment_data.get("strategy")

                    response.metadata["transition_suppressed"] = transition_suppressed
                except Exception:
                    self.logger.exception(
                        "sentiment_adaptation_failed",
                        error_code=ErrorCode.SENTIMENT_ADAPTATION_FAILED,
                    )

            # Capture merchant_id before persistence (which may rollback and expire objects)
            merchant_id_for_log = context.merchant_id

            res = await self._persist_conversation_message(
                db=db,
                context=context,
                merchant_id=context.merchant_id,
                user_message=message,
                bot_response=response.message,
                intent=intent_name,
                confidence=confidence,
                cart=response.cart,
            )

            conversation_id = None
            if res:
                conversation_id, bot_msg_id = res
                response.message_id = bot_msg_id

            # Story 11-12a: Track conversation turn for analytics
            if conversation_id:
                try:
                    sentiment_strategy_name: str | None = None
                    sentiment_confidence: float | None = None
                    sentiment_data = context.metadata.get("current_sentiment_adaptation")
                    if sentiment_data and sentiment_data.get("strategy") not in (None, "none"):
                        sentiment_strategy_name = sentiment_data.get("strategy", "").upper()
                        score_confidence = sentiment_data.get("confidence")
                        if score_confidence is not None:
                            sentiment_confidence = float(score_confidence)

                    turn_context_snapshot = self._build_turn_context_snapshot(
                        confidence=confidence,
                        processing_time_ms=processing_time_ms,
                        context=context,
                        sentiment_confidence=sentiment_confidence,
                        mode=merchant.onboarding_mode,
                    )
                    await self._write_conversation_turn(
                        db=db,
                        conversation_id=conversation_id,
                        turn_number=len(context.conversation_history) + 1,
                        intent_detected=intent_name,
                        sentiment=sentiment_strategy_name,
                        context_snapshot=turn_context_snapshot,
                    )
                except Exception as e:
                    error_type = "duplicate" if isinstance(e, IntegrityError) else "unknown"
                    UnifiedConversationService._turn_write_metrics[error_type] += 1
                    self.logger.error(
                        "conversation_turn_write_failed",
                        error_code=7127,
                        conversation_id=conversation_id,
                        error=str(e),
                        error_type=error_type,
                        metric_count=UnifiedConversationService._turn_write_metrics[error_type],
                    )

            # Detect and record knowledge gaps
            await self._detect_and_record_knowledge_gap(
                db=db,
                merchant=merchant,
                conversation_id=conversation_id,
                user_message=message,
                bot_response=response.message if response else "",
                confidence=confidence if confidence else 0.0,
                rag_chunks=rag_chunks,
                faq_matched=faq_matched,
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
            try:
                from app.services.conversation.error_recovery_service import (
                    ErrorType,
                    NaturalErrorRecoveryService,
                )

                recovery_service = NaturalErrorRecoveryService()
                return await recovery_service.recover(
                    error_type=ErrorType.GENERAL,
                    merchant=merchant,
                    context=context,
                    error=e,
                    intent=intent_name or "unknown",
                    conversation_id=str(context.session_id),
                )
            except Exception as recovery_error:
                self.logger.error(
                    "error_recovery_failed",
                    merchant_id=context.merchant_id,
                    original_error=str(e),
                    recovery_error=str(recovery_error),
                )
                raise APIError(
                    ErrorCode.LLM_PROVIDER_ERROR,
                    f"Failed to process message: {str(e)}",
                )

    async def generate_handoff_resolution_message(
        self,
        db: AsyncSession,
        conversation_id: int,
        merchant_id: int,
    ) -> dict[str, Any]:
        """Generate context-aware handoff resolution message using LLM.

        Story: LLM-powered handoff resolution messages for widget

        Creates a personalized message when merchants resolve handoff items,
        using conversation context and merchant's personality settings.

        Args:
            db: Database session
            conversation_id: ID of the conversation being resolved
            merchant_id: ID of the merchant

        Returns:
            {
                "content": str,  # Generated message
                "fallback": bool,  # True if used fallback message
                "reason": str  # "llm_success" or error reason
            }
        """
        from app.models.conversation import Conversation
        from app.models.message import Message
        from app.services.conversation.handlers.llm_handler import LLMHandler
        from app.services.llm.base_llm_service import LLMMessage

        start_time = time.time()

        # Load merchant
        merchant = await self._load_merchant(db, merchant_id)
        if not merchant:
            return {
                "content": PersonalityAwareResponseFormatter.format_response(
                    "conversation", "welcome_back_fallback", PersonalityType.FRIENDLY
                ),
                "fallback": True,
                "reason": "merchant_not_found",
            }

        # Load conversation

        conversation_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.merchant_id == merchant_id,
            )
        )
        conversation = conversation_result.scalars().first()

        if not conversation:
            return {
                "content": PersonalityAwareResponseFormatter.format_response(
                    "conversation", "welcome_back_fallback", PersonalityType.FRIENDLY
                ),
                "fallback": True,
                "reason": "conversation_not_found",
            }

        from app.services.personality.transition_selector import get_transition_selector

        platform_sender_id = conversation.platform_sender_id
        if platform_sender_id:
            get_transition_selector().clear_conversation(platform_sender_id)

        # Get last 5 messages for context
        messages_query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )
        result = await db.execute(messages_query)
        recent_messages = list(result.scalars().all())
        recent_messages = list(reversed(recent_messages))  # Oldest first

        # Build LLM messages
        business_name = merchant.business_name or "our store"
        personality_type = (
            merchant.personality if merchant.personality else PersonalityType.FRIENDLY
        )

        # Get LLM service
        llm_service = await self._get_merchant_llm(merchant, db, None)

        # Build system prompt using LLMHandler's resolution prompt builder
        llm_handler = LLMHandler()
        system_prompt = llm_handler.build_resolution_system_prompt(
            personality_type=personality_type,
            business_name=business_name,
        )

        messages = [LLMMessage(role="system", content=system_prompt)]

        # Add conversation history for context
        for msg in recent_messages:
            role = "user" if msg.sender == "customer" else "assistant"
            messages.append(LLMMessage(role=role, content=msg.content or ""))

        # Add final instruction
        messages.append(
            LLMMessage(role="user", content="Generate a brief transition message back to bot mode.")
        )

        try:
            # Generate response with timeout
            llm_response = await asyncio.wait_for(
                llm_service.chat(messages=messages, temperature=0.7), timeout=5.0
            )

            response_content = llm_response.content.strip()

            # Validate response length (1-3 sentences)
            sentences = [s.strip() for s in response_content.split(".") if s.strip()]
            if len(sentences) > 3:
                # Truncate to 3 sentences
                response_content = ". ".join(sentences[:3]) + "."

            response_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "handoff_resolution_llm_success",
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                business_name=business_name,
                personality=personality_type,
                message_length=len(response_content),
                response_time_ms=response_time_ms,
                sentence_count=len(sentences),
            )

            return {
                "content": response_content,
                "fallback": False,
                "reason": "llm_success",
                "response_time_ms": response_time_ms,
            }

        except TimeoutError:
            logger.warning(
                "handoff_resolution_llm_timeout",
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                timeout_seconds=5.0,
            )
            return {
                "content": "Welcome back! Is there anything else I can help you with?",
                "fallback": True,
                "reason": "llm_timeout",
            }

        except Exception as e:
            logger.error(
                "handoff_resolution_llm_failed",
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return {
                "content": "Welcome back! Is there anything else I can help you with?",
                "fallback": True,
                "reason": f"llm_error: {type(e).__name__}",
            }

    async def _load_merchant(
        self,
        db: AsyncSession,
        merchant_id: int,
    ) -> Merchant | None:
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
        context: ConversationContext | None,
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

        llm_config = merchant.llm_configuration

        if llm_config:
            provider_name = llm_config.provider or "ollama"
            model = llm_config.ollama_model or llm_config.cloud_model

            config = {"model": model}
            if provider_name == "ollama":
                config["ollama_url"] = llm_config.ollama_url
            else:
                if llm_config.api_key_encrypted:
                    from app.core.security import decrypt_access_token

                    config["api_key"] = decrypt_access_token(llm_config.api_key_encrypted)

            try:
                llm_service = LLMProviderFactory.create_provider(
                    provider_name=provider_name,
                    config=config,
                )
                return BudgetAwareLLMWrapper(
                    llm_service=llm_service,
                    db=db,
                    merchant_id=merchant.id,
                    conversation_id=context.session_id if context else None,
                    track_costs=self.track_costs,
                    redis_client=None,
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

    _SUMMARIZE_PATTERNS: ClassVar[list[str]] = [
        r"^(recap|summarize|summary|quick recap)\s*[!?.]*$",
        r"^what (did|have) we (discuss(ed)?|talk(ed)? about|cover(ed)?)\s*[?!.]*$",
        r"^refresh my memory\s*[!?.]*$",
        r"^catch me up\s*[!?.]*$",
        r"^summarize (our|this|the) (conversation|chat|discussion)\s*[!?.]*$",
        r"^give me (a |an |the )?(recap|summary|overview)\s*[!?.]*$",
    ]

    def _check_summarize_pattern(self, message: str) -> ClassifierIntentType | None:
        """Story 11-9: Check if message matches a summarize intent pattern.

        Runs BEFORE multi-turn check, FAQ check, proactive gathering,
        and general-mode bypass. Uses tight ^...$ anchors to prevent
        false matches like 'summarize the return policy'.
        """
        normalized = message.strip().lower()
        for pattern in self._SUMMARIZE_PATTERNS:
            if re.match(pattern, normalized, re.IGNORECASE):
                return ClassifierIntentType.SUMMARIZE
        return None

    def _classify_by_patterns(self, message: str) -> ClassificationResult | None:
        """Fast pattern-based intent classification.

        Story 11-3: Enhanced with synonym normalization, typo tolerance,
        and expanded colloquial/indirect request patterns.

        Args:
            message: User's message

        Returns:
            ClassificationResult if pattern matches, None otherwise
        """
        import re

        from app.services.intent.classification_schema import (
            ExtractedEntities,
        )
        from app.services.intent.classification_schema import (
            IntentType as ClassifierIntentType,
        )
        from app.services.intent.variation_maps import normalize_message

        lower_msg = normalize_message(message)

        # Greeting patterns
        greeting_patterns = [
            r"^(hi|hello|hey|howdy|greetings|good\s*(morning|afternoon|evening)|yo|sup|what'?s\s*up|howdy|heya)\s*[!?.]*$",
            r"^(hi|hello|hey|yo)\s+there\s*[!?.]*$",
            r"^(hi|hello|hey)\s+(anyone|anybody|somebody)\s*(there|home|around)?\s*[!?.]*$",
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
            r"(add\s+(this|that|it|these|those)\s+to\s+(my\s+)?(cart|basket|bag))",
            r"(put\s+(this|that|it)\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(throw\s+(it|that|this)\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(toss\s+(it|that|this)\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(drop\s+(it|that|this)\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(throw\s+(it|that|this)\s+in\s+the\s+(cart|basket|bag))",
            r"(toss\s+(it|that|this)\s+in\s+the\s+(cart|basket|bag))",
            r"(drop\s+(it|that|this)\s+in\s+the\s+(cart|basket|bag))",
            r"(i\s+(want|need)\s+to\s+add\s+.*(to\s+(cart|basket|bag))?)",
            r"^(add\s+to\s+(cart|basket|bag))$",
            r"(i'?ll\s+take\s+(that|it|this|them))",
            r"(i\s+want\s+(to\s+)?(grab|get|cop|snag|scoop)\s+(this|that|it|them))",
            r"(put\s+the\s+\w+\s+(ones?|shoes?|kicks?)\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(add\s+the\s+\w+\s+(ones?|shoes?|kicks?)\s+to\s+(my\s+)?(cart|basket|bag))",
            r"(get\s+me\s+(that|it|this|them))",
            r"(hook\s+me\s+up\s+with\s+(that|it|this|them))",
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
            r"(show|view|see|what'?s?\s+in|check|open)\s+(my\s+)?(cart|basket|bag)",
            r"^cart$",
            r"^(my\s+)?cart\s*(contents)?$",
            r"what\s+(is\s+)?(in\s+)?(my\s+)?(cart|basket|bag)",
            r"(what'?s\s+in\s+(my\s+)?(cart|basket|bag))",
            r"(cart|basket|bag)\s*(contents|items|stuff)?$",
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
            r"(let'?s\s+do\s+this|let'?s\s+go)",
            r"(i'?m\s+ready\s+to\s+(buy|pay|checkout|purchase))",
            r"(ring\s+me\s+up|take\s+my\s+money)",
            r"(time\s+to\s+(pay|checkout|buy)|ready\s+to\s+(pay|checkout|buy|purchase))",
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

        # Order tracking patterns with order number extraction
        # Pattern matches: #1003, order 1003, order #1003, order ORD-123, etc.
        # Story 11-3: Consolidated from two duplicate blocks (3 shared + 2 unique 4th patterns)
        order_number_pattern = r"(?:^|\s)(?:#|order\s*(?:#|number|no\.?)?\s*)((?:[0-9][A-Za-z0-9\-]*|[A-Za-z]+[-][A-Za-z0-9\-]+|[A-Za-z]+[0-9][A-Za-z0-9\-]*))(?:\b|$)"
        order_number_match = re.search(order_number_pattern, lower_msg)

        order_patterns = [
            r"(where\s+is\s+my|track\s+my|check\s+my|where'?s?\s+my|when'?s?\s+my)\s+(order|stuff|package|delivery|shipment)",
            r"(order\s+status|shipping\s+status|delivery\s+status)",
            r"^order$",
            r"(?:^|\s)(?:#|order\s*(?:#|number|no\.?)?\s*)(?:[0-9][A-Za-z0-9\-]*|[A-Za-z]+[-][A-Za-z0-9\-]+|[A-Za-z]+[0-9][A-Za-z0-9\-]*)",
            r"(?:order\s*(?:number|#|no\.?)?\s*|#)\s*[A-Za-z0-9\-]{4,20}",
            r"(has\s+my\s+order\s+shipped|is\s+my\s+order\s+on\s+the\s+way)",
            r"(delivery\s+status|where\s+is\s+my\s+package|when\s+will\s+my\s+(stuff|order|package)\s+arrive)",
        ]
        for pattern in order_patterns:
            if re.search(pattern, lower_msg):
                entities = ExtractedEntities()
                if order_number_match:
                    order_number = order_number_match.group(1).strip().lstrip("#")
                    entities = ExtractedEntities(order_number=order_number)
                    self.logger.info(
                        "order_number_extracted",
                        order_number=order_number,
                        raw_message=message,
                    )
                return ClassificationResult(
                    intent=ClassifierIntentType.ORDER_TRACKING,
                    confidence=0.95,
                    entities=entities,
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
            r"(this\s+bot\s+isn'?t\s+helping|bot\s+is\s+useless|bot\s+can'?t\s+help)",
            r"(get\s+me\s+someone\s+who\s+knows|i\s+need\s+real\s+help)",
            r"(connect\s+me\s+to\s+(support|help|someone|agent))",
            r"(let\s+me\s+talk\s+to\s+(your\s+)?manager|talk\s+to\s+(a\s+)?real\s+person)",
            r"(not\s+(a\s+)?bot|no\s+more\s+bot|stop\s+(the\s+)?bot)",
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
            r"(products?|items?|things?|stuff|gear)\s+(under|below|less\s+than|cheaper\s+than|up\s+to)\s*\$?(\d+)",
            r"(under|below|up\s+to|no\s+more\s+than|max\s+)\s*\$?(\d+)",
            r"(products?|items?|stuff)\s+(for|at|under|around|about)\s*\$?(\d+)",
            r"(what\s+can\s+i\s+(get|buy|afford)\s+(for|with|under))\s*\$?(\d+)",
            r"(budget\s+(is|of|around|about))\s*\$?(\d+)",
            r"(looking|searching|shopping)\s+(for\s+)?(something\s+)?(under|below|around|about)\s*\$?(\d+)",
            r"(for|around|about)\s+\$?(\d+)\s*(bucks|dollars|bucks)?",
            r"(what\s+can\s+i\s+get)\s+(for|with|under)\s+\$?(\d+)",
        ]
        for pattern in price_patterns:
            match = re.search(pattern, lower_msg)
            if match:
                groups = match.groups()
                budget = None
                for g in reversed(groups):
                    if g and g.replace(".", "", 1).isdigit():
                        budget = float(g)
                        break
                if budget is None:
                    continue
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
            r"(most\s+expensive|highest\s+priced?|priciest|costliest|top\s+of\s+the\s+line)",
            r"(what'?s?\s+the\s+)?(most\s+expensive|highest\s+price|top\s+dollar)",
            r"(premium|luxury|high-end|expensive|top-shelf)\s+(products?|items?|options?|picks?|stuff)",
            r"(show\s+me\s+(the\s+)?(expensive|fancy|premium|luxury|high-end)\s*(stuff|options?|items?)?)",
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
            r"(cheapest|lowest\s+priced?|least\s+expensive|most\s+affordable|budget\s+friendly)",
            r"(what'?s?\s+the\s+)?(cheapest|lowest\s+price|best\s+(deal|value|bang\s+for\s+buck))",
            r"(budget|affordable|inexpensive|wallet\s+friendly|won'?t\s+break\s+the\s+bank)",
            r"(on\s+a\s+budget|(good|great)\s+(deal|bargain|steal))",
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
                    intent=ClassifierIntentType.PRODUCT_RECOMMENDATION,
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
            (r"(wondering\s+if\s+you\s+(have|carry|stock|sell))\s+(?:any\s+)?(\w+)", 3),
            (r"(do\s+you\s+(carry|stock|sell|have))\s+(?:any\s+)?(\w+)", 3),
            (
                r"i'?m\s+(in\s+the\s+market\s+for|shopping\s+around\s+for|after)\s+(?:a\s+|an\s+)?(\w+)",
                2,
            ),
            (r"(browsing|shopping|search)\s+(?:for\s+)?(\w+)", 2),
            (r"(got\s+any|any\s+)(\w+)(?:\s+(?:products?|items?|stuff))?", 2),
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

        check_consent_patterns = [
            r"(are|is)\s+(my\s+)?(preferences?|data|consent|settings)\s+(saved|stored|recorded|wishlist)",
            r"(confirm|check|verify)\s+(if\s+)?(my\s+)?(preferences?|data|consent)",
            r"what('?s|\s+is)\s+(my\s+)?(consent|preference)\s+status",
            r"do\s+you\s+(remember|know)\s+(my\s+)?(preferences?|data)",
            r"(show|tell)\s+me\s+(my\s+)?(consent|preference)\s+status",
            r"(did\s+i\s+(say|tell|let)\s+you\s+(to\s+)?(remember|save|keep)\s+(my\s+)?(data|info|preferences?))",
            r"(you\s+(still\s+)?(remember|know)\s+(my\s+)?(info|data|preferences?|settings))",
        ]
        for pattern in check_consent_patterns:
            if re.search(pattern, lower_msg):
                return ClassificationResult(
                    intent=ClassifierIntentType.CHECK_CONSENT_STATUS,
                    confidence=0.95,
                    entities=ExtractedEntities(),
                    raw_message=message,
                    llm_provider="pattern",
                    model="regex",
                    processing_time_ms=0,
                )

        forget_patterns = [
            r"(forget|clear|reset|delete|wipe|erase)\s+(my\s+)?(preferences?|data|cart|memory|info|history)",
            r"(start\s+over|start\s+again|fresh\s+start|clean\s+slate|wipe\s+clean)",
            r"(don'?t\s+(remember|save|keep|store)\s+(my\s+)?(info|data|preferences?|stuff))",
            r"(erase|wipe|scrub)\s+(everything|all\s+(my\s+)?(data|info))",
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
        entities: dict[str, Any] | None = None,
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

            if intent_name in ("product_search", "product_inquiry", "product_recommendation"):
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
        cart: dict | None = None,
    ) -> tuple[int, int] | None:
        """Persist conversation and messages to database.

        Story 5-10 Code Review Fix (C8):
        - Creates/updates Conversation record
        - Creates Message records for user and bot
        - Enables widget conversations to appear in conversation page

        Story 6-1: Consent-based persistence
        - Only persist conversation messages if consent granted
        - Always persist operational data (cart, order refs) regardless of consent

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
            Tuple of (conversation_id, bot_message_id) if persisted, None on failure
        """
        can_store_conversation = context.consent_state.can_store_conversation

        if not can_store_conversation:
            self.logger.debug(
                "conversation_persist_skipped_no_consent",
                merchant_id=merchant_id,
                session_id=context.session_id,
                consent_status=context.consent_state.status,
            )
            if cart is not None and intent in ("checkout", "order_tracking"):
                pass
            else:
                return None

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
                    data_tier=DataTier.VOLUNTARY,
                )
                db.add(conversation)
                await db.flush()

            user_msg = Message(
                conversation_id=conversation.id,
                sender="customer",
                content=user_message,
                message_type="text",
                data_tier=DataTier.VOLUNTARY,
            )
            user_msg.set_encrypted_content(user_message, "customer")
            db.add(user_msg)

            bot_msg = Message(
                conversation_id=conversation.id,
                sender="bot",
                content=bot_response,
                message_type="text",
                data_tier=DataTier.VOLUNTARY,
                message_metadata={
                    "intent": intent,
                    "confidence": confidence,
                    "channel": context.channel,
                },
            )
            db.add(bot_msg)
            await db.flush()  # Ensure IDs are generated

            if cart is not None:
                if conversation.conversation_data is None:
                    conversation.conversation_data = {}
                conversation.conversation_data["cart"] = cart

            conversation.updated_at = datetime.utcnow()

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

            return conversation.id, bot_msg.id

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
    ) -> ConversationResponse | None:
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
                    message=PersonalityAwareResponseFormatter.format_response(
                        "conversation",
                        "bot_paused",
                        merchant.personality or PersonalityType.FRIENDLY,
                    ),
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
    ) -> ConversationResponse | None:
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
                if datetime.now(UTC) > expires_dt:
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
        now = datetime.now(UTC)
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

    async def _check_and_prompt_consent(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
    ) -> ConversationResponse | None:
        """Check consent status and prompt if needed.

        Story 6-1: Opt-In Consent Flow
        Task 3.1: Consent check integration

        Checks if consent prompt should be shown and updates context state.
        Returns a consent prompt response if needed.

        Args:
            db: Database session
            context: Conversation context (will be updated in-place)
            merchant: Merchant model

        Returns:
            ConversationResponse with consent prompt if needed, None otherwise
        """
        try:
            consent_service = ConversationConsentService(db=db)

            consent = await consent_service.get_consent_for_conversation(
                session_id=context.session_id,
                merchant_id=merchant.id,
                visitor_id=context.consent_state.visitor_id,
            )

            if consent:
                # Compute status from granted and revoked_at fields
                # Consent model doesn't have a 'status' property
                if consent.granted and consent.revoked_at is None:
                    status = ConsentStatus.OPTED_IN
                elif consent.granted is False and consent.revoked_at is not None:
                    status = ConsentStatus.OPTED_OUT
                else:
                    status = ConsentStatus.PENDING

                context.consent_state.status = status
                context.consent_state.can_store_conversation = status == ConsentStatus.OPTED_IN
                context.consent_state.prompt_shown = consent.consent_message_shown or False

                if status == ConsentStatus.OPTED_IN:
                    context.consent_status = "granted"
                elif status == ConsentStatus.OPTED_OUT:
                    context.consent_status = "denied"
                else:
                    context.consent_status = "pending"

                self.logger.debug(
                    "consent_status_loaded",
                    session_id=context.session_id,
                    merchant_id=merchant.id,
                    status=status,
                    can_store=context.consent_state.can_store_conversation,
                )
                # If consent exists and prompt was already shown, don't show again
                return None

            # No consent record exists - this is a new conversation
            # Show consent prompt by returning a response
            context.consent_state.status = ConsentStatus.PENDING
            context.consent_state.can_store_conversation = False
            context.consent_state.prompt_shown = False
            context.consent_status = "pending"

            self.logger.info(
                "consent_status_pending_no_record_showing_prompt",
                session_id=context.session_id,
                merchant_id=merchant.id,
                visitor_id=context.consent_state.visitor_id,
            )

            # Import prompt service to generate consent prompt message
            from app.services.consent.consent_prompt_service import ConsentPromptService

            prompt_service = ConsentPromptService()

            consent_prompt_message = prompt_service.get_consent_prompt_message(
                personality=merchant.personality,
            )

            # Get quick replies for the consent prompt
            quick_replies = prompt_service.get_consent_quick_replies()

            # Return consent prompt response
            return ConversationResponse(
                message=consent_prompt_message,
                intent="consent_prompt",
                confidence=1.0,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={
                    "consent_prompt_required": True,
                    "consent_status": ConsentStatus.PENDING.value,
                    "quick_replies": quick_replies,
                },
            )

        except Exception as e:
            self.logger.warning(
                "consent_check_failed",
                session_id=context.session_id,
                merchant_id=merchant.id,
                error=str(e),
            )
            context.consent_state.can_store_conversation = False
            return None

    async def _check_faq_match(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
        message: str,
    ) -> ConversationResponse | None:
        """Check for FAQ match before intent classification.

        If FAQ matches with high confidence, return rephrased answer immediately.
        This prevents handoff from being triggered for common questions.

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model
            message: User's message

        Returns:
            ConversationResponse with FAQ answer if matched, None otherwise
        """
        try:
            from app.models.faq import Faq
            from app.services.faq import match_faq, rephrase_faq_with_personality

            # Get merchant's FAQs
            result = await db.execute(
                select(Faq).where(Faq.merchant_id == merchant.id).order_by(Faq.order_index)
            )
            faqs = list(result.scalars().all())

            if not faqs:
                return None

            # Try to match FAQ
            faq_match = await match_faq(message, faqs)

            if not faq_match:
                return None

            self.logger.info(
                "faq_matched_unified",
                merchant_id=merchant.id,
                session_id=context.session_id,
                faq_id=faq_match.faq.id,
                confidence=faq_match.confidence,
                match_type=faq_match.match_type,
            )

            # Get personality settings
            personality_type = (
                merchant.personality if merchant.personality else PersonalityType.FRIENDLY
            )
            business_name = merchant.business_name or "our store"
            bot_name = merchant.bot_name if merchant.bot_name else "Mantisbot"

            # Get LLM service for rephrasing
            llm_service = await self._get_merchant_llm(merchant, db, context)

            # Rephrase with personality
            faq_answer = faq_match.faq.answer
            try:
                faq_answer = await rephrase_faq_with_personality(
                    llm_service=llm_service,
                    faq_answer=faq_match.faq.answer,
                    personality_type=personality_type,
                    business_name=business_name,
                    bot_name=bot_name,
                )
            except Exception as e:
                self.logger.warning(
                    "faq_rephrase_failed_unified",
                    faq_id=faq_match.faq.id,
                    error=str(e),
                )

            return ConversationResponse(
                message=faq_answer,
                intent="faq",
                confidence=faq_match.confidence,
                checkout_url=None,
                fallback=False,
                fallback_url=None,
                products=None,
                cart=None,
                order=None,
                metadata={
                    "faq_id": faq_match.faq.id,
                    "faq_match_type": faq_match.match_type,
                    "faq_question": faq_match.faq.question,
                    "source": "faq_preprocessor_unified",
                },
            )

        except Exception as e:
            self.logger.warning(
                "faq_check_failed_unified",
                merchant_id=merchant.id,
                session_id=context.session_id,
                error=str(e),
            )
            return None

    async def _check_handoff(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Merchant,
        message: str,
        confidence: float,
        intent_name: str,
    ) -> ConversationResponse | None:
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
            from app.core.config import settings
            from app.services.handoff.detector import HandoffDetector

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

                handoff_message = await self._get_handoff_message(merchant)

                await self._update_conversation_handoff_status(
                    db=db,
                    context=context,
                    merchant=merchant,
                    reason=result.reason.value if result.reason else "unknown",
                    confidence_count=result.confidence_count,
                    user_message=message,
                    bot_response=handoff_message,
                )

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
    ) -> Any | None:
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
        user_message: str = "",
        bot_response: str = "",
    ) -> None:
        """Update conversation status to handoff in database.

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model
            reason: Handoff reason
            confidence_count: Consecutive low confidence count
            user_message: User's message that triggered handoff
            bot_response: Bot's handoff response
        """
        try:
            from app.models.conversation import Conversation, DataTier
            from app.models.message import Message

            conversation = await self._get_conversation(db, context.session_id, merchant.id)

            if not conversation:
                conversation = Conversation(
                    merchant_id=merchant.id,
                    platform=context.channel,
                    platform_sender_id=context.session_id,
                    status="handoff",
                    handoff_status="pending",
                    handoff_triggered_at=datetime.utcnow(),
                    handoff_reason=reason,
                    consecutive_low_confidence_count=confidence_count,
                    data_tier=DataTier.VOLUNTARY,
                )
                db.add(conversation)
                await db.flush()
                self.logger.info(
                    "handoff_conversation_created",
                    session_id=context.session_id,
                    reason=reason,
                )
            else:
                conversation.status = "handoff"
                conversation.handoff_status = "pending"
                conversation.handoff_triggered_at = datetime.utcnow()
                conversation.handoff_reason = reason
                conversation.consecutive_low_confidence_count = confidence_count
                self.logger.info(
                    "handoff_status_updated_unified",
                    conversation_id=conversation.id,
                    session_id=context.session_id,
                    reason=reason,
                    confidence_count=confidence_count,
                )

            if user_message:
                user_msg = Message(
                    conversation_id=conversation.id,
                    sender="customer",
                    content=user_message,
                    message_type="text",
                    data_tier=DataTier.VOLUNTARY,
                )
                user_msg.set_encrypted_content(user_message, "customer")
                db.add(user_msg)

            if bot_response:
                bot_msg = Message(
                    conversation_id=conversation.id,
                    sender="bot",
                    content=bot_response,
                    message_type="text",
                    data_tier=DataTier.VOLUNTARY,
                )
                bot_msg.set_encrypted_content(bot_response, "bot")
                db.add(bot_msg)

            # Create handoff alert for queue visibility
            try:
                from sqlalchemy import select

                from app.models.handoff_alert import HandoffAlert

                # Check if alert already exists for this conversation
                existing_alert = await db.execute(
                    select(HandoffAlert).where(HandoffAlert.conversation_id == conversation.id)
                )
                if not existing_alert.scalars().first():
                    # Determine urgency level
                    urgency_level = "low"
                    message_lower = (user_message or "").lower()

                    high_priority_keywords = [
                        "checkout",
                        "payment",
                        "charged",
                        "refund",
                        "cancel",
                    ]
                    medium_priority_keywords = [
                        "order",
                        "delivery",
                        "shipping",
                        "track",
                        "where is",
                    ]

                    if any(kw in message_lower for kw in high_priority_keywords):
                        urgency_level = "high"
                    elif reason in ("low_confidence", "clarification_loop"):
                        urgency_level = "medium"
                    elif any(kw in message_lower for kw in medium_priority_keywords):
                        urgency_level = "medium"

                    # Get customer ID (masked)
                    customer_id = None
                    if conversation.platform_sender_id:
                        if len(conversation.platform_sender_id) > 4:
                            customer_id = f"{conversation.platform_sender_id[:4]}****"
                        else:
                            customer_id = conversation.platform_sender_id

                    # Get conversation preview
                    conversation_preview = user_message[:500] if user_message else None

                    # Check if offline (outside business hours)
                    is_offline = False
                    try:
                        from app.services.handoff.business_hours_handoff_service import (
                            BusinessHoursHandoffService,
                        )

                        bh_service = BusinessHoursHandoffService()
                        is_offline = bh_service.is_offline_handoff(merchant.business_hours_config)
                    except Exception:
                        pass  # Default to False if check fails

                    # Create alert
                    alert = HandoffAlert(
                        conversation_id=conversation.id,
                        merchant_id=merchant.id,
                        urgency_level=urgency_level,
                        customer_name=None,
                        customer_id=customer_id,
                        conversation_preview=conversation_preview,
                        wait_time_seconds=0,
                        is_read=False,
                        is_offline=is_offline,
                    )
                    db.add(alert)
                    await db.flush()

                    self.logger.info(
                        "handoff_alert_created",
                        conversation_id=conversation.id,
                        urgency_level=urgency_level,
                        is_offline=is_offline,
                    )
            except Exception as e:
                self.logger.warning(
                    "handoff_alert_creation_failed",
                    conversation_id=conversation.id,
                    error=str(e),
                )

            await db.commit()

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

    def _looks_like_order_number(self, message: str) -> bool:
        """Check if message looks like an order number.

        Args:
            message: User message

        Returns:
            True if message looks like an order number
        """
        import re

        cleaned = message.strip().lstrip("#")
        if len(cleaned) < 4 or len(cleaned) > 20:
            return False
        return bool(re.match(r"^[A-Za-z0-9\-]+$", cleaned))

    def _is_simple_greeting(self, message: str) -> bool:
        """Check if message is a simple greeting that doesn't need RAG retrieval.

        Simple greetings like "hi", "hello", "hey", "thanks" don't benefit from
        RAG context and shouldn't show source citations.

        Args:
            message: User message

        Returns:
            True if message is a simple greeting
        """
        import re

        normalized = message.strip().lower()
        normalized = re.sub(r"[^\w\s]", "", normalized)
        words = normalized.split()

        if len(words) > 4:
            return False

        greeting_patterns = [
            r"^(hi|hello|hey|heya|hii+|hola|howdy|greetings)$",
            r"^(good\s*(morning|afternoon|evening|day))$",
            r"^(what'?s?\s*up|sup)$",
            r"^(how\s*(are|r)\s*(you|u|ya))$",
            r"^(thanks?|thank\s*you|thx|ty|cheers)$",
            r"^(ok|okay|k|kk|cool|got\s*it|understood)$",
            r"^(bye|goodbye|see\s*ya|later|ciao)$",
            r"^(yes|no|yep|nope|yeah|nah)$",
            r"^(hi\s*there|hello\s*there|hey\s*there)$",
        ]

        combined = " ".join(words)
        for pattern in greeting_patterns:
            if re.match(pattern, combined):
                return True

        return False

    def _is_question(self, message: str) -> bool:
        """Check if message is a question that warrants RAG retrieval and citations.

        Only actual questions should show source citations. Statements, greetings,
        and conversational messages should not show citations.

        Args:
            message: User message

        Returns:
            True if message is a question
        """
        import re

        normalized = message.strip()

        if not normalized:
            return False

        if self._is_simple_greeting(message):
            return False

        if normalized.endswith("?"):
            return True

        question_starters = [
            r"^(what|whats|what's|which|where|when|why|how|who|whom)",
            r"^(can|could|would|will|should|is|are|do|does|did|has|have|had)",
            r"^(tell\s+me|explain|describe|help\s+me|show\s+me)",
            r"^(i\s+want\s+to\s+know|i\s+need\s+to\s+know|i'm\s+wondering)",
            r"^(could\s+you|would\s+you|can\s+you|will\s+you)",
            r"^(any\s+idea|do\s+you\s+know)",
        ]

        lower = normalized.lower()
        for pattern in question_starters:
            if re.match(pattern, lower):
                return True

        question_words = [
            "what",
            "where",
            "when",
            "why",
            "how",
            "who",
            "which",
            "can i",
            "could i",
            "would i",
            "should i",
            "is there",
            "are there",
            "do you have",
            "does it",
            "how much",
            "how many",
            "how long",
            "how do",
        ]
        lower_no_punct = re.sub(r"[^\w\s]", "", lower)
        for qw in question_words:
            if qw in lower_no_punct:
                return True

        return False

    def _build_turn_context_snapshot(
        self,
        confidence: float,
        processing_time_ms: float,
        context: ConversationContext,
        sentiment_adaptation: SentimentAdaptation | None = None,
        sentiment_confidence: float | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "confidence": confidence,
            "processing_time_ms": int(processing_time_ms),
            "has_context_reference": len(context.conversation_history) > 0,
        }
        if mode is not None:
            snapshot["mode"] = mode
        if sentiment_adaptation and sentiment_adaptation.original_score:
            snapshot["sentiment_score"] = sentiment_adaptation.original_score.confidence
        elif sentiment_confidence is not None:
            snapshot["sentiment_score"] = sentiment_confidence

        clarification_state = context.clarification_state
        if clarification_state and clarification_state.multi_turn_state != "IDLE":
            snapshot["clarification_state"] = clarification_state.multi_turn_state
            snapshot["clarification_attempt_count"] = clarification_state.attempt_count

        return snapshot

    async def _write_conversation_turn(
        self,
        db: AsyncSession,
        conversation_id: int,
        turn_number: int,
        intent_detected: str | None,
        sentiment: str | None,
        context_snapshot: dict[str, Any],
    ) -> None:
        async with db.begin_nested():
            turn = ConversationTurn(
                conversation_id=conversation_id,
                turn_number=turn_number,
                intent_detected=intent_detected,
                context_snapshot=context_snapshot,
                sentiment=sentiment,
            )
            db.add(turn)
            await db.flush()

    async def _detect_and_record_knowledge_gap(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation_id: int | None,
        user_message: str,
        bot_response: str,
        confidence: float,
        rag_chunks: list[RetrievedChunk],
        faq_matched: bool,
    ) -> None:
        """Detect and record knowledge gaps.

        A knowledge gap occurs when:
        1. User asks a question AND
        2. (FAQ doesn't match AND RAG returns no chunks) OR
           LLM indicates it couldn't find information OR
           Confidence is low (< 0.5)

        Args:
            db: Database session
            merchant: Merchant model
            conversation_id: Conversation ID (may be None)
            user_message: User's message
            bot_response: Bot's response
            confidence: Classification confidence
            rag_chunks: RAG chunks retrieved (empty if no match)
            faq_matched: Whether an FAQ matched
        """
        try:
            if not self._is_question(user_message):
                return

            gap_types: list[str] = []

            has_rag_match = len(rag_chunks) > 0
            if not faq_matched:
                gap_types.append(GapType.NO_FAQ_MATCH.value)
            if not has_rag_match:
                gap_types.append(GapType.NO_RAG_MATCH.value)
            if confidence < 0.5:
                gap_types.append(GapType.LOW_CONFIDENCE.value)
            if self._indicates_no_information_found(bot_response):
                gap_types.append(GapType.LLM_NO_INFO.value)

            if not gap_types:
                return

            import hashlib

            normalized_question = " ".join(user_message.lower().split())
            question_hash = hashlib.sha256(normalized_question.encode()).hexdigest()[:32]

            existing_gap = await db.execute(
                select(KnowledgeGap).where(
                    KnowledgeGap.merchant_id == merchant.id,
                    KnowledgeGap.question_hash == question_hash,
                    KnowledgeGap.resolved == False,
                )
            )
            existing = existing_gap.scalars().first()

            if existing:
                existing.occurrence_count += 1
                existing.last_occurred_at = datetime.now(UTC)
                existing.gap_types = list(set(existing.gap_types + gap_types))
                existing.sample_response = bot_response
                self.logger.debug(
                    "knowledge_gap_updated",
                    merchant_id=merchant.id,
                    question_hash=question_hash,
                    occurrence_count=existing.occurrence_count,
                )
            else:
                new_gap = KnowledgeGap(
                    merchant_id=merchant.id,
                    conversation_id=conversation_id,
                    question=user_message,
                    question_hash=question_hash,
                    gap_types=gap_types,
                    occurrence_count=1,
                    sample_response=bot_response,
                )
                db.add(new_gap)
                self.logger.info(
                    "knowledge_gap_detected",
                    merchant_id=merchant.id,
                    question_preview=user_message[:50],
                    gap_types=gap_types,
                )

            await db.commit()

        except Exception as e:
            self.logger.warning(
                "knowledge_gap_detection_failed",
                merchant_id=merchant.id,
                error=str(e),
            )

    def _indicates_no_information_found(self, message: str) -> bool:
        """Check if the LLM response indicates it couldn't find relevant information.

        When the LLM explicitly says it couldn't find information, we should hide
        source citations to avoid misleading users with sources that weren't actually used.

        Args:
            message: LLM response message

        Returns:
            True if response indicates no information was found
        """
        import re

        lower = message.lower()

        no_info_patterns = [
            r"couldn'?t\s+find\s+(any\s+)?information",
            r"could\s+not\s+find\s+(any\s+)?information",
            r"no\s+information\s+(about|regarding|on|in)",
            r"don'?t\s+have\s+(any\s+)?information",
            r"do\s+not\s+have\s+(any\s+)?information",
            r"not\s+able\s+to\s+(find|answer|locate)",
            r"unable\s+to\s+(find|answer|locate)",
            r"doesn'?t\s+(mention|say|contain|include)",
            r"does\s+not\s+(mention|say|contain|include)",
            r"no\s+(mention|reference|details|information)",
            r"nothing\s+(about|in)\s+(the\s+)?(documents?|files?|context)",
            r"documents?\s+(i\s+have\s+)?(don'?t|doesn'?t|do\s+not|does\s+not)",
        ]

        for pattern in no_info_patterns:
            if re.search(pattern, lower):
                return True

        return False

    async def _check_proactive_gathering(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Any,
        message: str,
    ) -> ConversationResponse | None:
        """Story 11-8: Proactive information gathering.

        Checks active gathering state and handles response.
        If no active state, starts fresh gathering.

        Only runs for ecommerce mode with classified intents.
        Mutual exclusion: skip if CLARIFYING state.
        Max 2 gathering rounds then best-effort routing.
        """
        from app.services.proactive_gathering.intent_requirements import _SKIP_INTENTS
        from app.services.proactive_gathering.proactive_gathering_service import (
            ProactiveGatheringService,
        )
        from app.services.proactive_gathering.schemas import GatheringState as GatheringStateSchema

        gs = context.gathering_state
        if gs and gs.active and not gs.is_complete:
            return await self._handle_active_gathering(
                db,
                context,
                merchant,
                message,
                gs,
            )

        mode = getattr(merchant, "onboarding_mode", "ecommerce") or "ecommerce"
        personality = getattr(merchant, "personality", "friendly") or "friendly"
        bot_name = getattr(merchant, "bot_name", "ShopBot")
        conv_id = context.conversation_id or str(context.session_id) or ""

        if hasattr(self, "_cached_classification") and self._cached_classification is not None:
            classification = self._cached_classification
            self._cached_classification = None
        else:
            llm_service = await self._get_merchant_llm(merchant, db, context)
            classification = await self._classify_intent(
                llm_service=llm_service,
                message=message,
                context=context,
            )
        if not classification or not classification.entities:
            return None

        classification_intent = classification.intent
        if classification_intent in _SKIP_INTENTS:
            return None

        gathering_service = ProactiveGatheringService()
        entities = classification.entities
        missing = gathering_service.detect_missing_info(
            classification_intent,
            entities,
            context,
            mode,
        )
        if not missing:
            return None

        missing_required = [f for f in missing if f.required]
        if not missing_required:
            return None

        partial = gathering_service.extract_partial_answer(
            message,
            missing_required,
            mode,
        )
        remaining = [f for f in missing_required if f.field_name not in partial]
        if not remaining:
            return None

        intent_val = (
            classification_intent.value
            if hasattr(classification_intent, "value")
            else str(classification_intent)
        )
        context.gathering_state = GatheringStateSchema(
            active=True,
            round_count=0,
            original_intent=intent_val,
            original_query=message,
            missing_fields=remaining,
            gathered_data=partial,
        )
        gathering_msg = gathering_service.generate_gathering_message(
            remaining,
            personality,
            bot_name,
            mode,
            context,
            conv_id,
        )
        self.logger.info("proactive_gathering_started")
        return ConversationResponse(
            message=gathering_msg,
            intent="proactive_gathering",
            confidence=0.9,
        )

    async def _handle_active_gathering(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Any,
        message: str,
        gs: Any,
    ) -> ConversationResponse | None:
        """Handle an active proactive gathering round."""
        from app.models.merchant import PersonalityType
        from app.services.personality.conversation_templates import PROACTIVE_GATHERING_TEMPLATES
        from app.services.proactive_gathering.proactive_gathering_service import (
            ProactiveGatheringService,
        )

        mode = getattr(merchant, "onboarding_mode", "ecommerce") or "ecommerce"
        personality = getattr(merchant, "personality", "friendly") or "friendly"
        bot_name = getattr(merchant, "bot_name", "ShopBot")
        conv_id = context.conversation_id or str(context.session_id) or ""

        next_round = gs.round_count + 1
        if next_round >= 2:
            gs.is_complete = True
            gs.active = False
            context.gathering_state = gs
            best_effort_fallback = (
                "I'll do my best with what I have! Let me search with the information provided."
            )
            best_effort_msg = best_effort_fallback
            try:
                pt = PersonalityType(personality)
                best_effort_msg = PROACTIVE_GATHERING_TEMPLATES.get(pt, {}).get(
                    "best_effort_notice", best_effort_fallback
                )
            except (ValueError, KeyError):
                pass
            return ConversationResponse(
                message=best_effort_msg,
                intent="proactive_gathering",
                confidence=0.85,
            )

        gathering_service = ProactiveGatheringService()
        extracted = gathering_service.extract_partial_answer(
            message,
            gs.missing_fields,
            mode,
        )
        remaining = [f for f in gs.missing_fields if f.field_name not in extracted]
        gs.gathered_data.update(extracted)

        if not remaining:
            gs.is_complete = True
            gs.active = False
            context.gathering_state = gs
            self.logger.info("proactive_gathering_complete")
            return None

        gs.missing_fields = remaining
        gs.round_count = next_round
        context.gathering_state = gs

        gathering_msg = gathering_service.generate_gathering_message(
            remaining,
            personality,
            bot_name,
            mode,
            context,
            conv_id,
        )
        self.logger.info("proactive_gathering_round")
        return ConversationResponse(
            message=gathering_msg,
            intent="proactive_gathering",
            confidence=0.9,
        )

    async def _check_multi_turn_state(
        self,
        db: AsyncSession,
        context: ConversationContext,
        merchant: Any,
        message: str,
    ) -> ConversationResponse | None:
        """Check if conversation is in an active multi-turn flow.

        Story 11-2: Multi-Turn Query Handling
        Routes directly to multi-turn handler when state is CLARIFYING or REFINE_RESULTS.
        Skips normal intent classification to avoid misrouting.

        Args:
            db: Database session
            context: Conversation context
            merchant: Merchant model
            message: User's message

        Returns:
            ConversationResponse if multi-turn flow is active, None otherwise
        """
        from app.services.clarification.question_generator import QuestionGenerator
        from app.services.multi_turn import (
            ConstraintAccumulator,
            ConversationStateMachine,
            MessageClassifier,
            MessageType,
            MultiTurnConfig,
            MultiTurnState,
            MultiTurnStateEnum,
        )

        clarification_state = context.clarification_state
        mt_state_str = getattr(clarification_state, "multi_turn_state", "IDLE")

        if mt_state_str in ("IDLE", "COMPLETE") or mt_state_str == MultiTurnStateEnum.IDLE:
            return None

        # Story 11-9 defense-in-depth: if message matches SUMMARIZE pattern, don't intercept
        if self._check_summarize_pattern(message) is not None:
            return None

        conv_id = context.conversation_id
        if not conv_id:
            return None

        mode = getattr(merchant, "onboarding_mode", "ecommerce") or "ecommerce"

        mt_state = MultiTurnState(
            state=mt_state_str,
            turn_count=getattr(clarification_state, "turn_count", 0),
            accumulated_constraints=getattr(clarification_state, "accumulated_constraints", {}),
            questions_asked=list(clarification_state.questions_asked),
            pending_questions=[],
            original_query=getattr(clarification_state, "original_query", None),
            invalid_response_count=getattr(clarification_state, "invalid_response_count", 0),
            mode=mode,
        )

        config = MultiTurnConfig()
        sm = ConversationStateMachine(config)
        accumulator = ConstraintAccumulator()
        question_gen = QuestionGenerator()

        classifier = MessageClassifier()
        msg_type = await classifier.classify(message, mt_state, {})

        async def _persist_mt_state() -> None:
            conversation = await self._get_conversation(db, context.session_id, merchant.id)
            if conversation and hasattr(conversation, "context"):
                ctx_data = conversation.context if isinstance(conversation.context, dict) else {}
                cs = clarification_state.model_dump()
                ctx_data["clarification_state"] = cs
                conversation.context = ctx_data
                await db.commit()

        if msg_type == MessageType.TOPIC_CHANGE:
            sm.reset(mt_state)
            clarification_state.multi_turn_state = "IDLE"
            clarification_state.turn_count = 0
            clarification_state.accumulated_constraints = {}
            clarification_state.original_query = None
            clarification_state.invalid_response_count = 0
            await _persist_mt_state()
            return None

        if msg_type == MessageType.INVALID_RESPONSE:
            sm.increment_invalid_count(mt_state)
            clarification_state.invalid_response_count = mt_state.invalid_response_count

            if mt_state.invalid_response_count >= config.max_invalid_responses:
                sm.transition_to_refine(mt_state, "max_invalid_responses")
                clarification_state.multi_turn_state = "REFINE_RESULTS"
                await _persist_mt_state()
                understanding = question_gen.generate_summary_of_understanding(
                    mt_state.accumulated_constraints, mode
                )
                try:
                    msg = PersonalityAwareResponseFormatter.format_response(
                        "clarification_natural",
                        "near_limit_summary",
                        merchant.personality or PersonalityType.FRIENDLY,
                        understanding=understanding,
                    )
                except Exception:
                    msg = f"Let me search based on what we know: {understanding}"
                return ConversationResponse(
                    message=msg,
                    intent="clarification",
                    confidence=0.8,
                )

            await _persist_mt_state()
            try:
                retry_msg = PersonalityAwareResponseFormatter.format_response(
                    "clarification_natural",
                    "invalid_response_retry",
                    merchant.personality or PersonalityType.FRIENDLY,
                )
            except Exception:
                retry_msg = "I didn't quite catch that. Could you try again?"
            return ConversationResponse(
                message=retry_msg,
                intent="clarification",
                confidence=0.7,
            )

        if msg_type == MessageType.CONSTRAINT_ADDITION:
            new_constraints = accumulator.accumulate(
                message, mt_state.accumulated_constraints, mode
            )
            mt_state.accumulated_constraints = new_constraints
            clarification_state.accumulated_constraints = new_constraints

            sm.transition_to_refine(mt_state, "constraint_added")
            clarification_state.multi_turn_state = "REFINE_RESULTS"
            await _persist_mt_state()

            understanding = question_gen.generate_summary_of_understanding(new_constraints, mode)
            try:
                ack_msg = PersonalityAwareResponseFormatter.format_response(
                    "clarification_natural",
                    "constraint_added_acknowledgment",
                    merchant.personality or PersonalityType.FRIENDLY,
                    understanding=understanding,
                )
            except Exception:
                ack_msg = f"Got it! {understanding} Let me refine the search."
            return ConversationResponse(
                message=ack_msg,
                intent="clarification",
                confidence=0.85,
            )

        if msg_type == MessageType.CLARIFICATION_RESPONSE:
            new_constraints = accumulator.accumulate(
                message, mt_state.accumulated_constraints, mode
            )
            mt_state.accumulated_constraints = new_constraints
            clarification_state.accumulated_constraints = new_constraints

            current_pending = getattr(mt_state, "pending_questions", [])
            constraint_name = current_pending[0] if current_pending else "general"

            sm.process_clarification_response(mt_state, constraint_name, message, is_valid=True)
            clarification_state.turn_count = mt_state.turn_count
            clarification_state.multi_turn_state = mt_state.state

            if sm.is_near_turn_limit(mt_state) and mt_state.state in (
                "CLARIFYING",
                MultiTurnStateEnum.CLARIFYING,
            ):
                understanding = question_gen.generate_summary_of_understanding(
                    new_constraints, mode
                )
                sm.transition_to_refine(mt_state, "near_turn_limit")
                clarification_state.multi_turn_state = "REFINE_RESULTS"
                await _persist_mt_state()
                try:
                    near_limit_msg = PersonalityAwareResponseFormatter.format_response(
                        "clarification_natural",
                        "near_limit_summary",
                        merchant.personality or PersonalityType.FRIENDLY,
                        understanding=understanding,
                    )
                except Exception:
                    near_limit_msg = f"Based on what you've told me: {understanding}"
                return ConversationResponse(
                    message=near_limit_msg,
                    intent="clarification",
                    confidence=0.85,
                )

            if mt_state.state in ("REFINE_RESULTS", MultiTurnStateEnum.REFINE_RESULTS):
                understanding = question_gen.generate_summary_of_understanding(
                    new_constraints, mode
                )
                await _persist_mt_state()
                try:
                    results_msg = PersonalityAwareResponseFormatter.format_response(
                        "clarification_natural",
                        "transition_to_results",
                        merchant.personality or PersonalityType.FRIENDLY,
                        understanding=understanding,
                    )
                except Exception:
                    results_msg = f"Here's what I've found: {understanding}"
                return ConversationResponse(
                    message=results_msg,
                    intent="clarification",
                    confidence=0.85,
                )

            try:
                question, next_constraint = await question_gen.generate_mode_aware_question(
                    pending_questions=current_pending,
                    questions_asked=mt_state.questions_asked,
                    mode=mode,
                    accumulated_constraints=new_constraints,
                )
                clarification_state.last_question = question
                clarification_state.last_type = next_constraint
                await _persist_mt_state()
                return ConversationResponse(
                    message=question,
                    intent="clarification",
                    confidence=0.8,
                )
            except ValueError:
                sm.transition_to_refine(mt_state, "all_questions_answered")
                clarification_state.multi_turn_state = "REFINE_RESULTS"
                understanding = question_gen.generate_summary_of_understanding(
                    new_constraints, mode
                )
                await _persist_mt_state()
                try:
                    thanks_msg = PersonalityAwareResponseFormatter.format_response(
                        "clarification_natural",
                        "transition_to_results_thanks",
                        merchant.personality or PersonalityType.FRIENDLY,
                        understanding=understanding,
                    )
                except Exception:
                    thanks_msg = f"Thanks for all the details! {understanding}"
                return ConversationResponse(
                    message=thanks_msg,
                    intent="clarification",
                    confidence=0.85,
                )

        return None
