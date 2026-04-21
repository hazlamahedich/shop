"""Quick Reply Suggestion Generator.

Generates contextual quick reply suggestions to guide conversation
flow and reduce user effort.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from redis import Redis

from app.models.conversation_context import ConversationContext
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class QuickReplyGenerator:
    """Generate contextual quick reply suggestions."""

    REDIS_KEY_PREFIX = "quick_replies"
    REDIS_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def generate_quick_replies(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any] | None,
        merchant_mode: str = "ecommerce",
        personality: PersonalityType = PersonalityType.FRIENDLY,
    ) -> list[str]:
        """Generate 3-5 contextual quick reply suggestions.

        Args:
            context: Conversation context
            response_metadata: Response metadata
            merchant_mode: E-commerce or general mode
            personality: Bot personality

        Returns:
            List of quick reply suggestions (max 5)
        """
        replies = []

        # Get current intent from metadata
        current_intent = response_metadata.get("intent", "unknown") if response_metadata else "unknown"

        # Generate suggestions based on current intent
        replies.extend(
            self._get_intent_based_replies(current_intent, context, personality)
        )

        # Add conversation state suggestions
        replies.extend(
            self._get_conversation_state_replies(context, personality)
        )

        # Add entity-based suggestions
        replies.extend(
            self._get_entity_based_replies(context, response_metadata, personality)
        )

        # Add merchant mode suggestions
        replies.extend(
            self._get_mode_based_replies(merchant_mode, context, personality)
        )

        # Remove duplicates and limit to 5
        unique_replies = list(dict.fromkeys(replies))
        return unique_replies[:5]

    def _get_intent_based_replies(
        self,
        intent: str,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate intent-based quick replies.

        Args:
            intent: Current intent
            context: Conversation context
            personality: Bot personality

        Returns:
            List of intent-based replies
        """
        replies = []

        intent_replies = {
            "product_search": [
                "Show me more options",
                "Filter by price",
                "Compare products",
            ],
            "product_inquiry": [
                "Show details",
                "Similar products",
                "Add to cart",
            ],
            "cart_view": [
                "Add more items",
                "Checkout now",
                "Remove items",
                "Continue shopping",
            ],
            "cart_add": [
                "View cart",
                "Checkout",
                "Continue shopping",
            ],
            "checkout": [
                "Apply discount",
                "Guest checkout",
                "Account holder checkout",
            ],
            "order_tracking": [
                "Track another order",
                "Contact support",
                "View order details",
            ],
            "greeting": [
                "Browse products",
                "Track my order",
                "Get help",
                "View recommendations",
            ],
            "general": [
                "Browse products",
                "Search catalog",
                "Get recommendations",
            ],
            "unknown": [
                "Browse products",
                "Search catalog",
                "Get help",
            ],
        }

        personality_modifications = {
            PersonalityType.FRIENDLY: {
                "Browse products": "Browse products",
                "Track my order": "Track my order",
                "Get help": "Get help",
            },
            PersonalityType.PROFESSIONAL: {
                "Browse products": "View product catalog",
                "Track my order": "Track order status",
                "Get help": "Contact support",
            },
            PersonalityType.ENTHUSIASTIC: {
                "Browse products": "Browse products!!!",
                "Track my order": "Track my order!!!",
                "Get help": "Get help here!!!",
            },
        }

        base_replies = intent_replies.get(intent, intent_replies["general"])

        # Apply personality modifications
        for i, reply in enumerate(base_replies):
            personality_maps = personality_modifications.get(personality, {})
            if reply in personality_maps:
                base_replies[i] = personality_maps[reply]

        return base_replies

    def _get_conversation_state_replies(
        self,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate conversation state quick replies.

        Args:
            context: Conversation context
            personality: Bot personality

        Returns:
            List of conversation state replies
        """
        replies = []

        turn_count = len(context.conversation_history)

        # Long conversation replies
        if turn_count > 8:
            personality_replies = {
                PersonalityType.FRIENDLY: [
                    "That's everything I needed",
                    "Summarize our conversation",
                    "Start new topic",
                ],
                PersonalityType.PROFESSIONAL: [
                    "That completes my inquiry",
                    "Provide summary",
                    "Change topic",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "That's everything!!!",
                    "Summarize please!!!",
                    "New topic!!!",
                ],
            }
            replies.extend(personality_replies.get(personality, []))

        # Short conversation replies
        elif turn_count < 3:
            replies.extend([
                "Tell me more",
                "Show recommendations",
                "Help me decide",
            ])

        return replies

    def _get_entity_based_replies(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any],
        personality: PersonalityType,
    ) -> list[str]:
        """Generate entity-based quick replies.

        Args:
            context: Conversation context
            response_metadata: Response metadata
            personality: Bot personality

        Returns:
            List of entity-based replies
        """
        replies = []

        if not response_metadata:
            return replies

        # Products mentioned in response
        if response_metadata.get("products_viewed"):
            replies.extend([
                "Add to cart",
                "See details",
                "Find similar",
            ])

        # Cart has items
        if response_metadata.get("cart_has_items"):
            replies.extend([
                "Checkout",
                "View cart",
                "Continue shopping",
            ])

        # Budget mentioned
        if context.metadata.get("budget_mentioned"):
            replies.extend([
                "Show options in my budget",
                "Adjust budget range",
                "See all options",
            ])

        # Gift mentioned
        if context.metadata.get("is_gift"):
            replies.extend([
                "Add gift wrapping",
                "See gift options",
                "Include gift message",
            ])

        return replies

    def _get_mode_based_replies(
        self,
        merchant_mode: str,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate mode-based quick replies.

        Args:
            merchant_mode: E-commerce or general mode
            context: Conversation context
            personality: Bot personality

        Returns:
            List of mode-based replies
        """
        replies = []

        if merchant_mode == "ecommerce":
            # Always available e-commerce actions
            ecom_actions = {
                PersonalityType.FRIENDLY: [
                    "Browse products",
                    "Track order",
                    "Get support",
                ],
                PersonalityType.PROFESSIONAL: [
                    "View catalog",
                    "Track order status",
                    "Contact support",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Browse products!!!",
                    "Track order!!!",
                    "Get support!!!",
                ],
            }
            replies.extend(ecom_actions.get(personality, []))

        elif merchant_mode == "general":
            # General mode actions
            general_actions = {
                PersonalityType.FRIENDLY: [
                    "Learn more",
                    "Get started",
                    "Contact support",
                ],
                PersonalityType.PROFESSIONAL: [
                    "View information",
                    "Get started",
                    "Request assistance",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Learn more!!!",
                    "Get started!!!",
                    "Contact support!!!",
                ],
            }
            replies.extend(general_actions.get(personality, []))

        return replies

    async def store_quick_reply_interaction(
        self,
        conversation_id: int,
        quick_reply: str,
        selected: bool,
    ) -> None:
        """Store quick reply interaction for analytics.

        Args:
            conversation_id: Conversation ID
            quick_reply: Quick reply text
            selected: Whether user clicked on it
        """
        if self.redis:
            try:
                interaction_key = f"{self.REDIS_KEY_PREFIX}:interaction:{conversation_id}"
                interaction_data = {
                    "quick_reply": quick_reply,
                    "selected": selected,
                    "timestamp": datetime.now().isoformat(),
                }

                # Store interaction
                current_interactions = self.redis.get(interaction_key)
                interactions = json.loads(current_interactions) if current_interactions else []
                interactions.append(interaction_data)

                self.redis.setex(
                    interaction_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(interactions[-20:]),  # Keep last 20
                )
            except Exception:
                pass