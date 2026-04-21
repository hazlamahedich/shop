"""Natural Typing Indicators Simulator.

Simulates natural typing behavior and delays to make conversations
feel more human and less robotic.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import structlog
from redis import Redis

from app.models.conversation_context import ConversationContext
from app.models.merchant import PersonalityType

logger = structlog.get_logger(__name__)


class NaturalTypingSimulator:
    """Simulate natural typing behavior for conversations."""

    REDIS_KEY_PREFIX = "typing_simulator"
    REDIS_TTL_SECONDS = 3600  # 1 hour

    # Typing speed: ~50 chars per second
    CHARS_PER_SECOND = 50

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def get_typing_duration(
        self,
        response_length: int,
        complexity: float = 0.5,
        conversation_id: int | None = None,
        personality: PersonalityType = PersonalityType.FRIENDLY,
    ) -> float:
        """Calculate natural typing duration.

        Args:
            response_length: Length of response in characters
            complexity: Response complexity (0.0 to 1.0)
            conversation_id: Optional conversation ID for personalization
            personality: Bot personality

        Returns:
            Typing duration in seconds
        """
        # Base typing speed
        base_duration = response_length / self.CHARS_PER_SECOND

        # Add complexity factor (complex responses take longer)
        complexity_multiplier = 1.0 + (complexity * 0.5)
        adjusted_duration = base_duration * complexity_multiplier

        # Add natural variation (±20%)
        import random
        variation = random.uniform(0.8, 1.2)
        duration_with_variation = adjusted_duration * variation

        # Personality-based adjustments
        personality_modifiers = {
            PersonalityType.FRIENDLY: 1.0,      # Normal speed
            PersonalityType.PROFESSIONAL: 0.9,   # Slightly faster
            PersonalityType.ENTHUSIASTIC: 1.2, # More expressive, slower
        }

        final_duration = duration_with_variation * personality_modifiers.get(
            personality, 1.0
        )

        # Add minimum typing time (even for short responses)
        minimum_time = 0.5  # 0.5 seconds minimum
        maximum_time = 15.0  # 15 seconds maximum

        return max(minimum_time, min(maximum_time, final_duration))

    async def simulate_typing(
        self,
        duration: float,
        conversation_id: int | None = None,
    ) -> None:
        """Simulate typing indicator and delay.

        Args:
            duration: Typing duration in seconds
            conversation_id: Optional conversation ID for events
        """
        # Send typing indicator
        await self._send_typing_indicator(True, conversation_id)

        # Wait for typing duration
        await asyncio.sleep(duration)

        # Clear typing indicator
        await self._send_typing_indicator(False, conversation_id)

    async def simulate_thinking(
        self,
        duration: float = 1.0,
        conversation_id: int | None = None,
    ) -> None:
        """Simulate thinking delay before response.

        Args:
            duration: Thinking duration in seconds
            conversation_id: Optional conversation ID for events
        """
        # Add small random variation
        import random
        varied_duration = duration * random.uniform(0.8, 1.2)

        await asyncio.sleep(varied_duration)

    async def _send_typing_indicator(
        self,
        is_typing: bool,
        conversation_id: int | None = None,
    ) -> None:
        """Send typing indicator event.

        Args:
            is_typing: True to show typing, False to hide
            conversation_id: Optional conversation ID
        """
        # In production, this would send WebSocket event to frontend
        # For now, we just log it
        if conversation_id:
            self.logger.debug(
                "typing_indicator",
                conversation_id=conversation_id,
                is_typing=is_typing,
                status="showing" if is_typing else "cleared",
            )

    async def get_typing_behavior_config(
        self,
        merchant: PersonalityType,
        context: ConversationContext | None = None,
    ) -> dict[str, Any]:
        """Get typing behavior configuration for merchant.

        Args:
            merchant: Bot personality
            context: Optional conversation context

        Returns:
            Typing behavior configuration
        """
        config = {
            "enabled": True,
            "min_typing_time": 0.5,
            "max_typing_time": 15.0,
            "typing_variation": 0.2,  # ±20% variation
            "thinking_time": 1.0,
            "personality_adjustments": {
                PersonalityType.FRIENDLY: {
                    "base_speed": 1.0,
                    "variation": 0.2,
                },
                PersonalityType.PROFESSIONAL: {
                    "base_speed": 0.9,
                    "variation": 0.15,
                },
                PersonalityType.ENTHUSIASTIC: {
                    "base_speed": 1.2,
                    "variation": 0.25,
                },
            },
        }

        return config

    async def should_simulate_typing(
        self,
        context: ConversationContext,
        response_length: int,
    ) -> bool:
        """Determine if typing simulation is appropriate.

        Args:
            context: Conversation context
            response_length: Length of response

        Returns:
            True if typing should be simulated
        """
        # Don't simulate typing for very short responses
        if response_length < 20:
            return False

        # Don't simulate typing for urgent/intent
        if context.metadata.get("urgent"):
            return False

        # Don't simulate typing for error responses
        if context.metadata.get("is_error_response"):
            return False

        # Simulate typing for normal conversational responses
        return True

    async def calculate_response_complexity(
        self,
        response: str,
        context: ConversationContext,
    ) -> float:
        """Calculate response complexity for typing duration.

        Args:
            response: Response text
            context: Conversation context

        Returns:
            Complexity score (0.0 to 1.0)
        """
        complexity = 0.5  # Base complexity

        # Length complexity
        if len(response) > 500:
            complexity += 0.2
        elif len(response) > 200:
            complexity += 0.1

        # Structural complexity
        if "\n" in response:
            complexity += 0.1

        # Contains lists or numbered items
        if any(char in response for char in ["1.", "2.", "3.", "-", "•"]):
            complexity += 0.1

        # Contains questions
        if "?" in response:
            complexity += 0.1

        # Contains links or URLs
        if "http" in response or "www." in response:
            complexity += 0.1

        return min(complexity, 1.0)

    async def track_typing_metrics(
        self,
        conversation_id: int,
        typing_duration: float,
        response_length: int,
    ) -> None:
        """Track typing metrics for analytics.

        Args:
            conversation_id: Conversation ID
            typing_duration: How long typing was simulated
            response_length: Length of response
        """
        if self.redis:
            try:
                metric_key = f"{self.REDIS_KEY_PREFIX}:metrics:{conversation_id}"
                metric_data = {
                    "typing_duration": typing_duration,
                    "response_length": response_length,
                    "chars_per_second": response_length / typing_duration if typing_duration > 0 else 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                self.redis.setex(
                    metric_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(metric_data),
                )
            except Exception:
                pass

    async def get_aggregated_typing_stats(
        self,
        merchant_id: int | None = None,
    ) -> dict[str, Any]:
        """Get aggregated typing statistics.

        Args:
            merchant_id: Optional merchant ID filter

        Returns:
            Aggregated typing statistics
        """
        if not self.redis:
            return {}

        try:
            # Scan for typing metrics
            pattern = f"{self.REDIS_KEY_PREFIX}:metrics:*"
            cursor = "0"
            all_metrics = []

            while cursor:
                cursor, keys = self.redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )

                if keys:
                    for key in keys:
                        data = self.redis.get(key)
                        if data:
                            all_metrics.append(json.loads(data))

                if cursor == "0":
                    break

            if all_metrics:
                total_typing_time = sum(m["typing_duration"] for m in all_metrics)
                total_response_length = sum(m["response_length"] for m in all_metrics)

                avg_typing_duration = total_typing_time / len(all_metrics) if all_metrics else 0
                avg_response_length = total_response_length / len(all_metrics) if all_metrics else 0
                avg_chars_per_second = total_response_length / total_typing_time if total_typing_time > 0 else 0

                return {
                    "total_conversations": len(all_metrics),
                    "avg_typing_duration": avg_typing_duration,
                    "avg_response_length": avg_response_length,
                    "avg_chars_per_second": avg_chars_per_second,
                    "total_typing_time": total_typing_time,
                }
        except Exception:
            pass

        return {}

    async def should_add_thinking_pause(
        self,
        context: ConversationContext,
        response_complexity: float,
    ) -> bool:
        """Determine if thinking pause is appropriate.

        Args:
            context: Conversation context
            response_complexity: Response complexity score

        Returns:
            True if thinking pause should be added
        """
        # Add thinking pause for complex questions
        if response_complexity > 0.7:
            return True

        # Add thinking pause if user seems confused
        if context.metadata.get("user_confused"):
            return True

        # Add thinking pause for first message in long conversation
        if len(context.conversation_history) > 10 and context.metadata.get("is_first_message"):
            return True

        return False

    async def get_thinking_duration(
        self,
        response_complexity: float,
        personality: PersonalityType,
    ) -> float:
        """Calculate appropriate thinking duration.

        Args:
            response_complexity: Response complexity score
            personality: Bot personality

        Returns:
            Thinking duration in seconds
        """
        # Base thinking time
        base_time = 1.0

        # Add complexity factor
        complexity_time = base_time * (1.0 + response_complexity)

        # Personality adjustments
        personality_modifiers = {
            PersonalityType.FRIENDLY: 1.0,
            PersonalityType.PROFESSIONAL: 0.8,
            PersonalityType.ENTHUSIASTIC: 1.2,
        }

        final_time = complexity_time * personality_modifiers.get(personality, 1.0)

        # Add variation
        import random
        variation = random.uniform(0.8, 1.2)

        return final_time * variation