"""Recommendation handler for contextual product recommendations (Story 11-6).

Handles PRODUCT_RECOMMENDATION intent with context-aware scoring.
"""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.llm.base_llm_service import BaseLLMService
from app.services.personality.response_formatter import PersonalityAwareResponseFormatter
from app.services.recommendation.contextual_recommendation_service import (
    ContextualRecommendationService,
)
from app.services.recommendation.explanation_generator import ExplanationGenerator
from app.services.recommendation.schemas import RecommendationScore

logger = structlog.get_logger(__name__)


class RecommendationHandler(BaseHandler):
    _MODE = "ecommerce"

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: dict[str, Any] | None = None,
    ) -> ConversationResponse:
        if merchant.onboarding_mode != "ecommerce":
            return self._general_mode_fallback(merchant)

        try:
            products = await self._fetch_products(db, merchant)
        except Exception as e:
            logger.error(
                "recommendation_product_fetch_failed", merchant_id=merchant.id, error=str(e)
            )
            from app.services.conversation.error_recovery_service import (
                ErrorType,
                NaturalErrorRecoveryService,
            )

            return await NaturalErrorRecoveryService().recover(
                error_type=ErrorType.SEARCH_FAILED,
                merchant=merchant,
                context=context,
                error=e,
                intent="product_recommendation",
                conversation_id=str(context.session_id),
            )

        context_data = await self._load_context_data(db, context)
        shopping_state = context.shopping_state.model_dump() if context.shopping_state else {}

        dismissed_from_context = context_data.get("dismissed_products") or []
        if dismissed_from_context and context.shopping_state:
            context.shopping_state.dismissed_product_ids = [
                pid for pid in dismissed_from_context if isinstance(pid, int)
            ]
            shopping_state["dismissed_product_ids"] = context.shopping_state.dismissed_product_ids

        rec_service = ContextualRecommendationService()
        result = rec_service.generate_recommendations(
            products=products,
            context_data=context_data,
            shopping_state=shopping_state,
        )

        if result.empty:
            return self._empty_set_fallback(merchant, context)

        recommendations = result.recommendations

        explanations: list[str] = []
        for rec in recommendations:
            explanation = self._build_explanation(rec, merchant)
            explanations.append(explanation)

        formatted_products = self._format_products(recommendations, merchant)

        response_message = self._format_recommendation_message(
            formatted_products, explanations, merchant, context
        )

        logger.info(
            "recommendation_handler_success",
            merchant_id=merchant.id,
            recommendation_count=len(recommendations),
            total_candidates=result.total_candidates,
        )

        return ConversationResponse(
            message=response_message,
            intent="product_recommendation",
            confidence=1.0,
            products=formatted_products,
            metadata={
                "total_candidates": result.total_candidates,
                "filtered_out": result.filtered_out,
                "context_aware": True,
            },
        )

    async def _fetch_products(self, db: AsyncSession, merchant: Merchant) -> list:
        from app.services.shopify_admin import ShopifyAdminClient

        admin_client = await ShopifyAdminClient.create(db, merchant.id)
        return await admin_client.list_products(merchant.id)

    async def _load_context_data(
        self, db: AsyncSession, context: ConversationContext
    ) -> dict[str, Any]:
        from app.services.conversation_context import ConversationContextService

        if context.conversation_id:
            service = ConversationContextService(db)
            ctx = await service.get_context(context.conversation_id)
            if ctx:
                return ctx
        return {
            "viewed_products": [],
            "cart_items": [],
            "dismissed_products": [],
            "constraints": {},
        }

    def _build_explanation(self, rec: RecommendationScore, merchant: Merchant) -> str:
        from app.models.merchant import PersonalityType

        personality = getattr(merchant, "personality", PersonalityType.FRIENDLY)
        if isinstance(personality, str):
            personality = PersonalityType(personality)
        reason_parts = rec.reason.split("||") if rec.reason else []
        reason_type = "default"
        template_vars: dict[str, str] = {}
        for part in reason_parts:
            if ":" not in part:
                continue
            key, value = part.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "brand_match":
                reason_type = "brand_match" if reason_type == "default" else "multi_match"
                template_vars["brand"] = value
            elif key == "budget_match":
                reason_type = "budget_match" if reason_type == "default" else "multi_match"
                template_vars["budget"] = value
            elif key in ("feature_match", "category_match"):
                reason_type = key if reason_type == "default" else "multi_match"
                template_vars["feature"] = value
                template_vars["category"] = value
            elif key == "novelty":
                if reason_type == "default":
                    reason_type = "novelty"
        if reason_type == "multi_match" and len(reason_parts) > 1:
            reasons_list = [p.split(":", 1)[1].strip() for p in reason_parts if ":" in p]
            template_vars["reasons"] = ", ".join(reasons_list)
        return ExplanationGenerator.generate_explanation(
            reason=rec.reason,
            reason_type=reason_type,
            personality=personality,
            **template_vars,
        )

    def _format_products(
        self, recommendations: list[RecommendationScore], merchant: Merchant
    ) -> list[dict[str, Any]]:
        formatted = []
        for rec in recommendations:
            p = rec.product
            formatted.append(
                {
                    "id": p.id,
                    "product_id": p.id,
                    "variant_id": str(p.variants[0].id) if p.variants else None,
                    "title": p.title,
                    "price": float(p.price) if p.price else None,
                    "currency": str(p.currency_code) if p.currency_code else "USD",
                    "image_url": p.images[0].url if p.images else None,
                    "available": (
                        any(v.available_for_sale for v in p.variants) if p.variants else True
                    ),
                    "context_aware": True,
                }
            )
        return formatted

    def _format_recommendation_message(
        self,
        products: list[dict[str, Any]],
        explanations: list[str],
        merchant: Merchant,
        context: ConversationContext,
    ) -> str:
        business_name = merchant.business_name or "our store"
        conversation_id = str(context.session_id) if context else None
        mode = getattr(merchant, "onboarding_mode", None) or "ecommerce"
        personality = merchant.personality

        if len(products) == 1:
            p = products[0]
            price_str = f" (${p['price']:.2f})" if p.get("price") else ""
            reason = explanations[0] if explanations else ""
            return PersonalityAwareResponseFormatter.format_response(
                "product_search",
                "recommendation_single",
                personality,
                include_transition=True,
                conversation_id=conversation_id,
                mode=mode,
                business_name=business_name,
                title=p["title"],
                price=price_str,
                reason=reason,
            )

        product_lines = []
        for i, p in enumerate(products[:5], 1):
            price_str = f" - ${p['price']:.2f}" if p.get("price") else ""
            reason = explanations[i - 1] if i - 1 < len(explanations) else ""
            product_lines.append(f"{i}. {p['title']}{price_str}")
            if reason:
                product_lines.append(f"   _{reason}_")
        products_str = "\n".join(product_lines)

        return PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "recommendation_multiple",
            personality,
            include_transition=True,
            conversation_id=conversation_id,
            mode=mode,
            business_name=business_name,
            products=products_str,
            more_options="",
        )

    def _empty_set_fallback(
        self, merchant: Merchant, context: ConversationContext
    ) -> ConversationResponse:
        conversation_id = str(context.session_id) if context else None
        mode = getattr(merchant, "onboarding_mode", None) or "ecommerce"
        personality = merchant.personality

        message = PersonalityAwareResponseFormatter.format_response(
            "product_search",
            "no_results",
            personality,
            include_transition=True,
            conversation_id=conversation_id,
            mode=mode,
            query="matching your preferences",
        )
        return ConversationResponse(
            message=message,
            intent="product_recommendation",
            confidence=1.0,
            products=[],
            metadata={"empty_recommendation": True},
        )

    def _general_mode_fallback(self, merchant: Merchant) -> ConversationResponse:
        message = PersonalityAwareResponseFormatter.format_response(
            "general_mode_fallback",
            "ecommerce_not_supported",
            merchant.personality,
        )
        return ConversationResponse(
            message=message,
            intent="product_recommendation",
            confidence=1.0,
        )
