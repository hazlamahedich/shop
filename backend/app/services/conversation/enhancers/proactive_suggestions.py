"""Proactive Suggestion Engine.

Generates proactive suggestions based on conversation context,
user behavior, and conversation state to improve engagement.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis

from app.models.conversation_context import ConversationContext
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class ProactiveSuggestionEngine:
    """Generate proactive suggestions based on context."""

    REDIS_KEY_PREFIX = "proactive_suggestions"
    REDIS_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def generate_suggestions(
        self,
        context: ConversationContext,
        current_intent: str,
        merchant_mode: str = "ecommerce",
        personality: PersonalityType = PersonalityType.FRIENDLY,
    ) -> list[str]:
        """Generate proactive suggestions.

        Args:
            context: Conversation context
            current_intent: Current classified intent
            merchant_mode: E-commerce or general mode
            personality: Bot personality

        Returns:
            List of proactive suggestions (max 5)
        """
        suggestions = []

        # Generate suggestions based on various triggers
        suggestions.extend(
            await self._get_conversation_state_suggestions(context, personality)
        )

        suggestions.extend(
            await self._get_intent_based_suggestions(current_intent, context, personality)
        )

        suggestions.extend(
            await self._get_entity_based_suggestions(context, personality)
        )

        suggestions.extend(
            await self._get_behavioral_suggestions(context, merchant_mode, personality)
        )

        suggestions.extend(
            await self._get_timing_based_suggestions(context, personality)
        )

        # Remove duplicates and limit
        unique_suggestions = list(dict.fromkeys(suggestions))
        return unique_suggestions[:5]

    async def _get_conversation_state_suggestions(
        self,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate suggestions based on conversation state.

        Args:
            context: Conversation context
            personality: Bot personality

        Returns:
            List of conversation state suggestions
        """
        suggestions = []

        turn_count = len(context.conversation_history)

        # Long conversation suggestions
        if turn_count > 8:
            personality_phrases = {
                PersonalityType.FRIENDLY: [
                    "Would you like me to summarize what we've discussed?",
                    "That's a lot of information! Want to take a break?",
                ],
                PersonalityType.PROFESSIONAL: [
                    "Would you like a summary of our discussion?",
                    "Shall I consolidate the key points?",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Want me to summarize everything we've talked about?!",
                    "That's a lot!!! Need a quick recap?!",
                ],
            }
            suggestions.extend(personality_phrases.get(personality, []))

        # Short conversation suggestions
        elif turn_count < 3:
            if turn_count == 1:
                personality_phrases = {
                    PersonalityType.FRIENDLY: [
                        "How can I help you today?",
                        "What are you looking for?",
                    ],
                    PersonalityType.PROFESSIONAL: [
                        "How may I assist you?",
                        "What can I help you find?",
                    ],
                    PersonalityType.ENTHUSIASTIC: [
                        "What can I help you find today?!",
                        "What are you looking for?!",
                    ],
                }
                suggestions.extend(personality_phrases.get(personality, []))

        # No recent activity
        if turn_count > 0:
            last_turn = context.conversation_history[-1]
            time_since_last = (datetime.now(timezone.utc) - last_turn.timestamp).total_seconds()

            if time_since_last > 300:  # 5 minutes
                suggestions.append("Still there? I'm here to help!")

        return suggestions

    async def _get_intent_based_suggestions(
        self,
        intent: str,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate suggestions based on current intent.

        Args:
            intent: Current intent
            context: Conversation context
            personality: Bot personality

        Returns:
            List of intent-based suggestions
        """
        suggestions = []

        # Product search intents
        if intent in ["product_search", "product_inquiry"]:
            personality_phrases = {
                PersonalityType.FRIENDLY: [
                    "Need help narrowing down your options?",
                    "Want to see more details about any of these?",
                    "Should I filter by price or features?",
                ],
                PersonalityType.PROFESSIONAL: [
                    "Would you like me to narrow these results?",
                    "Shall I provide more detailed information?",
                    "Would you prefer to filter by specific criteria?",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Want help narrowing down your options?!",
                    "Should I show you more details?!",
                    "Want to filter these results?!",
                ],
            }
            suggestions.extend(personality_phrases.get(personality, []))

        # Cart-related intents
        elif intent in ["cart_view", "cart_add", "cart_remove"]:
            suggestions.extend([
                "Ready to checkout?",
                "Need help with your cart?",
                "Want to see similar products?",
            ])

        # Order tracking
        elif intent == "order_tracking":
            suggestions.extend([
                "Need help with a different issue?",
                "Have questions about your order?",
            ])

        # Greeting intent
        elif intent == "greeting":
            suggestions.extend([
                "Browse products",
                "Track my order",
                "Get help",
            ])

        return suggestions

    async def _get_entity_based_suggestions(
        self,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate suggestions based on detected entities.

        Args:
            context: Conversation context
            personality: Bot personality

        Returns:
            List of entity-based suggestions
        """
        suggestions = []

        # Products viewed
        products_viewed = context.metadata.get("products_viewed", [])
        if products_viewed:
            suggestions.append("Would you like to see similar products?")
            suggestions.append("Want me to compare these items?")
            suggestions.append("Need more details about any of these?")

        # Cart has items
        if context.metadata.get("cart_has_items"):
            suggestions.append("Ready to complete your purchase?")
            suggestions.append("Need help with checkout?")

        # Budget mentioned
        if context.metadata.get("budget_mentioned"):
            suggestions.append("Want to see options within your budget?")
            suggestions.append("Need help with price comparisons?")

        # Gift mentioned
        if context.metadata.get("is_gift"):
            suggestions.append("Need gift wrapping options?")
            suggestions.append("Want to see gift card options?")

        return suggestions

    async def _get_behavioral_suggestions(
        self,
        context: ConversationContext,
        merchant_mode: str,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate suggestions based on user behavior patterns.

        Args:
            context: Conversation context
            merchant_mode: E-commerce or general mode
            personality: Bot personality

        Returns:
            List of behavioral suggestions
        """
        suggestions = []

        # Abandoned cart detection
        if self._is_abandoned_cart(context):
            personality_phrases = {
                PersonalityType.FRIENDLY: [
                    "Would you like to complete your purchase?",
                    "Still interested in these items?",
                ],
                PersonalityType.PROFESSIONAL: [
                    "Would you like to proceed with your order?",
                    "Are you ready to complete your purchase?",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Ready to complete your purchase?!",
                    "Don't miss out on these items!!!",
                ],
            }
            suggestions.extend(personality_phrases.get(personality, []))

        # Browsing behavior
        if len(context.conversation_history) > 5:
            # User has been browsing a while
            suggestions.append("Need help finding what you're looking for?")
            suggestions.append("Want me to recommend something?")

        # Hesitation patterns
        if self._shows_hesitation(context):
            suggestions.append("Take your time! Let me know if you have questions.")
            suggestions.append("Need more information to decide?")

        return suggestions

    async def _get_timing_based_suggestions(
        self,
        context: ConversationContext,
        personality: PersonalityType,
    ) -> list[str]:
        """Generate suggestions based on timing patterns.

        Args:
            context: Conversation context
            personality: Bot personality

        Returns:
            List of timing-based suggestions
        """
        suggestions = []

        # Check if user is returning
        if self._is_returning_user(context):
            personality_phrases = {
                PersonalityType.FRIENDLY: [
                    "Welcome back! Would you like to continue where we left off?",
                    "Good to see you again! Need help with anything?",
                ],
                PersonalityType.PROFESSIONAL: [
                    "Welcome back. Would you like to continue?",
                    "Good to see you return. How may I assist you?",
                ],
                PersonalityType.ENTHUSIASTIC: [
                    "Welcome back!!! Ready to continue shopping?!",
                    "Good to see you again!!! What can I help you find?!",
                ],
            }
            suggestions.extend(personality_phrases.get(personality, []))

        # Time-based suggestions
        current_hour = datetime.now(timezone.utc).hour
        if current_hour >= 22 or current_hour <= 6:  # Late night
            suggestions.append("Taking your time shopping tonight?")
            suggestions.append("Need help with anything specific?")

        return suggestions

    def _is_abandoned_cart(self, context: ConversationContext) -> bool:
        """Check if user has abandoned cart.

        Args:
            context: Conversation context

        Returns:
            True if cart appears abandoned
        """
        # Check if cart has items but no recent activity
        if not context.metadata.get("cart_has_items"):
            return False

        # Check if conversation has stopped
        if len(context.conversation_history) > 0:
            last_turn = context.conversation_history[-1]
            time_since_last = (datetime.now(timezone.utc) - last_turn.timestamp).total_seconds()

            # If cart has items but no activity for 2+ minutes
            if time_since_last > 120:
                return True

        return False

    def _shows_hesitation(self, context: ConversationContext) -> bool:
        """Check if user shows hesitation patterns.

        Args:
            context: Conversation context

        Returns:
            True if user shows hesitation
        """
        if len(context.conversation_history) < 3:
            return False

        # Look for repeated questions or similar queries
        recent_messages = [
            turn.user_message.lower()
            for turn in context.conversation_history[-3:]
        ]

        # Check for repetitive patterns
        if len(recent_messages) == len(set(recent_messages)):
            return True

        # Check for uncertainty indicators
        uncertainty_words = ["maybe", "not sure", "think", "might", "probably"]
        for message in recent_messages:
            if any(word in message for word in uncertainty_words):
                return True

        return False

    def _is_returning_user(self, context: ConversationContext) -> bool:
        """Check if user is returning.

        Args:
            context: Conversation context

        Returns:
            True if user appears to be returning
        """
        # Check if conversation history exists and is substantial
        if len(context.conversation_history) > 10:
            return True

        # Check metadata for returning user flag
        if context.metadata.get("returning_user"):
            return True

        return False