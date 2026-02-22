"""Product Mention Detector for auto-product card generation.

Detects when LLM responses mention products and automatically
fetches matching products to display as product cards.
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm.base_llm_service import BaseLLMService, LLMMessage
from app.services.shopify.product_search_service import ProductSearchService
from app.services.intent.classification_schema import ExtractedEntities


logger = structlog.get_logger(__name__)


PRODUCT_MENTION_DETECTION_PROMPT = """You analyze chatbot responses to detect product mentions.

Given a chatbot's response, identify any product names or items mentioned that the user might want to see.

Rules:
1. Only extract ACTUAL product names (specific items the store sells)
2. Ignore generic terms like "products", "items", "our selection"
3. If the response is about a general topic without mentioning specific products, return empty array
4. Be conservative - only extract when confident

Return JSON:
{
    "product_mentions": ["Product Name 1", "Product Name 2"],
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}

Examples:

Response: "Yes, we have the Nike Air Max in stock! They're $129 and come in several colors."
Output: {"product_mentions": ["Nike Air Max"], "confidence": 0.95, "reasoning": "Specific product name mentioned"}

Response: "We have a great selection of running shoes. Check out our catalog!"
Output: {"product_mentions": [], "confidence": 0.90, "reasoning": "No specific product names, just category"}

Response: "The Espresso Blend and Colombian Roast are our bestsellers."
Output: {"product_mentions": ["Espresso Blend", "Colombian Roast"], "confidence": 0.92, "reasoning": "Two specific products mentioned"}

Response: "Our hours are 9am to 6pm weekdays."
Output: {"product_mentions": [], "confidence": 1.0, "reasoning": "No products mentioned, just business info"}

Response: "I'd recommend the Winter Jacket - it's perfect for cold weather and only $89."
Output: {"product_mentions": ["Winter Jacket"], "confidence": 0.90, "reasoning": "Specific product recommended"}
"""


class ProductMentionDetector:
    """Detects product mentions in LLM responses and fetches matching products.

    When the LLM generates a general response that happens to mention
    specific products, this detector can automatically find and return
    those products as cards.
    """

    def __init__(self, llm_service: BaseLLMService):
        """Initialize detector with LLM service.

        Args:
            llm_service: LLM service for product mention detection
        """
        self.llm_service = llm_service
        self.logger = structlog.get_logger(__name__)

    async def detect_and_fetch(
        self,
        response_text: str,
        merchant_id: int,
        db: AsyncSession,
        max_products: int = 3,
    ) -> Optional[list[dict[str, Any]]]:
        """Detect product mentions and fetch matching products.

        Args:
            response_text: The LLM response text to analyze
            merchant_id: Merchant ID for product search
            db: Database session
            max_products: Maximum number of products to return

        Returns:
            List of product dicts if mentions found, None otherwise
        """
        start_time = time.time()

        try:
            mentions = await self._detect_mentions(response_text)

            if not mentions or not mentions.get("product_mentions"):
                return None

            product_names = mentions["product_mentions"]
            confidence = mentions.get("confidence", 0.0)

            self.logger.debug(
                "product_mentions_detected",
                merchant_id=merchant_id,
                mentions=product_names,
                confidence=confidence,
            )

            if confidence < 0.7:
                return None

            products = await self._fetch_products_by_names(
                product_names=product_names,
                merchant_id=merchant_id,
                db=db,
                max_products=max_products,
            )

            processing_time = (time.time() - start_time) * 1000
            self.logger.info(
                "product_mention_detection_complete",
                merchant_id=merchant_id,
                mentions_count=len(product_names),
                products_found=len(products) if products else 0,
                processing_time_ms=processing_time,
            )

            return products if products else None

        except Exception as e:
            self.logger.warning(
                "product_mention_detection_failed",
                merchant_id=merchant_id,
                error=str(e),
            )
            return None

    async def _detect_mentions(self, response_text: str) -> Optional[dict[str, Any]]:
        """Use LLM to detect product mentions in response.

        Args:
            response_text: Response text to analyze

        Returns:
            Dict with product_mentions list and confidence
        """
        try:
            messages = [
                LLMMessage(role="system", content=PRODUCT_MENTION_DETECTION_PROMPT),
                LLMMessage(role="user", content=f"Response: {response_text}"),
            ]

            response = await self.llm_service.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=200,
            )

            json_str = response.content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            return json.loads(json_str)

        except Exception as e:
            self.logger.warning(
                "mention_detection_parse_failed",
                error=str(e),
            )
            return None

    async def _fetch_products_by_names(
        self,
        product_names: list[str],
        merchant_id: int,
        db: AsyncSession,
        max_products: int,
    ) -> list[dict[str, Any]]:
        """Fetch products matching the mentioned names.

        Args:
            product_names: List of product names to search for
            merchant_id: Merchant ID
            db: Database session
            max_products: Maximum products to return

        Returns:
            List of product dicts
        """
        search_service = ProductSearchService(db=db)
        found_products = []

        for name in product_names[:max_products]:
            try:
                entities = ExtractedEntities(category=name)
                result = await search_service.search_products(
                    entities=entities,
                    merchant_id=merchant_id,
                )

                if result.products:
                    best_match = result.products[0]
                    found_products.append(
                        {
                            "id": best_match.id,
                            "product_id": best_match.id,
                            "variant_id": str(best_match.variants[0].id)
                            if best_match.variants
                            else None,
                            "title": best_match.title,
                            "price": float(best_match.price) if best_match.price else None,
                            "currency": str(best_match.currency_code)
                            if best_match.currency_code
                            else "USD",
                            "image_url": best_match.images[0].url if best_match.images else None,
                            "available": (
                                any(v.available_for_sale for v in best_match.variants)
                                if best_match.variants
                                else True
                            ),
                        }
                    )

                    if len(found_products) >= max_products:
                        break

            except Exception as e:
                self.logger.warning(
                    "product_fetch_by_name_failed",
                    product_name=name,
                    error=str(e),
                )

        return found_products
