"""Conversation Context Service with Redis + PostgreSQL.

Story 11-1: Conversation Context Memory
Manages conversation context with hybrid storage (Redis for fast access, PostgreSQL for analytics).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import structlog
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_context import (
    ConversationContext,
    ConversationTurn,
)
from app.services.context import EcommerceContextExtractor, GeneralContextExtractor

logger = structlog.get_logger(__name__)

ModeType = Literal["ecommerce", "general"]


class ConversationContextService:
    """Manages conversation context with Redis + PostgreSQL.

    Storage Strategy:
    - Redis: Fast access with 24-hour TTL (hot data)
    - PostgreSQL: Analytics, history, durability (cold data)

    Context Structure:
    {
        "mode": "ecommerce" | "general",
        "turn_count": 5,
        "viewed_products": [123, 456],           # E-commerce
        "constraints": {"budget_max": 100},      # E-commerce
        "topics_discussed": ["login issue"],     # General
        "documents_referenced": [123],           # General
        "expires_at": "2026-03-31T12:00:00Z"
    }
    """

    REDIS_KEY_PREFIX = "conversation_context"
    REDIS_TTL_SECONDS = 86400  # 24 hours
    SUMMARIZE_TURNS_TRIGGER = 5
    SUMMARIZE_SIZE_TRIGGER_BYTES = 1024  # 1KB

    def __init__(
        self,
        db: AsyncSession,
        redis_client: Redis | None = None,
    ):
        self.db = db
        self.redis = redis_client
        self.logger = structlog.get_logger(__name__)

    async def get_context(
        self, conversation_id: int, bypass_cache: bool = False
    ) -> dict[str, Any] | None:
        if not bypass_cache and self.redis:
            try:
                context_json = self.redis.get(f"{self.REDIS_KEY_PREFIX}:{conversation_id}")
                if context_json:
                    self.logger.debug("Context cache hit", conversation_id=conversation_id)
                    return json.loads(context_json)
            except Exception as e:
                self.logger.warning(
                    "Redis get failed", error=str(e), conversation_id=conversation_id
                )

        self.logger.debug("Context cache miss, checking DB", conversation_id=conversation_id)
        result = await self.db.execute(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        context_model = result.scalar_one_or_none()

        if context_model:
            if context_model.expires_at < datetime.now(timezone.utc):
                self.logger.info("Context expired", conversation_id=conversation_id)
                return None

            context = self._model_to_dict(context_model)

            if self.redis:
                try:
                    self.redis.setex(
                        f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                        self.REDIS_TTL_SECONDS,
                        json.dumps(context),
                    )
                except Exception as e:
                    self.logger.warning("Redis repopulate failed", error=str(e))

            return context

        return None

    async def update_context(
        self,
        conversation_id: int,
        merchant_id: int,
        message: str,
        mode: ModeType,
    ) -> dict[str, Any]:
        existing_context = await self.get_context(conversation_id)

        if not existing_context:
            existing_context = {
                "mode": mode,
                "turn_count": 0,
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            }

        # Extract delta updates using mode-specific extractor, then merge with existing context.
        extractor = self._get_extractor(mode)
        updates = await extractor.extract(message, existing_context)
        updated_context = extractor._merge_context(existing_context, updates)

        # Log constraint contradictions for analytics (AC7: conflict resolution)
        self._log_constraint_changes(existing_context, updated_context, conversation_id)

        # Persist to PostgreSQL FIRST (so we have timestamps)
        await self._persist_to_db(
            conversation_id=conversation_id,
            merchant_id=merchant_id,
            context=updated_context,
        )

        # Reload from DB to get complete context with timestamps
        final_context = await self.get_context(conversation_id, bypass_cache=True)

        if not final_context:
            self.logger.warning(
                "Context not found after persisting", conversation_id=conversation_id
            )
            final_context = updated_context

        # Update Redis cache with complete context
        if self.redis:
            try:
                self.redis.setex(
                    f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                    self.REDIS_TTL_SECONDS,
                    json.dumps(final_context),
                )
            except Exception as e:
                self.logger.warning(
                    "Redis set failed", error=str(e), conversation_id=conversation_id
                )

        # Auto-summarize when trigger conditions are met
        if await self.should_summarize(final_context):
            self.logger.info(
                "Auto-summarization triggered",
                conversation_id=conversation_id,
                turn_count=final_context.get("turn_count", 0),
            )
            try:
                summarized = await self.summarize_context(conversation_id, final_context)
                final_context = summarized

                if self.redis:
                    try:
                        self.redis.setex(
                            f"{self.REDIS_KEY_PREFIX}:{conversation_id}",
                            self.REDIS_TTL_SECONDS,
                            json.dumps(final_context),
                        )
                    except Exception as e:
                        self.logger.warning(
                            "Redis set after summarization failed",
                            error=str(e),
                            conversation_id=conversation_id,
                        )
            except Exception as e:
                self.logger.warning(
                    "Auto-summarization failed, keeping full context",
                    error=str(e),
                    conversation_id=conversation_id,
                )

        return final_context

    async def should_summarize(self, context: dict[str, Any]) -> bool:
        turn_count = context.get("turn_count", 0)

        # Guard: don't summarize empty/new contexts (turn_count == 0)
        if turn_count == 0:
            return False

        # Trigger 1: Every 5 turns
        if turn_count % self.SUMMARIZE_TURNS_TRIGGER == 0:
            return True

        # Trigger 2: Context size > 1KB
        context_size = len(json.dumps(context).encode("utf-8"))
        if context_size > self.SUMMARIZE_SIZE_TRIGGER_BYTES:
            return True

        return False

    async def summarize_context(
        self,
        conversation_id: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from app.services.context_summarizer import ContextSummarizerService

        summarizer = ContextSummarizerService(db=self.db)

        summary = await summarizer.summarize_context(
            context=context,
            conversation_id=conversation_id,
        )

        return summary

    async def delete_context(self, conversation_id: int) -> None:
        # Delete from Redis
        if self.redis:
            try:
                self.redis.delete(f"{self.REDIS_KEY_PREFIX}:{conversation_id}")
            except Exception as e:
                self.logger.warning(
                    "Redis delete failed", error=str(e), conversation_id=conversation_id
                )

        # Delete from PostgreSQL (single query)
        result = await self.db.execute(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        context_model = result.scalar_one_or_none()

        if context_model:
            await self.db.delete(context_model)
            await self.db.commit()

            self.logger.info("Context deleted", conversation_id=conversation_id)

    def _get_extractor(self, mode: ModeType) -> EcommerceContextExtractor | GeneralContextExtractor:
        if mode == "ecommerce":
            return EcommerceContextExtractor()
        elif mode == "general":
            return GeneralContextExtractor()
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def _log_constraint_changes(
        self,
        old_context: dict[str, Any],
        new_context: dict[str, Any],
        conversation_id: int,
    ) -> None:
        """Log constraint contradictions for analytics (AC7).

        Tracks when numeric constraints change (e.g., budget $50 -> $100).
        Applies last-mentioned-wins rule and logs for analytics.
        """
        old_constraints = old_context.get("constraints") or {}
        new_constraints = new_context.get("constraints") or {}

        numeric_keys = {"budget_max", "budget_min"}
        for key in numeric_keys:
            old_val = old_constraints.get(key)
            new_val = new_constraints.get(key)
            if old_val is not None and new_val is not None and old_val != new_val:
                self.logger.info(
                    "Constraint contradiction detected",
                    conversation_id=conversation_id,
                    constraint_key=key,
                    old_value=old_val,
                    new_value=new_val,
                    resolution="last_mentioned_wins",
                )

        preference_keys = {"color", "brand", "size"}
        for key in preference_keys:
            old_val = old_constraints.get(key)
            new_val = new_constraints.get(key)
            if old_val is not None and new_val is not None and old_val != new_val:
                self.logger.info(
                    "Preference changed",
                    conversation_id=conversation_id,
                    preference_key=key,
                    old_value=old_val,
                    new_value=new_val,
                    resolution="last_mentioned_wins",
                )

    async def _persist_to_db(
        self,
        conversation_id: int,
        merchant_id: int,
        context: dict[str, Any],
    ) -> None:
        result = await self.db.execute(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        context_model = result.scalar_one_or_none()

        if context_model:
            context_model.context_data = context
            context_model.turn_count = context.get("turn_count", 0)
            context_model.updated_at = datetime.now(timezone.utc)

            if context.get("mode") == "ecommerce":
                context_model.viewed_products = context.get("viewed_products")
                context_model.cart_items = context.get("cart_items")
                context_model.dismissed_products = context.get("dismissed_products")
                context_model.constraints = context.get("constraints")
                context_model.search_history = context.get("search_history")
            elif context.get("mode") == "general":
                context_model.topics_discussed = context.get("topics_discussed")
                context_model.documents_referenced = context.get("documents_referenced")
                context_model.support_issues = context.get("support_issues")
                context_model.escalation_status = context.get("escalation_status")

        else:
            context_model = ConversationContext(
                conversation_id=conversation_id,
                merchant_id=merchant_id,
                mode=context.get("mode", "ecommerce"),
                context_data=context,
                turn_count=context.get("turn_count", 0),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )

            if context.get("mode") == "ecommerce":
                context_model.viewed_products = context.get("viewed_products")
                context_model.cart_items = context.get("cart_items")
                context_model.dismissed_products = context.get("dismissed_products")
                context_model.constraints = context.get("constraints")
                context_model.search_history = context.get("search_history")
            elif context.get("mode") == "general":
                context_model.topics_discussed = context.get("topics_discussed")
                context_model.documents_referenced = context.get("documents_referenced")
                context_model.support_issues = context.get("support_issues")
                context_model.escalation_status = context.get("escalation_status")

            self.db.add(context_model)

        await self.db.commit()

    def _model_to_dict(self, model: ConversationContext) -> dict[str, Any]:
        context = {
            "mode": model.mode,
            "turn_count": model.turn_count,
            "expires_at": model.expires_at.isoformat(),
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "last_summarized_at": model.last_summarized_at.isoformat()
            if model.last_summarized_at
            else None,
            "preferences": model.preferences if model.preferences else None,
        }

        if model.mode == "ecommerce":
            if model.viewed_products:
                context["viewed_products"] = model.viewed_products
            if model.cart_items:
                context["cart_items"] = model.cart_items
            if model.dismissed_products:
                context["dismissed_products"] = model.dismissed_products
            if model.constraints:
                context["constraints"] = model.constraints
            if model.search_history:
                context["search_history"] = model.search_history

        elif model.mode == "general":
            if model.topics_discussed:
                context["topics_discussed"] = model.topics_discussed
            if model.documents_referenced:
                context["documents_referenced"] = model.documents_referenced
            if model.support_issues:
                context["support_issues"] = model.support_issues
            if model.escalation_status:
                context["escalation_status"] = model.escalation_status

        return context
