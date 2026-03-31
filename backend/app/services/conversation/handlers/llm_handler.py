"""LLM handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService

Handles GENERAL and UNKNOWN intents with LLM-powered responses.
Enhanced with automatic product mention detection for product cards.
Story 9-4: Added quick reply generation for conversation continuation.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_redis_client
from app.models.merchant import Merchant, PersonalityType
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation_context import ConversationContextService
from app.services.llm.base_llm_service import BaseLLMService, LLMMessage
from app.services.personality.personality_prompts import get_personality_system_prompt

logger = structlog.get_logger(__name__)


class LLMHandler(BaseHandler):
    """Handler for GENERAL and UNKNOWN intents.

    Generates responses using LLM with merchant's personality
    and business context.

    Enhanced to detect product mentions and attach product cards.
    Only shows products for shopping-related queries (intent-aware).
    """

    PRODUCT_RELATED_INTENTS = {
        "product_search",
        "product_inquiry",
        "product_comparison",
        "price_inquiry",
        "recommendation",
    }

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        """Handle general/unknown intent with LLM.

        Story 11-1: Enhanced with conversation context memory integration.
        Injects mode-aware context into LLM prompts for better responses.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context (with channel info)
            entities: Extracted entities (not used for general)

        Returns:
            ConversationResponse with LLM-generated message
        """
        # Story 11-1: Retrieve conversation context memory
        conversation_context = None
        if context.conversation_id:
            conversation_context = await self._get_conversation_context(db, context.conversation_id)

        rag_context = None
        if context.metadata:
            rag_context = context.metadata.get("rag_context")

        bot_name = merchant.bot_name or "Mantisbot"
        business_name = merchant.business_name or "our store"
        personality_type: PersonalityType = merchant.personality or PersonalityType.FRIENDLY

        pending_state = self._get_pending_state(context)

        system_prompt = await self._build_system_prompt(
            db=db,
            merchant=merchant,
            bot_name=bot_name,
            business_name=business_name,
            personality_type=personality_type,
            pending_state=pending_state,
        )

        # Story 11-1: Inject conversation context into system prompt
        if conversation_context:
            system_prompt = self._inject_conversation_context(
                system_prompt,
                conversation_context,
                merchant.onboarding_mode or "ecommerce"
            )

        if rag_context:
            logger.debug(
                "llm_handler_rag_context_injecting",
                merchant_id=merchant.id,
                rag_context_length=len(rag_context),
                rag_context_preview=rag_context[:500],
            )
            system_prompt = self._inject_rag_context(system_prompt, rag_context)
        else:
            logger.debug(
                "llm_handler_rag_context_unavailable",
                merchant_id=merchant.id,
                message="No relevant knowledge base information found",
            )
            system_prompt = self._add_no_rag_note(system_prompt, business_name, merchant.onboarding_mode)

        messages = [LLMMessage(role="system", content=system_prompt)]

        for msg in context.conversation_history[-5:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append(LLMMessage(role=role, content=msg.get("content", "")))

        if rag_context:
            messages.append(
                LLMMessage(
                    role="user",
                    content=f"Context:\n{rag_context}",
                )
            )
        messages.append(LLMMessage(role="user", content=message))

        logger.debug(
            "llm_handler_messages",
            merchant_id=merchant.id,
            message_count=len(messages),
            system_prompt_length=len(system_prompt),
            has_rag_context=rag_context is not None,
        )
        try:
            response = await llm_service.chat(messages=messages, temperature=0.7)
            response_text = response.content

            if response_text and response_text.strip().startswith('{"intent"'):
                logger.warning(
                    "llm_handler_classification_leak",
                    merchant_id=merchant.id,
                    raw_response=response_text[:200],
                )
                response_text = f"I'd be happy to help you with that! Could you tell me a bit more?"
        except Exception as e:
            logger.warning(
                "llm_handler_fallback",
                merchant_id=merchant.id,
                error=str(e),
            )
            response_text = (
                f"I'm here to help you shop at {business_name}! "
                "You can ask me about products, check your cart, or place an order."
            )

        products = None
        if self._should_detect_products(message, response_text):
            products = await self._detect_product_mentions(
                response_text=response_text,
                merchant=merchant,
                llm_service=llm_service,
                db=db,
            )

        quick_replies = self._generate_quick_replies(message, response_text, merchant)

        # Determine response type based on whether RAG context was used
        response_type = "rag" if rag_context else "general"

        return ConversationResponse(
            message=response_text,
            intent="general",
            confidence=1.0,
            products=products,
            quick_replies=quick_replies,
            metadata={
                "bot_name": bot_name,
                "business_name": business_name,
                "response_type": response_type,
            },
        )

    def _should_detect_products(self, user_message: str, response_text: str) -> bool:
        """Determine if product cards should be shown based on message content.

        Product cards should only appear for shopping-related queries,
        not for informational questions like "where are you located?".

        Args:
            user_message: Original user message
            response_text: LLM's response

        Returns:
            True if product detection should run, False otherwise
        """
        lower_msg = user_message.lower().strip()

        non_product_patterns = [
            "where are you located",
            "where is your store",
            "what is your address",
            "what are your hours",
            "business hours",
            "shipping policy",
            "return policy",
            "how do i return",
            "track my order",
            "order status",
            "contact you",
            "phone number",
            "email address",
            "talk to human",
            "speak to someone",
        ]

        for pattern in non_product_patterns:
            if pattern in lower_msg:
                return False

        shopping_indicators = [
            "looking for",
            "do you have",
            "show me",
            "i want",
            "i need",
            "buy",
            "purchase",
            "how much",
            "price",
            "cost",
            "available",
            "in stock",
            "recommend",
            "suggest",
            "best seller",
            "featured",
            "popular",
            "what do you sell",
            "products",
            "items",
        ]

        for indicator in shopping_indicators:
            if indicator in lower_msg:
                return True

        return False

    async def _detect_product_mentions(
        self,
        response_text: str,
        merchant: Merchant,
        llm_service: BaseLLMService,
        db: AsyncSession,
    ) -> list[dict[str, Any]] | None:
        """Detect product mentions in LLM response and fetch products.

        Args:
            response_text: The LLM's response text
            merchant: Merchant configuration
            llm_service: LLM service for detection
            db: Database session

        Returns:
            List of products if mentions detected, None otherwise
        """
        try:
            from app.services.conversation.product_mention_detector import ProductMentionDetector

            detector = ProductMentionDetector(llm_service=llm_service)

            products = await detector.detect_and_fetch(
                response_text=response_text,
                merchant_id=merchant.id,
                db=db,
                max_products=3,
            )

            if products:
                logger.info(
                    "llm_handler_products_detected",
                    merchant_id=merchant.id,
                    products_count=len(products),
                )

            return products

        except Exception as e:
            logger.warning(
                "llm_handler_product_detection_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            return None

    def _generate_quick_replies(
        self, user_message: str, response_text: str, merchant: Merchant
    ) -> list[dict[str, Any]] | None:
        """Generate contextual quick replies based on conversation.

        Story 9-4: Quick Reply Buttons

        Generates appropriate quick reply options based on the
        conversation context and response content.

        Mode-aware: General mode gets general quick replies,
        e-commerce mode gets shopping quick replies.

        Args:
            user_message: The user's message
            response_text: The bot's response
            merchant: The merchant object for mode detection

        Returns:
            List of quick reply dicts, or None if not applicable
        """
        lower_msg = user_message.lower().strip()
        lower_response = response_text.lower()

        if "?" in lower_response and ("would you" in lower_response or "are you" in lower_response):
            return [
                {"id": "1", "text": "Yes", "icon": "✓"},
                {"id": "2", "text": "No", "icon": "✗"},
            ]

        if any(word in lower_msg for word in ["hello", "hi", "hey", "greet"]):
            return [
                {"id": "1", "text": "Show products", "icon": "🛍️"},
                {"id": "2", "text": "Check my cart", "icon": "🛒"},
                {"id": "3", "text": "Track my order", "icon": "📦"},
            ]

        if "product" in lower_msg or "item" in lower_msg or "search" in lower_msg:
            return [
                {"id": "1", "text": "Show more", "icon": "🔍"},
                {"id": "2", "text": "Add to cart", "icon": "🛒"},
            ]

        if "cart" in lower_msg or "checkout" in lower_msg:
            return [
                {"id": "1", "text": "Checkout", "icon": "💳"},
                {"id": "2", "text": "Continue shopping", "icon": "🛍️"},
            ]

        onboarding_mode = getattr(merchant, "onboarding_mode", "ecommerce")

        if onboarding_mode == "general":
            return [
                {"id": "1", "text": "Learn more", "icon": "📚"},
                {"id": "2", "text": "Contact us", "icon": "💬"},
                {"id": "3", "text": "Ask a question", "icon": "❓"},
            ]
        else:
            return [
                {"id": "1", "text": "Show products", "icon": "🛍️"},
                {"id": "2", "text": "Check my cart", "icon": "🛒"},
            ]

    async def _build_system_prompt(
        self,
        db: AsyncSession,
        merchant: Merchant,
        bot_name: str,
        business_name: str,
        personality_type: PersonalityType,
        pending_state: dict | None = None,
    ) -> str:
        """Build system prompt with personality and context.

        Story 5-10: Fixed positional args bug - now passes all parameters correctly.
        Includes business_hours, custom_greeting, business_description, and product context.
        Added pending_state for conversation state awareness.

        Args:
            db: Database session
            merchant: Merchant configuration
            bot_name: Bot's name
            business_name: Business name
            personality_type: Personality type
            pending_state: Optional pending state context

        Returns:
            Complete system prompt
        """
        custom_greeting = getattr(merchant, "custom_greeting", None)
        business_description = getattr(merchant, "business_description", None)
        business_hours = getattr(merchant, "business_hours", None)

        product_context = ""
        order_context = ""

        if db:
            try:
                from app.services.product_context_service import (
                    get_order_context_prompt_section,
                    get_product_context_prompt_section,
                )

                product_context = await get_product_context_prompt_section(db, merchant.id)
                order_context = await get_order_context_prompt_section(db, merchant.id)
            except Exception as e:
                logger.warning(
                    "llm_handler_context_failed",
                    merchant_id=merchant.id,
                    error=str(e),
                )

        personality_prompt = get_personality_system_prompt(
            personality_type,
            custom_greeting,
            business_name,
            business_description,
            business_hours,
            bot_name,
            product_context,
            order_context,
            pending_state,
            merchant.onboarding_mode,
        )

        return personality_prompt

    def _get_pending_state(self, context: ConversationContext) -> dict | None:
        """Extract pending state from conversation context.

        Args:
            context: Conversation context

        Returns:
            Dictionary with pending state flags, or None if no pending state
        """
        conversation_data = context.conversation_data or {}
        metadata = context.metadata or {}

        pending_state = {}

        if conversation_data.get("pending_cross_device_lookup") or metadata.get(
            "pending_cross_device_lookup"
        ):
            pending_state["pending_cross_device_lookup"] = True

        return pending_state if pending_state else None

    async def _get_conversation_context(
        self,
        db: AsyncSession,
        conversation_id: int,
    ) -> dict[str, Any] | None:
        """Retrieve conversation context memory.

        Story 11-1: Context Memory Integration
        Fetches context from Redis/PostgreSQL for LLM prompt injection.

        Args:
            db: Database session
            conversation_id: Conversation ID

        Returns:
            Context dictionary or None if not found
        """
        redis_client = get_redis_client()
        context_service = ConversationContextService(db=db, redis_client=redis_client)

        try:
            context = await context_service.get_context(conversation_id)
            return context
        except Exception as e:
            logger.warning(
                "llm_handler_context_retrieval_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            return None

    def _inject_conversation_context(
        self,
        base_prompt: str,
        context: dict[str, Any] | None,
        onboarding_mode: str,
    ) -> str:
        """Inject conversation context into system prompt.

        Story 11-1: Context Memory Integration
        Injects mode-aware context to improve response relevance.

        Args:
            base_prompt: Original system prompt
            context: Conversation context dictionary (can be None)
            onboarding_mode: Merchant mode (ecommerce or general)

        Returns:
            Enhanced system prompt with context
        """
        if not context:
            return base_prompt

        # Build context section based on mode
        if onboarding_mode == "ecommerce":
            context_section = self._build_ecommerce_context(context)
        else:  # general mode
            context_section = self._build_general_context(context)

        # Inject context before instructions
        enhanced_prompt = f"""{base_prompt}

