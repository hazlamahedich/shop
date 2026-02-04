"""Redis-based conversation context management.

Stores classification history, extracted entities, and conversation state
for 24-hour session persistence.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any, Optional

import redis
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)


class ConversationContextManager:
    """Manages conversation context in Redis sessions.

    Stores classification history, extracted entities, and conversation state
    for 24-hour session persistence (Story 2.7 dependency).
    """

    SESSION_TTL_SECONDS: int = 24 * 60 * 60  # 24 hours

    def __init__(self, redis_client: Optional[redis.Redis] | None = None) -> None:
        """Initialize context manager.

        Args:
            redis_client: Redis client (uses default from settings if not provided)
        """
        self.redis = redis_client
        if not self.redis:
            redis_url = settings()["REDIS_URL"]
            self.redis = redis.from_url(redis_url, decode_responses=True)
        self.logger = structlog.get_logger(__name__)

    def _get_session_key(self, psid: str) -> str:
        """Generate Redis key for conversation session.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Redis session key
        """
        return f"conversation:{psid}"

    async def get_context(self, psid: str) -> dict[str, Any]:
        """Get conversation context from Redis.

        Args:
            psid: Facebook Page-Scoped ID

        Returns:
            Conversation context dict
        """
        session_key = self._get_session_key(psid)

        try:
            data = self.redis.get(session_key)
            if data:
                context = json.loads(data)
                self.logger.debug("conversation_context_retrieved", psid=psid)
                return context
            else:
                # Initialize new context
                return {
                    "psid": psid,
                    "created_at": None,  # Will be set on first message
                    "last_message_at": None,
                    "message_count": 0,
                    "previous_intents": [],
                    "extracted_entities": {},
                    "conversation_state": "active",
                }
        except Exception as e:
            self.logger.error("context_retrieval_failed", psid=psid, error=str(e))
            # Return empty context on error
            return {"psid": psid, "conversation_state": "error"}

    async def update_classification(
        self,
        psid: str,
        classification: dict[str, Any],
    ) -> None:
        """Update conversation context with new classification.

        Args:
            psid: Facebook Page-Scoped ID
            classification: Classification result dict
        """
        context = await self.get_context(psid)
        session_key = self._get_session_key(psid)

        try:
            # Update context with classification
            if "previous_intents" not in context:
                context["previous_intents"] = []
            context["previous_intents"].append(classification.get("intent", "unknown"))

            # Merge extracted entities
            if "extracted_entities" not in context:
                context["extracted_entities"] = {}

            entities = classification.get("entities", {})
            for key, value in entities.items():
                if value is not None:
                    context["extracted_entities"][key] = value

            context["last_message_at"] = classification.get("raw_message", "")
            context["message_count"] = context.get("message_count", 0) + 1

            # Set created_at on first message
            if not context.get("created_at"):
                context["created_at"] = datetime.now(UTC).isoformat()

            # Save to Redis with TTL
            self.redis.setex(
                session_key,
                self.SESSION_TTL_SECONDS,
                json.dumps(context),
            )

            self.logger.debug("conversation_context_updated", psid=psid)

        except Exception as e:
            self.logger.error("context_update_failed", psid=psid, error=str(e))

    async def delete_context(self, psid: str) -> None:
        """Delete conversation context (for GDPR compliance).

        Args:
            psid: Facebook Page-Scoped ID
        """
        session_key = self._get_session_key(psid)

        try:
            self.redis.delete(session_key)
            self.logger.info("conversation_context_deleted", psid=psid)
        except Exception as e:
            self.logger.error("context_deletion_failed", psid=psid, error=str(e))

    async def update_search_results(
        self,
        psid: str,
        search_result: dict[str, Any],
    ) -> None:
        """Update conversation context with product search results.

        Args:
            psid: Facebook Page-Scoped ID
            search_result: Search results dict with products and metadata
        """
        context = await self.get_context(psid)
        session_key = self._get_session_key(psid)

        try:
            # Store search results in context
            context["last_search_results"] = search_result

            # Update timestamp
            context["last_message_at"] = datetime.now(UTC).isoformat()

            # Save to Redis with TTL
            self.redis.setex(
                session_key,
                self.SESSION_TTL_SECONDS,
                json.dumps(context),
            )

            self.logger.debug("search_results_stored", psid=psid, result_count=len(search_result.get("products", [])))

        except Exception as e:
            self.logger.error("search_results_update_failed", psid=psid, error=str(e))
