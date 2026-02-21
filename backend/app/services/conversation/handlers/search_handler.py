"""Search handler for unified conversation processing.

Story 5-10: Widget Full App Integration
Task 1: Create UnifiedConversationService
Task 15: Circuit Breaker for Shopify

Handles PRODUCT_SEARCH intent with Shopify Admin API integration.
Implements circuit breaker for resilience.
"""

from __future__ import annotations

from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.services.conversation.schemas import (
    ConversationContext,
    ConversationResponse,
)
from app.services.conversation.handlers.base_handler import BaseHandler
from app.services.llm.base_llm_service import BaseLLMService
from app.services.shopify.circuit_breaker import (
    CircuitOpenError,
    ShopifyCircuitBreaker,
)


logger = structlog.get_logger(__name__)


class SearchHandler(BaseHandler):
    """Handler for PRODUCT_SEARCH intent.

    Searches products using Shopify Admin API and returns
    formatted results with images, titles, and prices.
    """

    async def handle(
        self,
        db: AsyncSession,
        merchant: Merchant,
        llm_service: BaseLLMService,
        message: str,
        context: ConversationContext,
        entities: Optional[dict[str, Any]] = None,
    ) -> ConversationResponse:
        """Handle product search intent.

        Args:
            db: Database session
            merchant: Merchant configuration
            llm_service: LLM service for this merchant
            message: User's message
            context: Conversation context
            entities: Extracted entities (category, budget, etc.)

        Returns:
            ConversationResponse with product results
        """
        try:
            from app.services.shopify.product_search_service import ProductSearchService
            from app.services.intent.classification_schema import ExtractedEntities

            search_service = ProductSearchService(db=db)

            extracted_entities = ExtractedEntities()
            if entities:
                extracted_entities = ExtractedEntities(
                    category=entities.get("category"),
                    budget=entities.get("budget"),
                    budget_currency=entities.get("budget_currency", "USD"),
                    size=entities.get("size"),
                    color=entities.get("color"),
                    brand=entities.get("brand"),
                    constraints=entities.get("constraints", {}),
                )

            search_result = await ShopifyCircuitBreaker.execute(
                merchant.id,
                search_service.search_products,
                merchant.id,
                extracted_entities,
                message,
            )

            if not search_result.products:
                return ConversationResponse(
                    message=self._format_no_results_message(message, merchant),
                    intent="product_search",
                    confidence=1.0,
                    products=[],
                )

            formatted_products = [
                {
                    "product_id": p.id,
                    "title": p.title,
                    "price": float(p.price) if p.price else None,
                    "currency": p.currency_code or "USD",
                    "image_url": p.image_url,
                    "available": p.available,
                }
                for p in search_result.products[:5]
            ]

            response_message = self._format_results_message(
                formatted_products,
                search_result.total_count,
                merchant,
            )

            logger.info(
                "search_handler_success",
                merchant_id=merchant.id,
                total_results=search_result.total_count,
                returned_count=len(formatted_products),
            )

            return ConversationResponse(
                message=response_message,
                intent="product_search",
                confidence=1.0,
                products=formatted_products,
                metadata={"total_count": search_result.total_count},
            )

        except CircuitOpenError as e:
            logger.warning(
                "search_circuit_open",
                merchant_id=merchant.id,
                retry_after=e.retry_after,
            )
            return ConversationResponse(
                message=ShopifyCircuitBreaker.get_fallback_message(merchant),
                intent="product_search",
                confidence=1.0,
                fallback=True,
                fallback_url=ShopifyCircuitBreaker.get_fallback_url(merchant),
                metadata={"circuit_open": True},
            )

        except Exception as e:
            logger.error(
                "search_handler_failed",
                merchant_id=merchant.id,
                error=str(e),
            )
            return ConversationResponse(
                message="I had trouble searching for products. Please try again or ask me about something else!",
                intent="product_search",
                confidence=1.0,
                fallback=True,
            )

    def _format_no_results_message(self, query: str, merchant: Merchant) -> str:
        """Format message when no products found."""
        business_name = merchant.business_name or "our store"
        return (
            f"I couldn't find any products matching '{query}' at {business_name}. "
            "Try a different search term or ask me what we have available!"
        )

    def _format_results_message(
        self,
        products: list[dict],
        total_count: int,
        merchant: Merchant,
    ) -> str:
        """Format message with product results."""
        business_name = merchant.business_name or "our store"

        if len(products) == 1:
            p = products[0]
            price_str = f" (${p['price']:.2f})" if p.get("price") else ""
            return f"I found this at {business_name}:\n\n• {p['title']}{price_str}"

        lines = [f"Here's what I found at {business_name}:\n"]
        for p in products[:5]:
            price_str = f" - ${p['price']:.2f}" if p.get("price") else ""
            lines.append(f"• {p['title']}{price_str}")

        if total_count > 5:
            lines.append(f"\n...and {total_count - 5} more. Want me to show you more?")

        return "\n".join(lines)
