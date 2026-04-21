"""Conversation Goal Tracking System.

Tracks conversation objectives and provides proactive assistance
to help users complete their goals.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import ConversationContext, ConversationTurn
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class ConversationGoal(str, Enum):
    """Types of conversation goals."""
    PRODUCT_SEARCH = "product_search"
    PURCHASE_ASSISTANCE = "purchase_assistance"
    SUPPORT = "support"
    INFORMATION = "information"
    COMPARISON = "comparison"
    CART_MANAGEMENT = "cart_management"
    ORDER_TRACKING = "order_tracking"


class ConversationGoalTracker:
    """Track and manage conversation goals."""

    REDIS_KEY_PREFIX = "conversation_goals"
    REDIS_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def track_goal_progress(
        self,
        conversation_id: int,
        current_intent: str,
        entities: dict[str, Any] | None,
        context: ConversationContext,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Track progress toward conversation goal.

        Args:
            conversation_id: Conversation ID
            current_intent: Current classified intent
            entities: Extracted entities
            context: Conversation context
            db: Database session

        Returns:
            Goal tracking information with suggestions
        """
        # Infer goal from intent and context
        goal = await self._infer_conversation_goal(current_intent, entities, context)

        # Calculate progress
        progress = await self._calculate_progress(goal, context, db)

        # Generate suggestions based on progress
        if progress >= 80:
            suggestions = await self._generate_completion_suggestions(goal, context)
        else:
            suggestions = await self._generate_next_steps(goal, progress, context)

        # Get next milestone
        next_milestone = self._get_next_milestone(goal, progress)

        # Track goal state
        goal_state = {
            "goal": goal.value,
            "progress": progress,
            "suggestions": suggestions,
            "next_milestone": next_milestone,
            "current_intent": current_intent,
            "turn_count": len(context.conversation_history),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Store goal state
        await self._store_goal_state(conversation_id, goal_state)

        return goal_state

    async def _infer_conversation_goal(
        self,
        intent: str,
        entities: dict[str, Any] | None,
        context: ConversationContext,
    ) -> ConversationGoal:
        """Infer conversation goal from intent and context.

        Args:
            intent: Current intent
            entities: Extracted entities
            context: Conversation context

        Returns:
            Inferred conversation goal
        """
        # Direct intent to goal mapping
        intent_to_goal = {
            "product_search": ConversationGoal.PRODUCT_SEARCH,
            "product_inquiry": ConversationGoal.PRODUCT_SEARCH,
            "product_comparison": ConversationGoal.COMPARISON,
            "cart_add": ConversationGoal.PURCHASE_ASSISTANCE,
            "cart_view": ConversationGoal.CART_MANAGEMENT,
            "checkout": ConversationGoal.PURCHASE_ASSISTANCE,
            "order_tracking": ConversationGoal.ORDER_TRACKING,
            "human_handoff": ConversationGoal.SUPPORT,
        }

        # Check direct mapping first
        if intent in intent_to_goal:
            return intent_to_goal[intent]

        # Analyze conversation history for goal inference
        if len(context.conversation_history) > 3:
            recent_intents = [
                turn.metadata.get("intent", "unknown")
                for turn in context.conversation_history[-3:]
            ]

            # Detect product research pattern
            if any(intent in ["product_search", "product_inquiry", "product_comparison"] for intent in recent_intents):
                return ConversationGoal.PRODUCT_SEARCH

            # Detect purchase pattern
            if any(intent in ["cart_add", "checkout", "cart_view"] for intent in recent_intents):
                return ConversationGoal.PURCHASE_ASSISTANCE

            # Detect support pattern
            if "frustrated" in str(context.conversation_history).lower() or "problem" in str(context.conversation_history).lower():
                return ConversationGoal.SUPPORT

        # Default based on merchant mode
        merchant_mode = getattr(context, "merchant_mode", "ecommerce")
        if merchant_mode == "ecommerce":
            return ConversationGoal.PRODUCT_SEARCH

        return ConversationGoal.INFORMATION

    async def _calculate_progress(
        self,
        goal: ConversationGoal,
        context: ConversationContext,
        db: AsyncSession,
    ) -> float:
        """Calculate progress toward conversation goal.

        Args:
            goal: Conversation goal
            context: Conversation context
            db: Database session

        Returns:
            Progress percentage (0-100)
        """
        progress = 0.0

        # Progress indicators for different goals
        if goal == ConversationGoal.PRODUCT_SEARCH:
            # Have we found products?
            if context.metadata.get("products_viewed"):
                progress += 30

            # Has user shown interest in specific products?
            if len(context.conversation_history) > 2:
                progress += 20

            # Have we narrowed down options?
            if context.metadata.get("narrowed_down"):
                progress += 30

            # Have we provided recommendations?
            if context.metadata.get("recommendations_provided"):
                progress += 20

        elif goal == ConversationGoal.PURCHASE_ASSISTANCE:
            # Has user viewed products?
            if context.metadata.get("products_viewed"):
                progress += 25

            # Has user added to cart?
            if context.metadata.get("cart_added"):
                progress += 40

            # Has user initiated checkout?
            if context.metadata.get("checkout_initiated"):
                progress += 35

        elif goal == ConversationGoal.COMPARISON:
            # Have we found multiple products?
            products = context.metadata.get("products_viewed", [])
            if len(products) >= 2:
                progress += 40

            # Have we provided comparison?
            if context.metadata.get("comparison_provided"):
                progress += 60

        elif goal == ConversationGoal.SUPPORT:
            # Have we identified the issue?
            if context.metadata.get("issue_identified"):
                progress += 30

            # Have we provided solution?
            if context.metadata.get("solution_provided"):
                progress += 40

            # Is user satisfied?
            if context.metadata.get("user_satisfied"):
                progress += 30

        elif goal == ConversationGoal.ORDER_TRACKING:
            # Have we found the order?
            if context.metadata.get("order_found"):
                progress += 50

            # Have we provided status?
            if context.metadata.get("status_provided"):
                progress += 50

        # Base progress from conversation depth
        if progress == 0 and len(context.conversation_history) > 0:
            progress = min(len(context.conversation_history) * 10, 30)

        return min(progress, 100.0)

    async def _generate_completion_suggestions(
        self,
        goal: ConversationGoal,
        context: ConversationContext,
    ) -> list[str]:
        """Generate suggestions for goal completion.

        Args:
            goal: Conversation goal
            context: Conversation context

        Returns:
            List of completion suggestions
        """
        suggestions = []

        if goal == ConversationGoal.PRODUCT_SEARCH:
            if not context.metadata.get("cart_added"):
                suggestions.append("Would you like to add any of these to your cart?")
                suggestions.append("Need help deciding between options?")
            else:
                suggestions.append("Ready to checkout?")
                suggestions.append("Want me to help you compare these further?")

        elif goal == ConversationGoal.PURCHASE_ASSISTANCE:
            suggestions.append("Ready to complete your purchase?")
            suggestions.append("Need help with checkout?")
            suggestions.append("Have questions before buying?")

        elif goal == ConversationGoal.COMPARISON:
            suggestions.append("Would you like a detailed comparison?")
            suggestions.append("Should I highlight the key differences?")
            suggestions.append("Ready to make a decision?")

        elif goal == ConversationGoal.SUPPORT:
            suggestions.append("Did this resolve your issue?")
            suggestions.append("Is there anything else I can help with?")
            suggestions.append("Want me to follow up on this?")

        return suggestions[:3]

    async def _generate_next_steps(
        self,
        goal: ConversationGoal,
        progress: float,
        context: ConversationContext,
    ) -> list[str]:
        """Generate next step suggestions.

        Args:
            goal: Conversation goal
            progress: Current progress
            context: Conversation context

        Returns:
            List of next step suggestions
        """
        suggestions = []

        if goal == ConversationGoal.PRODUCT_SEARCH:
            if progress < 30:
                suggestions.append("Let me know your price range")
                suggestions.append("What features are you looking for?")
            elif progress < 60:
                suggestions.append("Want to see more options?")
                suggestions.append("Should I filter these results?")
            else:
                suggestions.append("Need help narrowing down?")

        elif goal == ConversationGoal.PURCHASE_ASSISTANCE:
            if progress < 30:
                suggestions.append("Would you like to see product details?")
            elif progress < 60:
                suggestions.append("Ready to add to cart?")
                suggestions.append("Need help with sizing?")
            else:
                suggestions.append("Proceed to checkout?")

        elif goal == ConversationGoal.COMPARISON:
            suggestions.append("Which products would you like to compare?")
            suggestions.append("What features matter most to you?")

        elif goal == ConversationGoal.SUPPORT:
            suggestions.append("Can you describe the issue in more detail?")
            suggestions.append("What were you trying to do when this happened?")

        return suggestions[:3]

    def _get_next_milestone(
        self,
        goal: ConversationGoal,
        progress: float,
    ) -> str:
        """Get next milestone for goal.

        Args:
            goal: Conversation goal
            progress: Current progress

        Returns:
            Next milestone description
        """
        milestones = {
            ConversationGoal.PRODUCT_SEARCH: [
                (0, "Start product search"),
                (30, "Find relevant products"),
                (60, "Narrow down options"),
                (90, "Make final selection"),
            ],
            ConversationGoal.PURCHASE_ASSISTANCE: [
                (0, "Start shopping"),
                (25, "View products"),
                (50, "Add to cart"),
                (75, "Initiate checkout"),
                (100, "Complete purchase"),
            ],
            ConversationGoal.COMPARISON: [
                (0, "Start comparison"),
                (40, "Find products to compare"),
                (70, "Analyze differences"),
                (100, "Make decision"),
            ],
            ConversationGoal.SUPPORT: [
                (0, "Identify issue"),
                (30, "Provide solution"),
                (70, "Verify resolution"),
                (100, "Confirm satisfaction"),
            ],
        }

        goal_milestones = milestones.get(goal, [])

        for milestone_progress, milestone_desc in goal_milestones:
            if progress < milestone_progress:
                return f"Next: {milestone_desc}"

        return "Goal nearly complete!"

    async def _store_goal_state(
        self,
        conversation_id: int,
        goal_state: dict[str, Any],
    ) -> None:
        """Store goal state in Redis.

        Args:
            conversation_id: Conversation ID
            goal_state: Goal state to store
        """
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(goal_state),
                )
            except Exception:
                pass