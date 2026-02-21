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

            # Check if this is a recommendation/pinned product request
            constraints = entities.get("constraints", {}) if entities else {}
            is_pinned_request = constraints.get("pinned", False)

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
                    constraints=constraints,
                )

            # For pinned/recommendation requests, get pinned products first
            if is_pinned_request:
                search_result = await self._get_pinned_products(
                    db=db,
                    merchant=merchant,
                    search_service=search_service,
                    extracted_entities=extracted_entities,
                )
            else:
                search_result = await ShopifyCircuitBreaker.execute(
                    merchant.id,
                    search_service.search_products,
                    extracted_entities,
                    merchant.id,
                )

            if not search_result.products:
                return await self._handle_no_results_with_fallback(
                    db=db,
                    merchant=merchant,
                    search_service=search_service,
                    original_query=message,
                    entities=entities,
                )

            formatted_products = [
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
                }
                for p in search_result.products[:5]
            ]

            # Use recommendation message format for pinned requests
            if is_pinned_request:
                response_message = self._format_recommendation_message(
                    formatted_products,
                    search_result.total_count,
                    merchant,
                )
            else:
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

    async def _handle_no_results_with_fallback(
        self,
        db: AsyncSession,
        merchant: Merchant,
        search_service,
        original_query: str,
        entities: dict | None,
    ) -> ConversationResponse:
        """Handle no results by showing featured products as fallback.

        Args:
            db: Database session
            merchant: Merchant configuration
            search_service: Product search service
            original_query: The user's original search query
            entities: Extracted entities from intent

        Returns:
            ConversationResponse with featured products or no-results message
        """
        from app.services.intent.classification_schema import ExtractedEntities

        try:
            fallback_entities = ExtractedEntities(
                constraints={"pinned": True, "sort_by": "relevance"}
            )
            fallback_result = await self._get_pinned_products(
                db=db,
                merchant=merchant,
                search_service=search_service,
                extracted_entities=fallback_entities,
            )

            if fallback_result and fallback_result.products:
                formatted_products = [
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
                    }
                    for p in fallback_result.products[:5]
                ]

                category = entities.get("category") if entities else None
                query_term = category or original_query
                message = self._format_fallback_message(
                    query_term=query_term,
                    products=formatted_products,
                    merchant=merchant,
                )

                logger.info(
                    "search_fallback_to_featured",
                    merchant_id=merchant.id,
                    original_query=original_query,
                    fallback_count=len(formatted_products),
                )

                return ConversationResponse(
                    message=message,
                    intent="product_search",
                    confidence=1.0,
                    products=formatted_products,
                    metadata={"fallback": True, "original_query": original_query},
                )

        except Exception as e:
            logger.warning(
                "search_fallback_failed",
                merchant_id=merchant.id,
                error=str(e),
            )

        return ConversationResponse(
            message=self._format_no_results_message(original_query, merchant),
            intent="product_search",
            confidence=1.0,
            products=[],
        )

    def _format_fallback_message(
        self,
        query_term: str,
        products: list[dict],
        merchant: Merchant,
    ) -> str:
        """Format message when showing fallback products.

        Args:
            query_term: The product term the user searched for
            products: List of fallback products
            merchant: Merchant configuration

        Returns:
            Formatted message string
        """
        business_name = merchant.business_name or "our store"

        lines = [
            f"I don't have {query_term} at {business_name}, but here are some popular items:\n"
        ]

        for p in products[:5]:
            price_str = f" - ${p['price']:.2f}" if p.get("price") else ""
            lines.append(f"• {p['title']}{price_str}")

        lines.append("\nWould you like more details on any of these?")
        return "\n".join(lines)

    def _format_no_results_message(self, query: str, merchant: Merchant) -> str:
        """Format message when no products found."""
        business_name = merchant.business_name or "our store"
        return (
            f"I couldn't find any products matching '{query}' at {business_name}. "
            "Try a different search term or ask me what we have available!"
        )

    def _format_recommendation_message(
        self,
        products: list[dict],
        total_count: int,
        merchant: Merchant,
    ) -> str:
        """Format message for product recommendations.

        Args:
            products: List of recommended products
            total_count: Total number of products available
            merchant: Merchant configuration

        Returns:
            Formatted recommendation message
        """
        business_name = merchant.business_name or "our store"

        if len(products) == 1:
            p = products[0]
            price_str = f" (${p['price']:.2f})" if p.get("price") else ""
            return f"My top pick at {business_name}:\n\n• {p['title']}{price_str}"

        lines = [f"Here are my recommendations from {business_name}:\n"]
        for i, p in enumerate(products[:5], 1):
            price_str = f" - ${p['price']:.2f}" if p.get("price") else ""
            lines.append(f"{i}. {p['title']}{price_str}")

        if total_count > 5:
            lines.append(f"\nWant to see more options?")

        return "\n".join(lines)

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

    async def _get_pinned_products(
        self,
        db: AsyncSession,
        merchant: Merchant,
        search_service,
        extracted_entities,
    ):
        """Get pinned products for recommendations.

        Args:
            db: Database session
            merchant: Merchant configuration
            search_service: Product search service
            extracted_entities: Extracted entities from intent

        Returns:
            ProductSearchResult with pinned products
        """
        from app.services.product_pin_service import get_pinned_product_ids
        from app.schemas.shopify import ProductSearchResult

        try:
            # Get pinned product IDs (merchant_id is int, not string)
            pinned_ids = await get_pinned_product_ids(db, merchant.id)

            if not pinned_ids:
                # No pinned products, fall back to regular search
                logger.info("no_pinned_products_fallback", merchant_id=merchant.id)
                return await search_service.search_products(extracted_entities, merchant.id)

            # Convert pinned IDs to strings for comparison
            pinned_ids_str = {str(pid) for pid in pinned_ids}
            logger.info("pinned_ids_found", merchant_id=merchant.id, pinned_count=len(pinned_ids))

            # Fetch all products and filter to pinned ones
            result = await search_service.search_products(extracted_entities, merchant.id)

            # Filter to only pinned products (compare as strings)
            pinned_products = [p for p in result.products if str(p.id) in pinned_ids_str]

            logger.info(
                "pinned_filter_results",
                merchant_id=merchant.id,
                total_products=len(result.products),
                pinned_found=len(pinned_products),
            )

            if pinned_products:
                # Update result to only include pinned products
                result.products = pinned_products[:5]
                result.total_count = len(pinned_products)
            else:
                # No pinned products found in search results, return regular results
                pass

            return result
        except Exception as e:
            logger.warning("pinned_products_failed", merchant_id=merchant.id, error=str(e))
            # Fall back to regular search
            return await search_service.search_products(extracted_entities, merchant.id)
