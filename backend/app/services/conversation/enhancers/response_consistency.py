"""Response Consistency Enhancement System.

Prevents bot from giving contradictory information across conversations
and ensures responses remain consistent with conversation history.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import ConversationTurn
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class ResponseConsistencyChecker:
    """Ensures responses are consistent with conversation history."""

    REDIS_KEY_PREFIX = "response_consistency"
    REDIS_TTL_SECONDS = 86400  # 24 hours

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def check_response_consistency(
        self,
        proposed_response: str,
        conversation_history: list[ConversationTurn],
        conversation_id: int,
        personality: PersonalityType,
    ) -> dict[str, Any]:
        """Check if proposed response is consistent with history.

        Args:
            proposed_response: The response we want to send
            conversation_history: Previous conversation turns
            conversation_id: Current conversation ID
            personality: Bot personality type

        Returns:
            Consistency check results with suggestions if needed
        """
        # Skip consistency check for short conversations
        if len(conversation_history) < 2:
            return {"is_consistent": True, "reason": "short_conversation"}

        # Get previous responses
        previous_responses = [
            turn.bot_message for turn in conversation_history[-3:]
            if turn.bot_message
        ]

        # Check for direct contradictions
        contradictions = await self._detect_contradictions(
            proposed_response, previous_responses
        )

        if contradictions:
            self.logger.info(
                "response_contradiction_detected",
                conversation_id=conversation_id,
                contradictions=len(contradictions),
            )

            # Generate consistent alternative
            consistent_response = await self._generate_consistent_response(
                proposed_response,
                previous_responses,
                contradictions,
                personality,
            )

            return {
                "is_consistent": False,
                "reason": "contradiction_detected",
                "contradictions": contradictions,
                "original_response": proposed_response,
                "suggested_response": consistent_response,
            }

        # Check for factual consistency
        factual_check = await self._check_factual_consistency(
            proposed_response, conversation_history, conversation_id
        )

        if not factual_check["is_factual_consistent"]:
            return {
                "is_consistent": False,
                "reason": "factual_inconsistency",
                "inconsistencies": factual_check["inconsistencies"],
                "suggested_response": await self._generate_factually_consistent_response(
                    proposed_response, factual_check["inconsistencies"], personality
                ),
            }

        # Response is consistent
        await self._track_response_patterns(
            conversation_id, proposed_response, personality
        )

        return {"is_consistent": True, "reason": "no_issues"}

    async def _detect_contradictions(
        self,
        proposed_response: str,
        previous_responses: list[str],
    ) -> list[dict[str, Any]]:
        """Detect direct contradictions with previous responses.

        Args:
            proposed_response: Response we want to send
            previous_responses: Previous bot responses

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Define contradiction patterns
        contradiction_patterns = [
            # Direct opposites
            (r"(?i)\b(yes|available|in stock|open|working)\b",
             r"(?i)\b(no|unavailable|out of stock|closed|not working)\b"),
            # Price contradictions
            (r"(?i)\$(\d+)", r"(?i)\$(\d+)"),
            # Time contradictions
            (r"(?i)\b(\d+) (?:days?|hours?)\b", r"(?i)\b(\d+) (?:days?|hours?)\b"),
            # Statement contradictions
            (r"(?i)\bwe (?:do|can|will)\b", r"(?i)\bwe (?:don't|can't|won't)\b"),
        ]

        for prev_response in previous_responses:
            for pattern_1, pattern_2 in contradiction_patterns:
                # Check if previous response has pattern_1
                if __import__("re").search(pattern_1, prev_response):
                    # Check if proposed response has pattern_2
                    if __import__("re").search(pattern_2, proposed_response):
                        contradictions.append({
                            "type": "direct_contradiction",
                            "previous_response": prev_response,
                            "contradiction": f"Pattern mismatch: {pattern_1} vs {pattern_2}",
                            "severity": "high",
                        })

        return contradictions

    async def _check_factual_consistency(
        self,
        proposed_response: str,
        conversation_history: list[ConversationTurn],
        conversation_id: int,
    ) -> dict[str, Any]:
        """Check factual consistency with established information.

        Args:
            proposed_response: Response we want to send
            conversation_history: Conversation history
            conversation_id: Conversation ID

        Returns:
            Factual consistency check results
        """
        # Get established facts from conversation
        established_facts = await self._get_established_facts(
            conversation_id, conversation_history
        )

        inconsistencies = []

        # Check if response contradicts established facts
        for fact_type, fact_value in established_facts.items():
            if self._contradicts_fact(proposed_response, fact_type, fact_value):
                inconsistencies.append({
                    "fact_type": fact_type,
                    "established_value": fact_value,
                    "contradiction": f"Response contradicts established {fact_type}",
                })

        return {
            "is_factual_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
            "established_facts": established_facts,
        }

    async def _generate_consistent_response(
        self,
        proposed_response: str,
        previous_responses: list[str],
        contradictions: list[dict[str, Any]],
        personality: PersonalityType,
    ) -> str:
        """Generate response that's consistent with history.

        Args:
            proposed_response: Original proposed response
            previous_responses: Previous bot responses
            contradictions: Detected contradictions
            personality: Bot personality

        Returns:
            Consistent response
        """
        # For now, use simple conflict resolution
        # In production, this would use LLM to generate consistent response

        # If high severity contradiction, acknowledge and clarify
        high_severity = [c for c in contradictions if c.get("severity") == "high"]

        if high_severity:
            # Acknowledge the inconsistency
            acknowledgments = {
                PersonalityType.FRIENDLY: "I want to make sure I'm consistent here...",
                PersonalityType.PROFESSIONAL: "Let me clarify to ensure accuracy...",
                PersonalityType.ENTHUSIASTIC: "I want to make sure I get this right!!!",
            }

            acknowledgment = acknowledgments.get(
                personality, "Let me clarify..."
            )

            return f"{acknowledgment} Based on what we discussed earlier, {proposed_response.lower()}"

        return proposed_response

    async def _generate_factually_consistent_response(
        self,
        proposed_response: str,
        inconsistencies: list[dict[str, Any]],
        personality: PersonalityType,
    ) -> str:
        """Generate factually consistent response.

        Args:
            proposed_response: Original proposed response
            inconsistencies: Detected factual inconsistencies
            personality: Bot personality

        Returns:
            Factually consistent response
        """
        if inconsistencies:
            inconsistency = inconsistencies[0]
            fact_type = inconsistency["fact_type"]
            established_value = inconsistency["established_value"]

            clarifications = {
                PersonalityType.FRIENDLY: f"Just to confirm, we established earlier that {fact_type}: {established_value}. Is that still correct?",
                PersonalityType.PROFESSIONAL: f"To confirm our earlier discussion: {fact_type}: {established_value}. Is this still accurate?",
                PersonalityType.ENTHUSIASTIC: f"Quick check! We talked about {fact_type}: {established_value} - is that still right?",
            }

            return clarifications.get(
                personality, f"Regarding {fact_type}, we mentioned {established_value} earlier..."
            )

        return proposed_response

    async def _get_established_facts(
        self,
        conversation_id: int,
        conversation_history: list[ConversationTurn],
    ) -> dict[str, Any]:
        """Extract established facts from conversation history.

        Args:
            conversation_id: Conversation ID
            conversation_history: Conversation history

        Returns:
            Dictionary of established facts
        """
        facts = {}

        # Check if we have cached facts
        if self.redis:
            try:
                cached_facts = self.redis.get(f"{self.REDIS_KEY_PREFIX}:facts:{conversation_id}")
                if cached_facts:
                    return json.loads(cached_facts)
            except Exception:
                pass

        # Extract facts from recent conversation turns
        for turn in conversation_history[-5:]:
            # Extract facts like prices, dates, policies
            user_msg = turn.user_message.lower()

            # Price facts
            import re
            prices = re.findall(r'\$(\d+)', user_msg)
            if prices:
                facts["price_range"] = {"min": min(prices), "max": max(prices)}

            # Time facts
            times = re.findall(r'(\d+) (?:days?|hours?)', user_msg)
            if times:
                facts["timeframe"] = times

            # Policy facts
            if "return policy" in user_msg:
                facts["return_policy_discussed"] = True

            # Product facts
            if "looking for" in user_msg or "want" in user_msg:
                facts["product_interest"] = True

        # Cache facts
        if self.redis and facts:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:facts:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(facts),
                )
            except Exception:
                pass

        return facts

    def _contradicts_fact(
        self,
        response: str,
        fact_type: str,
        fact_value: Any,
    ) -> bool:
        """Check if response contradicts established fact.

        Args:
            response: Response to check
            fact_type: Type of fact
            fact_value: Value of fact

        Returns:
            True if contradicts fact
        """
        response_lower = response.lower()

        # Check for price contradictions
        if fact_type == "price_range":
            import re
            prices = re.findall(r'\$(\d+)', response_lower)
            if prices:
                min_price = fact_value["min"]
                max_price = fact_value["max"]
                # Check if new prices are outside established range
                for price in prices:
                    if int(price) < int(min_price) * 0.8 or int(price) > int(max_price) * 1.2:
                        return True

        return False

    async def _track_response_patterns(
        self,
        conversation_id: int,
        response: str,
        personality: PersonalityType,
    ) -> None:
        """Track response patterns for consistency analysis.

        Args:
            conversation_id: Conversation ID
            response: Response sent
            personality: Bot personality
        """
        # Store response pattern for analysis
        if self.redis:
            try:
                pattern_key = f"{self.REDIS_KEY_PREFIX}:patterns:{conversation_id}"
                existing_patterns = self.redis.get(pattern_key)

                patterns = []
                if existing_patterns:
                    patterns = json.loads(existing_patterns)

                patterns.append({
                    "response_length": len(response),
                    "personality": personality.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                self.redis.setex(
                    pattern_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(patterns[-10:]),  # Keep last 10
                )
            except Exception:
                pass