## Conversation Context

{context_section}

When responding, take this context into account to provide more personalized and relevant assistance."""

        logger.debug(
            "llm_handler_context_injected",
            context_keys=list(context.keys()),
            onboarding_mode=onboarding_mode,
            context_length=len(context_section),
        )

        return enhanced_prompt

    def _build_ecommerce_context(self, context: dict[str, Any]) -> str:
        """Build e-commerce context section for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context section
        """
        parts = []

        # Products viewed
        if context.get("viewed_products"):
            products = context["viewed_products"][:5]  # Limit to 5 for token efficiency
            parts.append(f"Recently viewed products: {products}")

        # Constraints
        if context.get("constraints"):
            constraints = []
            if context["constraints"].get("budget_max"):
                constraints.append(f"budget max: ${context['constraints']['budget_max']}")
            if context["constraints"].get("budget_min"):
                constraints.append(f"budget min: ${context['constraints']['budget_min']}")

            # Preferences
            if context["constraints"].get("size"):
                constraints.append(f"size: {context['constraints']['size']}")
            if context["constraints"].get("color"):
                constraints.append(f"color: {context['constraints']['color']}")
            if context["constraints"].get("brand"):
                constraints.append(f"brand: {context['constraints']['brand']}")

            if constraints:
                parts.append(f"Customer constraints: {', '.join(constraints)}")

        # Cart items
        if context.get("cart_items"):
            parts.append(f"Items in cart: {context['cart_items']}")

        # Search history
        if context.get("search_history"):
            recent_searches = context["search_history"][-3:]  # Last 3 searches
            parts.append(f"Recent searches: {recent_searches}")

        return "\n".join(parts) if parts else "No specific context available."

    def _build_general_context(self, context: dict[str, Any]) -> str:
        """Build general mode context section for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context section
        """
        parts = []

        # Topics discussed
        if context.get("topics_discussed"):
            topics = context["topics_discussed"][:5]
            parts.append(f"Topics discussed: {', '.join(topics)}")

        # Support issues
        if context.get("support_issues"):
            issues = []
            for issue in context["support_issues"][:5]:
                issue_type = issue.get("type", "unknown")
                status = issue.get("status", "unknown")
                issues.append(f"{issue_type} ({status})")
            if issues:
                parts.append(f"Support issues: {', '.join(issues)}")

        # Documents referenced
        if context.get("documents_referenced"):
            parts.append(f"Documents referenced: {context['documents_referenced']}")

        # Escalation status
        if context.get("escalation_status"):
            escalation = context["escalation_status"]
            parts.append(f"Escalation level: {escalation}")

        return "\n".join(parts) if parts else "No specific context available."

    def _inject_rag_context(self, base_prompt: str, rag_context: str) -> str:
        """Inject RAG context into system prompt naturally.

        Story 8-5: RAG Integration in Conversation
        Story 10-1: Enhanced for general mode - prioritize knowledge base over shopping redirect
        Enhanced with clear instructions and examples to improve response quality.

        Args:
            base_prompt: Original system prompt
            rag_context: RAG context string with document chunks

        Returns:
            System prompt with RAG context
        """
        return f"""{base_prompt}

