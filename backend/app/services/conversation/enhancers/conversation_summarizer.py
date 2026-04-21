"""Conversation Summarization System.

Summarizes long conversations to maintain context while reducing
token usage and improving long-conversation quality.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import ConversationTurn

logger = structlog.get_logger(__name__)


class ConversationSummarizer:
    """Summarize long conversations for context preservation."""

    REDIS_KEY_PREFIX = "conversation_summaries"
    REDIS_TTL_SECONDS = 86400  # 24 hours
    SUMMARY_TRIGGER_TURNS = 10  # Summarize every 10 turns

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def should_summarize(
        self,
        turn_count: int,
        conversation_id: int,
        db: AsyncSession,
    ) -> bool:
        """Check if conversation should be summarized.

        Args:
            turn_count: Current conversation turn count
            conversation_id: Conversation ID
            db: Database session

        Returns:
            True if summarization is recommended
        """
        # Trigger at 10+ turns
        if turn_count < self.SUMMARY_TRIGGER_TURNS:
            return False

        # Check if we recently summarized
        if self.redis:
            try:
                last_summary_key = f"{self.REDIS_KEY_PREFIX}:last:{conversation_id}"
                last_summary = self.redis.get(last_summary_key)

                if last_summary:
                    last_summary_data = json.loads(last_summary)
                    last_summary_turn = last_summary_data.get("turn_number", 0)

                    # Only summarize if we've made progress since last summary
                    return turn_count - last_summary_turn >= self.SUMMARY_TRIGGER_TURNS
            except Exception:
                pass

        return True

    async def summarize_conversation(
        self,
        conversation_id: int,
        turn_count: int,
        db: AsyncSession,
        personality: str = "friendly",
    ) -> dict[str, Any]:
        """Summarize conversation when it gets too long.

        Args:
            conversation_id: Conversation ID
            turn_count: Current turn count
            db: Database session
            personality: Bot personality

        Returns:
            Summary with key points and continuation prompt
        """
        # Get conversation history
        history = await self._get_conversation_history(conversation_id, db)

        # Generate summary
        summary = await self._generate_summary(history, personality)

        # Extract key entities and decisions
        key_points = await self._extract_key_points(history)

        # Generate continuation prompt
        continuation_prompt = self._generate_continuation_prompt(key_points, personality)

        # Store summary for future context
        summary_data = {
            "conversation_id": conversation_id,
            "turn_number": turn_count,
            "summary": summary,
            "key_points": key_points,
            "continuation_prompt": continuation_prompt,
            "turns_summarized": turn_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "personality": personality,
        }

        await self._store_summary(conversation_id, summary_data)

        return summary_data

    async def _get_conversation_history(
        self,
        conversation_id: int,
        db: AsyncSession,
    ) -> list[ConversationTurn]:
        """Get conversation history from database.

        Args:
            conversation_id: Conversation ID
            db: Database session

        Returns:
            List of conversation turns
        """
        # Implementation would query database for conversation history
        # For now, return empty list as placeholder
        return []

    async def _generate_summary(
        self,
        history: list[ConversationTurn],
        personality: str,
    ) -> str:
        """Generate conversation summary.

        Args:
            history: Conversation history
            personality: Bot personality

        Returns:
            Generated summary
        """
        if not history:
            return "No conversation history to summarize."

        # Extract key information
        user_topics = []
        bot_actions = []

        for turn in history:
            if turn.user_message:
                user_topics.append(turn.user_message[:100])  # Truncate long messages
            if turn.bot_message:
                bot_actions.append(turn.bot_message[:100])

        # Generate personality-appropriate summary
        personality_templates = {
            "friendly": f"We've had {len(history)} exchanges. You asked about {', '.join(user_topics[:3])}. I helped you with various requests.",
            "professional": f"In our conversation of {len(history)} exchanges, we discussed {', '.join(user_topics[:3])}. I provided assistance on multiple topics.",
            "enthusiastic": f"We've had {len(history)} exchanges!!! You were interested in {', '.join(user_topics[:3])}!!! I helped you with lots of things!!!",
        }

        return personality_templates.get(
            personality, personality_templates["friendly"]
        )

    async def _extract_key_points(
        self,
        history: list[ConversationTurn],
    ) -> list[str]:
        """Extract key points from conversation.

        Args:
            history: Conversation history

        Returns:
            List of key points
        """
        key_points = []

        # Extract products mentioned
        for turn in history:
            if turn.user_message:
                # Simple product mention detection
                import re
                products = re.findall(r'(?:necklace|ring|earring|bracelet|pendant)', turn.user_message, re.IGNORECASE)
                key_points.extend(products[:3])

        # Extract price ranges
        for turn in history:
            if turn.user_message:
                prices = re.findall(r'\$(\d+)', turn.user_message)
                if prices:
                    key_points.append(f"Budget mentioned: ${min(prices)}-${max(prices)}")
                    break

        # Extract preferences
        for turn in history:
            if turn.user_message:
                if "gift" in turn.user_message.lower():
                    key_points.append("Shopping for gift")
                    break

        return key_points[:5]  # Max 5 key points

    def _generate_continuation_prompt(
        self,
        key_points: list[str],
        personality: str,
    ) -> str:
        """Generate continuation prompt for summary.

        Args:
            key_points: Key points from conversation
            personality: Bot personality

        Returns:
            Continuation prompt
        """
        if not key_points:
            return "How can I help you?"

        personality_prompts = {
            "friendly": f"To continue, we were discussing: {', '.join(key_points)}. What would you like to do next?",
            "professional": f"To continue our discussion regarding {', '.join(key_points)}, what would you like to do next?",
            "enthusiastic": f"Let's keep going with {', '.join(key_points)}!!! What's next?!",
        }

        return personality_prompts.get(
            personality, personality_prompts["friendly"]
        )

    async def _store_summary(
        self,
        conversation_id: int,
        summary_data: dict[str, Any],
    ) -> None:
        """Store summary in Redis.

        Args:
            conversation_id: Conversation ID
            summary_data: Summary data to store
        """
        if self.redis:
            try:
                # Store summary
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(summary_data),
                )

                # Store last summary metadata
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:last:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps({
                        "turn_number": summary_data["turn_number"],
                        "timestamp": summary_data["timestamp"],
                    }),
                )
            except Exception:
                pass

    async def get_summary(
        self,
        conversation_id: int,
    ) -> dict[str, Any] | None:
        """Get stored summary for conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            Summary data if exists, None otherwise
        """
        if not self.redis:
            return None

        try:
            summary_data = self.redis.get(f"{self.REDIS_KEY_PREFIX}:{conversation_id}")
            if summary_data:
                return json.loads(summary_data)
        except Exception:
            pass

        return None