"""Performance Optimization System for Conversations.

Optimizes response generation with caching, pre-computation,
and intelligent resource management for faster response times.
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


class ConversationOptimizer:
    """Optimize conversation performance with caching and pre-computation."""

    REDIS_KEY_PREFIX = "conversation_optimizer"
    REDIS_TTL_SECONDS = 3600  # 1 hour for common responses
    CACHE_KEY_PREFIX = "response_cache"

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.cache = {}  # In-memory cache
        self.logger = structlog.get_logger(__name__)

    async def optimize_response_generation(
        self,
        context: ConversationContext,
        intent: str,
        merchant: PersonalityType,
        message: str,
    ) -> tuple[bool, Any]:
        """Optimize response generation with caching.

        Args:
            context: Conversation context
            intent: Current intent
            merchant: Bot personality
            message: User message

        Returns:
            Tuple of (cache_hit, cached_response_or_None)
        """
        # Generate cache key
        cache_key = self._generate_cache_key(context, intent, merchant)

        # Check in-memory cache first (fastest)
        if cache_key in self.cache:
            cached_response = self.cache[cache_key]
            if self._is_cache_valid(cached_response):
                self.logger.debug(
                    "cache_hit_memory",
                    cache_key=cache_key[:50],
                )
                return True, cached_response

        # Check Redis cache (slower but persistent)
        if self.redis:
            try:
                cached_data = self.redis.get(f"{self.CACHE_KEY_PREFIX}:{cache_key}")
                if cached_data:
                    cached_response = json.loads(cached_data)
                    if self._is_cache_valid(cached_response):
                        self.logger.debug(
                            "cache_hit_redis",
                            cache_key=cache_key[:50],
                        )
                        # Add to memory cache for next time
                        self.cache[cache_key] = cached_response
                        return True, cached_response
            except Exception:
                pass

        # No cache hit
        return False, None

    async def cache_response(
        self,
        context: ConversationContext,
        intent: str,
        merchant: PersonalityType,
        response: Any,
    ) -> None:
        """Cache response for future use.

        Args:
            context: Conversation context
            intent: Current intent
            merchant: Bot personality
            response: Response to cache
        """
        cache_key = self._generate_cache_key(context, intent, merchant)

        # Create cache entry
        cache_entry = {
            "response": response,
            "context_hash": self._hash_context(context),
            "intent": intent,
            "personality": merchant.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "access_count": 0,
        }

        # Store in memory cache (with size limit)
        if len(self.cache) > 1000:  # Limit memory cache
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["created_at"])
            del self.cache[oldest_key]

        self.cache[cache_key] = cache_entry

        # Store in Redis cache
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.CACHE_KEY_PREFIX}:{cache_key}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(cache_entry),
                )
            except Exception:
                pass

        self.logger.debug(
            "response_cached",
            cache_key=cache_key[:50],
        )

    async def pre_compute_common_responses(
        self,
        merchant: PersonalityType,
        db: Any,  # AsyncSession
    ) -> dict[str, Any]:
        """Pre-compute common responses for faster responses.

        Args:
            merchant: Merchant configuration
            db: Database session

        Returns:
            Pre-computed responses
        """
        common_scenarios = {
            "greeting": self._get_greeting_response(merchant),
            "return_policy": self._get_return_policy_response(merchant),
            "shipping_info": self._get_shipping_info_response(merchant),
            "product_search_general": self._get_product_search_general_response(merchant),
        }

        # Cache pre-computed responses
        for scenario, response in common_scenarios.items():
            cache_key = f"precomputed:{merchant.value}:{scenario}"

            if self.redis:
                try:
                    self.redis.setex(
                        f"{self.CACHE_KEY_PREFIX}:{cache_key}",
                        self.REDIS_TTL_SECONDS,
                        json.dumps({
                            "response": response,
                            "scenario": scenario,
                            "precomputed_at": datetime.now(timezone.utc).isoformat(),
                        }),
                    )
                except Exception:
                    pass

        return common_scenarios

    def _generate_cache_key(
        self,
        context: ConversationContext,
        intent: str,
        merchant: PersonalityType,
    ) -> str:
        """Generate cache key from context parameters.

        Args:
            context: Conversation context
            intent: Current intent
            merchant: Bot personality

        Returns:
            Cache key
        """
        import hashlib

        # Create hash from context
        # Handle both Channel enum and string values
        channel_value = context.channel.value if hasattr(context.channel, "value") else str(context.channel)

        context_str = json.dumps({
            "intent": intent,
            "personality": merchant.value,
            "channel": channel_value,
            "has_history": len(context.conversation_history) > 0,
            "metadata_keys": list(context.metadata.keys()) if context.metadata else [],
        }, sort_keys=True)

        context_hash = hashlib.md5(context_str.encode()).hexdigest()

        return f"{merchant.value}:{intent}:{context_hash[:16]}"

    def _hash_context(self, context: ConversationContext) -> str:
        """Hash conversation context for cache validation.

        Args:
            context: Conversation context

        Returns:
            Context hash
        """
        import hashlib

        # Hash key elements
        elements = [
            str(len(context.conversation_history)),
            str(hash(tuple(sorted(context.metadata.keys())))) if context.metadata else "0",
        ]

        return hashlib.md5("|".join(elements).encode()).hexdigest()

    def _is_cache_valid(self, cached_response: dict[str, Any]) -> bool:
        """Check if cached response is still valid.

        Args:
            cached_response: Cached response data

        Returns:
            True if cache is valid
        """
        # Check age (max 1 hour)
        created_at = cached_response.get("created_at", "")
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at)
                age = (datetime.now(timezone.utc) - created_time).total_seconds()

                if age > self.REDIS_TTL_SECONDS:
                    return False
            except Exception:
                pass

        # Check access count (evict after 100 uses)
        access_count = cached_response.get("access_count", 0)
        if access_count > 100:
            return False

        return True

    def _get_greeting_response(self, merchant: PersonalityType) -> str:
        """Get pre-computed greeting response.

        Args:
            merchant: Bot personality

        Returns:
            Greeting response
        """
        greetings = {
            PersonalityType.FRIENDLY: "Hi there! How can I help you today?",
            PersonalityType.PROFESSIONAL: "Hello! How may I assist you today?",
            PersonalityType.ENTHUSIASTIC: "Hey!!! So excited to help you!!! What can I do for you today?!",
        }

        return greetings.get(merchant, greetings[PersonalityType.FRIENDLY])

    def _get_return_policy_response(self, merchant: PersonalityType) -> str:
        """Get pre-computed return policy response.

        Args:
            merchant: Bot personality

        Returns:
            Return policy response
        """
        responses = {
            PersonalityType.FRIENDLY: "Our return policy is simple: you have 30 days from delivery to return items in original condition. I can help you with specific return details!",
            PersonalityType.PROFESSIONAL: "Our return policy allows returns within 30 days of delivery. Items must be in original condition. I can provide specific return instructions.",
            PersonalityType.ENTHUSIASTIC: "Our return policy is super easy!!! You have 30 days to return items in original condition!!! I'll help you with all the details!!!",
        }

        return responses.get(merchant, responses[PersonalityType.FRIENDLY])

    def _get_shipping_info_response(self, merchant: PersonalityType) -> str:
        """Get pre-computed shipping info response.

        Args:
            merchant: Bot personality

        Returns:
            Shipping info response
        """
        responses = {
            PersonalityType.FRIENDLY: "We offer standard shipping (5-7 business days) and express shipping (2-3 business days). Free shipping on orders over $50!",
            PersonalityType.PROFESSIONAL: "We provide standard shipping (5-7 business days) and express shipping (2-3 business days). Complimentary shipping is available for orders over $50.",
            PersonalityType.ENTHUSIASTIC: "We've got super fast shipping!!! Standard shipping takes 5-7 business days, express is just 2-3 days!!! Free shipping on orders over $50!!!",
        }

        return responses.get(merchant, responses[PersonalityType.FRIENDLY])

    def _get_product_search_general_response(self, merchant: PersonalityType) -> str:
        """Get pre-computed product search response.

        Args:
            merchant: Bot personality

        Returns:
            Product search response
        """
        responses = {
            PersonalityType.FRIENDLY: "I'd be happy to help you find what you're looking for! What type of product are you interested in?",
            PersonalityType.PROFESSIONAL: "I can assist you with product search. What type of item are you looking for?",
            PersonalityType.ENTHUSIASTIC: "I'd LOVE to help you find exactly what you need!!! What are you looking for?!",
        }

        return responses.get(merchant, responses[PersonalityType.FRIENDLY])

    async def get_performance_stats(
        self,
    ) -> dict[str, Any]:
        """Get performance optimization statistics.

        Returns:
            Performance statistics
        """
        stats = {
            "memory_cache_size": len(self.cache),
            "memory_cache_keys": list(self.cache.keys())[:10],  # First 10 keys
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # Calculate cache hit rate from Redis
        if self.redis:
            try:
                # This would need actual tracking implementation
                stats["redis_cache_enabled"] = True
            except Exception:
                stats["redis_cache_enabled"] = False

        return stats

    async def invalidate_cache(
        self,
        conversation_id: int | None = None,
        merchant_id: int | None = None,
    ) -> int:
        """Invalidate cache entries.

        Args:
            conversation_id: Optional conversation ID to invalidate
            merchant_id: Optional merchant ID to invalidate

        Returns:
            Number of cache entries invalidated
        """
        invalidated = 0

        # Invalidate by conversation
        if conversation_id:
            keys_to_delete = [
                key for key in self.cache.keys()
                if str(conversation_id) in key
            ]

            for key in keys_to_delete:
                del self.cache[key]
                invalidated += 1

        # Invalidate by merchant
        if merchant_id:
            personality_prefixes = ["FRIENDLY", "PROFESSIONAL", "ENTHUSIASTIC"]
            for prefix in personality_prefixes:
                keys_to_delete = [
                    key for key in self.cache.keys()
                    if f"{prefix}:" in key
                ]

                for key in keys_to_delete:
                    del self.cache[key]
                    invalidated += 1

        # Invalidate Redis cache
        if self.redis and (conversation_id or merchant_id):
            try:
                pattern = f"*{conversation_id if conversation_id else '*'}:{merchant_id if merchant_id else '*'}*"

                # Use SCAN to find matching keys
                cursor = "0"
                while cursor:
                    cursor, keys = self.redis.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100,
                    )

                    if keys:
                        self.redis.delete(*keys)
                        invalidated += len(keys)

                    if cursor == "0":
                        break
            except Exception:
                pass

        return invalidated