**Relevant Information from Knowledge Base:**
{rag_context}

**Instructions for Using This Information:**
1. Use the information above to answer questions directly and accurately
2. Do NOT mention "the document", "the provided information", "according to", or similar phrases
3. Answer naturally as if you already know this information
4. If the information doesn't fully answer the question, provide what you can and acknowledge limitations
5. Only redirect to shopping/product topics if the question is completely unrelated to BOTH shopping AND the knowledge base

**Response Examples:**
❌ BAD: "According to the document, the Subaru WRX has a 2.0L engine."
✅ GOOD: "The Subaru WRX features a 2.0L turbocharged Boxer engine that delivers impressive power."

❌ BAD: "The provided information mentions safety features."
✅ GOOD: "The WRX has earned the maximum five-star ANCAP occupant safety rating, thanks to advanced safety systems."

Remember: You're not "looking up information" - you're answering based on what you know.
"""

    def _add_no_rag_note(
        self, base_prompt: str, business_name: str, onboarding_mode: str
    ) -> str:
        """Add note when no RAG context is available.

        Story 8-5: Graceful degradation when RAG finds no results.

        Args:
            base_prompt: Original system prompt
            business_name: Name of the business
            onboarding_mode: Merchant's onboarding mode (general/ecommerce)

        Returns:
            System prompt with no-RAG note
        """
        if onboarding_mode == "general":
            note = f"""
