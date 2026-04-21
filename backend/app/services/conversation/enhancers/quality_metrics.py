"""Conversation Quality Metrics Tracker.

Comprehensive quality measurement system for tracking conversation
performance and enabling data-driven optimization.
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


class ConversationQualityTracker:
    """Track conversation quality metrics."""

    REDIS_KEY_PREFIX = "quality_metrics"
    REDIS_TTL_SECONDS = 604800  # 7 days

    def __init__(self, redis_client: Redis | None = None):
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def track_quality_metrics(
        self,
        conversation_id: int,
        context: ConversationContext,
        response_metadata: dict[str, Any],
        merchant: PersonalityType,
        processing_time_ms: float,
    ) -> dict[str, float]:
        """Calculate quality metrics for conversation.

        Args:
            conversation_id: Conversation ID
            context: Conversation context
            response_metadata: Response metadata
            merchant: Bot personality
            processing_time_ms: Processing time in milliseconds

        Returns:
            Dictionary of quality metrics
        """
        metrics = {}

        # Emotional intelligence score
        metrics["empathy_score"] = self._calculate_empathy_score(context, response_metadata)

        # Context awareness score
        metrics["context_score"] = self._calculate_context_score(context, response_metadata)

        # Response relevance score
        metrics["relevance_score"] = self._calculate_relevance_score(context, response_metadata)

        # Conversation flow score
        metrics["flow_score"] = self._calculate_flow_score(context)

        # Goal completion score
        metrics["completion_score"] = self._calculate_completion_score(context, response_metadata)

        # Performance score
        metrics["performance_score"] = self._calculate_performance_score(processing_time_ms)

        # Overall satisfaction predictor
        metrics["satisfaction_predictor"] = self._predict_satisfaction(metrics)

        # Store metrics for analysis
        await self._store_metrics(conversation_id, metrics, merchant)

        return metrics

    def _calculate_empathy_score(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any],
    ) -> float:
        """Calculate emotional intelligence score.

        Args:
            context: Conversation context
            response_metadata: Response metadata

        Returns:
            Empathy score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check if empathy was applied
        if response_metadata.get("empathy_applied"):
            empathy_level = response_metadata.get("empathy_level", "none")

            empathy_scores = {
                "none": 0.0,
                "low": 0.6,
                "medium": 0.8,
                "high": 1.0,
            }

            score = empathy_scores.get(empathy_level, 0.5)

        # Check for emotional profile
        emotional_profile = response_metadata.get("emotional_profile")
        if emotional_profile:
            intensity = emotional_profile.get("intensity", 0.0)

            # Higher intensity detected and responded to = better
            if intensity > 0.6 and score > 0.7:
                score = min(score + 0.2, 1.0)

        return min(score, 1.0)

    def _calculate_context_score(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any],
    ) -> float:
        """Calculate context awareness score.

        Args:
            context: Conversation context
            response_metadata: Response metadata

        Returns:
            Context score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check for topic bridging
        if response_metadata.get("topic_bridging_applied"):
            score += 0.2

        # Check for cross-references
        if response_metadata.get("cross_reference_applied"):
            score += 0.15

        # Check for context restoration
        if response_metadata.get("context_restoration"):
            score += 0.15

        # Check for enhanced context usage
        enhanced_context = response_metadata.get("enhanced_context")
        if enhanced_context:
            context_count = len(enhanced_context.get("topics", []))
            score += min(context_count * 0.05, 0.3)

        return min(score, 1.0)

    def _calculate_relevance_score(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any],
    ) -> float:
        """Calculate response relevance score.

        Args:
            context: Conversation context
            response_metadata: Response metadata

        Returns:
            Relevance score (0.0 to 1.0)
        """
        score = 0.7  # Base score

        # Check if intent was handled appropriately
        intent = response_metadata.get("intent", "unknown")
        confidence = response_metadata.get("confidence", 0.0)

        if confidence > 0.7:
            score += 0.15

        # Check if products were shown (if relevant)
        if response_metadata.get("products"):
            score += 0.1

        # Check for clarification loops
        if context.metadata.get("clarification_attempt_count", 0) < 3:
            score += 0.05

        return min(score, 1.0)

    def _calculate_flow_score(
        self,
        context: ConversationContext,
    ) -> float:
        """Calculate conversation flow score.

        Args:
            context: Conversation context

        Returns:
            Flow score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        conversation_history = context.conversation_history

        if len(conversation_history) < 2:
            return score

        # Check for natural conversation flow
        # (In production, this would use ML model)
        # For now, use simple heuristics

        # Check response length variety (avoid too short/long responses)
        response_lengths = []
        for turn in conversation_history[-5:]:
            if turn.bot_message:
                response_lengths.append(len(turn.bot_message))

        if response_lengths:
            avg_length = sum(response_lengths) / len(response_lengths)
            # Ideal average length: 100-500 chars
            if 100 <= avg_length <= 500:
                score += 0.2
            elif avg_length > 500:
                score -= 0.1

        # Check for repeated phrases (simple heuristic)
        unique_responses = len(set(
            turn.bot_message[:50] for turn in conversation_history[-3:] if turn.bot_message
        ))

        if unique_responses == len(conversation_history[-3:]):
            score += 0.3

        return min(score, 1.0)

    def _calculate_completion_score(
        self,
        context: ConversationContext,
        response_metadata: dict[str, Any],
    ) -> float:
        """Calculate goal completion score.

        Args:
            context: Conversation context
            response_metadata: Response metadata

        Returns:
            Completion score (0.0 to 1.0)
        """
        score = 0.5  # Base score

        # Check goal progress
        goal_state = response_metadata.get("goal_state")
        if goal_state:
            progress = goal_state.get("progress", 0.0)
            score = progress / 100.0

        # Check for cart actions
        if response_metadata.get("cart_action_performed"):
            score += 0.2

        # Check for products shown
        if response_metadata.get("products"):
            score += 0.1

        return min(score, 1.0)

    def _calculate_performance_score(
        self,
        processing_time_ms: float,
    ) -> float:
        """Calculate performance score.

        Args:
            processing_time_ms: Processing time in milliseconds

        Returns:
            Performance score (0.0 to 1.0)
        """
        # Target: <2 seconds for good performance
        if processing_time_ms < 1000:
            return 1.0
        elif processing_time_ms < 2000:
            return 0.8
        elif processing_time_ms < 3000:
            return 0.6
        elif processing_time_ms < 5000:
            return 0.4
        else:
            return 0.2

    def _predict_satisfaction(
        self,
        metrics: dict[str, float],
    ) -> float:
        """Predict user satisfaction from metrics.

        Args:
            metrics: Quality metrics

        Returns:
            Satisfaction prediction (0.0 to 1.0)
        """
        # Weighted average of key metrics
        weights = {
            "empathy_score": 0.25,
            "context_score": 0.20,
            "relevance_score": 0.25,
            "flow_score": 0.15,
            "completion_score": 0.15,
        }

        satisfaction = sum(
            metrics.get(metric, 0.5) * weight
            for metric, weight in weights.items()
        )

        return min(satisfaction, 1.0)

    async def _store_metrics(
        self,
        conversation_id: int,
        metrics: dict[str, float],
        merchant: PersonalityType,
    ) -> None:
        """Store metrics for analysis.

        Args:
            conversation_id: Conversation ID
            metrics: Quality metrics
            merchant: Bot personality
        """
        if self.redis:
            try:
                metric_data = {
                    "conversation_id": conversation_id,
                    "metrics": metrics,
                    "personality": merchant.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                # Store conversation metrics
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:conversation:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(metric_data),
                )

                # Store aggregated metrics for merchant
                merchant_key = f"{self.REDIS_KEY_PREFIX}:merchant:{merchant.value}"
                merchant_metrics = self.redis.get(merchant_key)
                metrics_list = json.loads(merchant_metrics) if merchant_metrics else []

                metrics_list.append(metric_data)
                self.redis.setex(
                    merchant_key,
                    self.REDIS_TTL_SECONDS,
                    json.dumps(metrics_list[-100:]),  # Keep last 100
                )
            except Exception:
                pass

    async def get_merchant_metrics(
        self,
        merchant: PersonalityType,
    ) -> dict[str, Any]:
        """Get aggregated metrics for merchant.

        Args:
            merchant: Bot personality

        Returns:
            Aggregated metrics
        """
        if not self.redis:
            return {}

        try:
            merchant_key = f"{self.REDIS_KEY_PREFIX}:merchant:{merchant.value}"
            merchant_metrics = self.redis.get(merchant_key)

            if merchant_metrics:
                metrics_list = json.loads(merchant_metrics)

                # Calculate averages
                total_conversations = len(metrics_list)

                if total_conversations > 0:
                    avg_metrics = {
                        "total_conversations": total_conversations,
                        "avg_empathy_score": sum(
                            m["metrics"]["empathy_score"] for m in metrics_list
                        ) / total_conversations,
                        "avg_context_score": sum(
                            m["metrics"]["context_score"] for m in metrics_list
                        ) / total_conversations,
                        "avg_relevance_score": sum(
                            m["metrics"]["relevance_score"] for m in metrics_list
                        ) / total_conversations,
                        "avg_flow_score": sum(
                            m["metrics"]["flow_score"] for m in metrics_list
                        ) / total_conversations,
                        "avg_completion_score": sum(
                            m["metrics"]["completion_score"] for m in metrics_list
                        ) / total_conversations,
                        "avg_satisfaction": sum(
                            m["metrics"]["satisfaction_predictor"] for m in metrics_list
                        ) / total_conversations,
                    }

                    return avg_metrics
        except Exception:
            pass

        return {}