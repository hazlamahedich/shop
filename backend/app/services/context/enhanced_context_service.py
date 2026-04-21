"""Enhanced context service with multi-topic bridging and cross-references.

Story 11-2: Multi-Topic Context Awareness
Improves context awareness when switching between conversation topics.

Key improvements:
- Topic bridging phrases for smooth transitions
- Natural cross-references to prior context
- Entity tracking across topic switches
- Contextual memory with intelligent recall
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import (
    ConversationContext,
)
from app.services.context import EcommerceContextExtractor, GeneralContextExtractor

logger = structlog.get_logger(__name__)


class EnhancedContextService:
    """Enhanced context service with multi-topic awareness.

    Key features:
    - Tracks topics and enables smooth transitions
    - Generates natural bridging phrases
    - Maintains entity context across topic switches
    - Provides cross-reference suggestions
    """

    REDIS_KEY_PREFIX = "enhanced_conversation_context"
    REDIS_TTL_SECONDS = 86400  # 24 hours

    # Topic bridging phrases by personality
    TOPIC_BRIDGING_PHRASES = {
        "friendly": [
            "Picking up where we left off...",
            "Getting back to what we were talking about...",
            "So, returning to our earlier topic...",
            "Let's circle back to what you mentioned before...",
            "Right! So about the {topic} we were discussing...",
        ],
        "professional": [
            "Returning to our previous topic...",
            "Regarding our earlier discussion about {topic}...",
            "Let us revisit the subject we were addressing...",
            "Continuing from where we left off...",
        ],
        "enthusiastic": [
            "RIGHT! Let's get back to {topic}!!!",
            "YAY! So about the {topic} we were talking about!!!",
            "AWESOME! Let's circle back to {topic}!!!",
        ],
    }

    # Cross-reference templates
    CROSS_REFERENCE_TEMPLATES = {
        "budget": [
            "Still looking for options in that ${budget_min}-${budget_max} range?",
            "Keeping that ${budget_min}-${budget_max} budget in mind...",
            "Within your ${budget_min}-${budget_max} price range...",
        ],
        "product_category": [
            "You mentioned you're interested in {category}...",
            "Since you're looking for {category}...",
            "For the {category} you were interested in...",
        ],
        "gift_recipient": [
            "For the {recipient} you mentioned...",
            "Since we're shopping for {recipient}...",
            "Keeping the {recipient} in mind...",
        ],
        "preferences": [
            "Given your preference for {preference}...",
            "Since you prefer {preference}...",
            "Keeping your {preference} preference in mind...",
        ],
    }

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def get_enhanced_context(
        self,
        conversation_id: int,
        merchant_id: int,
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Get enhanced context with bridging suggestions.

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            personality: Personality type (friendly, professional, enthusiastic)

        Returns:
            Enhanced context with bridging phrases and cross-references
        """
        # Get base context from database/Redis
        base_context = await self._get_base_context(conversation_id)

        if not base_context:
            return {
                "conversation_id": conversation_id,
                "merchant_id": merchant_id,
                "personality": personality,
                "topics": [],
                "entities": {},
                "bridging_phrases": [],
                "cross_references": [],
                "last_topic": None,
                "turn_count": 0,
            }

        # Enhance with topic tracking and bridging
        enhanced = await self._enhance_context(base_context, personality)

        return enhanced

    async def update_context_with_topic_switch(
        self,
        conversation_id: int,
        merchant_id: int,
        old_topic: str,
        new_topic: str,
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Update context when topic switches.

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            old_topic: Previous topic
            new_topic: New topic
            personality: Personality type

        Returns:
            Updated context with bridging phrases
        """
        context = await self.get_enhanced_context(
            conversation_id, merchant_id, personality
        )

        # Track topic switch
        if "topic_history" not in context:
            context["topic_history"] = []

        context["topic_history"].append({
            "from": old_topic,
            "to": new_topic,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        context["last_topic"] = old_topic
        context["current_topic"] = new_topic

        # Generate bridging phrases for returning to old topic
        bridging_phrases = self._generate_bridging_phrases(
            old_topic, new_topic, personality
        )
        context["bridging_phrases"] = bridging_phrases

        # Generate cross-references based on entities
        cross_references = self._generate_cross_references(
            context.get("entities", {}), personality
        )
        context["cross_references"] = cross_references

        # Persist enhanced context
        await self._persist_enhanced_context(conversation_id, context)

        return context

    async def track_entity(
        self,
        conversation_id: int,
        merchant_id: int,
        entity_type: str,
        entity_value: Any,
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Track an entity (budget, product, preference) across topic switches.

        Args:
            conversation_id: Conversation ID
            merchant_id: Merchant ID
            entity_type: Type of entity (budget, product, preference, etc.)
            entity_value: Value of the entity
            personality: Personality type

        Returns:
            Updated context with entity tracked
        """
        context = await self.get_enhanced_context(
            conversation_id, merchant_id, personality
        )

        if "entities" not in context:
            context["entities"] = {}

        # Track entity with timestamp
        context["entities"][entity_type] = {
            "value": entity_value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "referenced_count": context["entities"].get(entity_type, {}).get("referenced_count", 0) + 1,
        }

        # Generate cross-reference for this entity
        cross_refs = self._generate_cross_references(context["entities"], personality)
        context["cross_references"] = cross_refs

        # Persist
        await self._persist_enhanced_context(conversation_id, context)

        return context

    def _generate_bridging_phrases(
        self,
        old_topic: str,
        new_topic: str,
        personality: str,
    ) -> list[str]:
        """Generate bridging phrases for topic transitions.

        Args:
            old_topic: Previous topic
            new_topic: Current topic
            personality: Personality type

        Returns:
            List of bridging phrases
        """
        templates = self.TOPIC_BRIDGING_PHRASES.get(
            personality,
            self.TOPIC_BRIDGING_PHRASES["friendly"]
        )

        bridging_phrases = []
        for template in templates:
            if "{topic}" in template:
                phrase = template.format(topic=old_topic)
                bridging_phrases.append(phrase)
            else:
                bridging_phrases.append(template)

        return bridging_phrases

    def _generate_cross_references(
        self,
        entities: dict[str, Any],
        personality: str,
    ) -> list[str]:
        """Generate natural cross-references to tracked entities.

        Args:
            entities: Tracked entities
            personality: Personality type

        Returns:
            List of cross-reference phrases
        """
        cross_references = []

        for entity_type, entity_data in entities.items():
            entity_value = entity_data.get("value")

            if not entity_value:
                continue

            # Get template for this entity type
            templates = self.CROSS_REFERENCE_TEMPLATES.get(entity_type, [])
            for template in templates:
                try:
                    if entity_type == "budget":
                        # Format budget range
                        budget_min = entity_value.get("budget_min", 0)
                        budget_max = entity_value.get("budget_max", 1000)
                        ref = template.format(
                            budget_min=budget_min,
                            budget_max=budget_max
                        )
                        cross_references.append(ref)
                    elif entity_type == "product_category":
                        ref = template.format(category=entity_value)
                        cross_references.append(ref)
                    elif entity_type == "gift_recipient":
                        ref = template.format(recipient=entity_value)
                        cross_references.append(ref)
                    elif entity_type == "preferences":
                        ref = template.format(preference=entity_value)
                        cross_references.append(ref)
                except (KeyError, ValueError):
                    continue

        return cross_references

    async def _enhance_context(
        self,
        base_context: dict[str, Any],
        personality: str,
    ) -> dict[str, Any]:
        """Enhance base context with topic tracking and bridging.

        Args:
            base_context: Base context from database
            personality: Personality type

        Returns:
            Enhanced context
        """
        enhanced = base_context.copy()
        enhanced["personality"] = personality

        # Initialize topic tracking
        if "topics" not in enhanced:
            enhanced["topics"] = []

        # Initialize entity tracking
        if "entities" not in enhanced:
            enhanced["entities"] = {}

        # Initialize bridging and cross-references
        if "bridging_phrases" not in enhanced:
            enhanced["bridging_phrases"] = []

        if "cross_references" not in enhanced:
            enhanced["cross_references"] = []

        # Extract entities from context based on mode
        mode = enhanced.get("mode", "ecommerce")

        if mode == "ecommerce":
            # Track budget constraints
            constraints = enhanced.get("constraints", {})
            if constraints:
                enhanced["entities"]["budget"] = {
                    "value": constraints,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "referenced_count": 1,
                }

            # Track product categories
            search_history = enhanced.get("search_history", [])
            if search_history:
                enhanced["entities"]["product_category"] = {
                    "value": search_history[-1],  # Most recent search
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "referenced_count": 1,
                }

        return enhanced

    async def _get_base_context(
        self,
        conversation_id: int,
    ) -> dict[str, Any] | None:
        """Get base context from Redis or database.

        Args:
            conversation_id: Conversation ID

        Returns:
            Base context or None
        """
        # Try Redis first
        if self.redis:
            try:
                context_json = self.redis.get(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}"
                )
                if context_json:
                    return json.loads(context_json)
            except Exception as e:
                self.logger.warning(
                    "Redis get failed",
                    error=str(e),
                    conversation_id=conversation_id,
                )

        # Fall back to database
        result = await self.db.execute(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        context_model = result.scalar_one_or_none()

        if context_model:
            return self._model_to_dict(context_model)

        return None

    async def _persist_enhanced_context(
        self,
        conversation_id: int,
        context: dict[str, Any],
    ) -> None:
        """Persist enhanced context to Redis and database.

        Args:
            conversation_id: Conversation ID
            context: Enhanced context to persist
        """
        # Save to Redis
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(context),
                )
            except Exception as e:
                self.logger.warning(
                    "Redis set failed",
                    error=str(e),
                    conversation_id=conversation_id,
                )

    def _model_to_dict(self, model: ConversationContext) -> dict[str, Any]:
        """Convert context model to dictionary.

        Args:
            model: ConversationContext model

        Returns:
            Dictionary representation
        """
        return {
            "mode": model.mode,
            "turn_count": model.turn_count,
            "viewed_products": model.viewed_products,
            "cart_items": model.cart_items,
            "constraints": model.constraints,
            "search_history": model.search_history,
            "topics_discussed": model.topics_discussed,
            "documents_referenced": model.documents_referenced,
            "support_issues": model.support_issues,
            "escalation_status": model.escalation_status,
            "preferences": model.preferences,
        }