**Note:** I don't have specific information about that in my knowledge base.
I can still try to help based on what I know about {business_name}, or you can ask about:
- Business information and services
- Policies and procedures
- General questions I might be able to answer
"""
        else:  # ecommerce mode
            note = f"""
**Note:** I don't have specific information about that in my knowledge base,
but I can help you with:
- Product searches and availability
- Shopping cart and checkout
- Order tracking and management
- {business_name} products and services
"""
        return f"{base_prompt}\n{note}"

    def build_resolution_system_prompt(
        self,
        personality_type: PersonalityType,
        business_name: str,
    ) -> str:
        """Build system prompt for handoff resolution message.

        Creates a personality-aware prompt for generating context-aware
        resolution messages when merchants resolve handoff items.

        Args:
            personality_type: Merchant's personality setting
            business_name: Name of the business to include naturally

        Returns:
            Complete system prompt for resolution message generation
        """
        base_prompt = get_personality_system_prompt(personality_type)

        resolution_context = f"""

SPECIAL CONTEXT: You are transitioning a conversation back to bot mode after a human agent from {business_name} helped resolve the customer's issue.

Your task is to generate a brief (1-3 sentences) message that:
- Smoothly acknowledges that the issue has been resolved
- Offers continued assistance from the bot
- Matches your personality tone perfectly
- Naturally mentions {business_name} if appropriate
- Does NOT repeat what the human agent said (just transition smoothly)

Examples by personality:
- Friendly: "All set! {business_name} is here for you anytime! 😊"
- Professional: "Thank you for your patience. {business_name} is available to assist you with any additional questions."
- Enthusiastic: "YAY! {business_name} has got you covered! ✨ I'm SO ready to help you find more amazing stuff! 🎉"

Generate your response now:"""

        return base_prompt + resolution_context
