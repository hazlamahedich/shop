"""Response Variety Enhancement System.

Ensures responses remain varied and natural to reduce
repetitiveness and maintain engagement.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis

from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class ResponseVarietyEnhancer:
    """Ensure response variety and naturalness."""

    REDIS_KEY_PREFIX = "response_variety"
    REDIS_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.response_history = {}  # Track recent responses
        self.logger = structlog.get_logger(__name__)

    async def enhance_variety(
        self,
        base_response: str,
        conversation_id: int,
        personality: PersonalityType,
    ) -> str:
        """Add variety to responses.

        Args:
            base_response: Original response
            conversation_id: Conversation ID
            personality: Bot personality

        Returns:
            Enhanced response with variety
        """
        # Get recent responses for this conversation
        recent_responses = await self._get_recent_responses(conversation_id)

        # Check for repetition
        if await self._is_similar_to_recent(base_response, recent_responses):
            # Generate alternative phrasing
            alternatives = await self._generate_alternatives(
                base_response, personality, recent_responses
            )
            if alternatives:
                base_response = alternatives[0]

        # Add natural variation
        base_response = await self._add_natural_variation(base_response, personality)

        # Track response
        await self._track_response(conversation_id, base_response)

        return base_response

    async def _get_recent_responses(
        self,
        conversation_id: int,
    ) -> list[str]:
        """Get recent responses for conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of recent responses
        """
        # Check in-memory cache first
        if conversation_id in self.response_history:
            return self.response_history[conversation_id][-5:]

        # Check Redis cache
        if self.redis:
            try:
                cached_history = self.redis.get(
                    f"{self.REDIS_KEY_PREFIX}:history:{conversation_id}"
                )
                if cached_history:
                    history = json.loads(cached_history)
                    self.response_history[conversation_id] = history
                    return history[-5:]
            except Exception:
                pass

        return []

    async def _is_similar_to_recent(
        self,
        response: str,
        recent_responses: list[str],
    ) -> bool:
        """Check if response is similar to recent responses.

        Args:
            response: Response to check
            recent_responses: Recent responses

        Returns:
            True if response is similar to recent responses
        """
        if not recent_responses:
            return False

        response_lower = response.lower()

        for recent_response in recent_responses:
            recent_lower = recent_response.lower()

            # Check for high similarity (>80%)
            similarity = self._calculate_similarity(response_lower, recent_lower)

            if similarity > 0.8:
                return True

        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    async def _generate_alternatives(
        self,
        base_response: str,
        personality: PersonalityType,
        recent_responses: list[str],
    ) -> list[str]:
        """Generate alternative phrasings for response.

        Args:
            base_response: Original response
            personality: Bot personality
            recent_responses: Recent responses to avoid

        Returns:
            List of alternative responses
        """
        alternatives = []

        # Personality-specific alternatives
        alternatives_map = {
            PersonalityType.FRIENDLY: [
                self._add_friendly_variation(base_response),
                self._add_casual_variation(base_response),
                self._add_enthusiastic_variation(base_response, False),
            ],
            PersonalityType.PROFESSIONAL: [
                self._add_formal_variation(base_response),
                self._add_casual_variation(base_response),
                self._add_concise_variation(base_response),
            ],
            PersonalityType.ENTHUSIASTIC: [
                self._add_enthusiastic_variation(base_response, True),
                self._add_friendly_variation(base_response),
                self._add_casual_variation(base_response),
            ],
        }

        personality_alternatives = alternatives_map.get(personality, [])

        # Filter out alternatives that are too similar to recent responses
        for alt in personality_alternatives:
            is_similar = False
            for recent in recent_responses:
                if self._calculate_similarity(alt.lower(), recent.lower()) > 0.7:
                    is_similar = True
                    break

            if not is_similar:
                alternatives.append(alt)

        return alternatives[:3]

    def _add_friendly_variation(self, response: str) -> str:
        """Add friendly variation to response."""
        friendly_prefixes = [
            "Great! ",
            "Awesome! ",
            "Perfect! ",
            "Happy to help! ",
        ]

        if random.random() < 0.3:  # 30% chance to add prefix
            prefix = random.choice(friendly_prefixes)
            return f"{prefix}{response}"

        return response

    def _add_casual_variation(self, response: str) -> str:
        """Add casual variation to response."""
        casual_starters = [
            "So, ",
            "Alright, ",
            "Okay, ",
            "Got it, ",
        ]

        if random.random() < 0.2:  # 20% chance to add starter
            starter = random.choice(casual_starters)
            return f"{starter}{response.lower()}"

        return response

    def _add_enthusiastic_variation(
        self,
        response: str,
        high_enthusiasm: bool = False,
    ) -> str:
        """Add enthusiastic variation to response."""
        if high_enthusiasm:
            return response.replace("!", "!!!").replace(".", "!")

        if random.random() < 0.25:  # 25% chance to add exclamation
            if not response.endswith("!"):
                return f"{response}!"

        return response

    def _add_formal_variation(self, response: str) -> str:
        """Add formal variation to response."""
        formal_prefixes = [
            "Certainly. ",
            "Of course. ",
            "Absolutely. ",
        ]

        if random.random() < 0.2:  # 20% chance to add prefix
            prefix = random.choice(formal_prefixes)
            return f"{prefix}{response}"

        return response

    def _add_concise_variation(self, response: str) -> str:
        """Add concise variation to response."""
        # Remove filler words
        concise_response = response.replace(" actually,", "").replace("basically,", "")

        # Remove redundant phrases
        redundant_phrases = [
            "in order to ",
            "for the purpose of ",
            "at this point in time ",
        ]

        for phrase in redundant_phrases:
            concise_response = concise_response.replace(phrase, "")

        return concise_response.strip()

    async def _add_natural_variation(
        self,
        response: str,
        personality: PersonalityType,
    ) -> str:
        """Add natural variation to response.

        Args:
            response: Response to enhance
            personality: Bot personality

        Returns:
            Enhanced response with natural variation
        """
        # Add natural filler phrases occasionally
        if random.random() < 0.1:  # 10% chance
            filler_phrases = {
                PersonalityType.FRIENDLY: [
                    ", actually,", ", basically,", ", you know,"
                ],
                PersonalityType.PROFESSIONAL: [
                    ", specifically,", ", to clarify,", ", in this case,"
                ],
                PersonalityType.ENTHUSIASTIC: [
                    ", basically,", ", you know,", ", actually,"
                ],
            }

            personality_fillers = filler_phrases.get(personality, [])
            if personality_fillers:
                filler = random.choice(personality_fillers)
                # Insert filler at random position
                words = response.split()
                if len(words) > 3:
                    insert_pos = random.randint(1, len(words) - 2)
                    words.insert(insert_pos, filler.rstrip(","))
                    response = " ".join(words)

        # Add occasional emphasis
        if random.random() < 0.05:  # 5% chance
            emphasis_words = ["really", "definitely", "certainly", "absolutely"]
            emphasis = random.choice(emphasis_words)

            # Add emphasis before important words
            if personality == PersonalityType.ENTHUSIASTIC:
                emphasis = emphasis.upper()

            words = response.split()
            if len(words) > 2:
                words[1] = f"{emphasis},"
                response = " ".join(words)

        return response

    async def _track_response(
        self,
        conversation_id: int,
        response: str,
    ) -> None:
        """Track response for variety analysis.

        Args:
            conversation_id: Conversation ID
            response: Response to track
        """
        # Update in-memory cache
        if conversation_id not in self.response_history:
            self.response_history[conversation_id] = []

        self.response_history[conversation_id].append(response)

        # Keep only last 10 responses in memory
        if len(self.response_history[conversation_id]) > 10:
            self.response_history[conversation_id] = self.response_history[conversation_id][-10:]

        # Update Redis cache
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:history:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(self.response_history[conversation_id]),
                )
            except Exception:
                pass