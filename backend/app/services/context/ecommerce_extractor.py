"""E-commerce mode context extractor.

Story 11-1: Conversation Context Memory
Extracts e-commerce specific context: products, prices, constraints, cart items.
"""

from __future__ import annotations

import re
from typing import Any

from app.services.context.base import BaseContextExtractor
from app.services.intent.variation_maps import ALL_BRANDS as _VARIATION_BRANDS


class EcommerceContextExtractor(BaseContextExtractor):
    """Extract context for e-commerce mode conversations.

    Tracks:
    - Products viewed/mentioned
    - Price constraints (budget max/min)
    - Size, color, brand preferences
    - Cart items
    - Search history
    """

    async def extract(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract e-commerce context from user message.

        Args:
            message: User message to analyze
            context: Current conversation context

        Returns:
            Updated context with extracted information
        """
        updates = {}

        products = self._extract_product_ids(message)
        if products:
            updates["viewed_products"] = products

        price_constraints = self._extract_price_constraints(message)
        if price_constraints:
            if "constraints" not in updates:
                updates["constraints"] = {}
            updates["constraints"].update(price_constraints)

        preferences = self._extract_preferences(message)
        if preferences:
            if "constraints" not in updates:
                updates["constraints"] = {}
            updates["constraints"].update(preferences)

        cart_items = self._extract_cart_mentions(message)
        if cart_items:
            updates["cart_items"] = cart_items

        dismissed = self._extract_dismissals(message, context)
        if dismissed:
            updates["dismissed_products"] = dismissed

        updates["search_history"] = [message]

        updates["turn_count"] = context.get("turn_count", 0) + 1

        return updates

    def _extract_product_ids(self, message: str) -> list[int] | None:
        """Extract product IDs from message.

        Looks for patterns like #123, product-123, etc.

        Args:
            message: User message

        Returns:
            List of product IDs or None
        """
        # Pattern: #123 or product-123
        pattern = r"(?:#|product\-)(\d+)"
        matches = re.findall(pattern, message, re.IGNORECASE)

        if matches:
            return [int(match) for match in matches]
        return None

    def _extract_price_constraints(self, message: str) -> dict[str, Any] | None:
        """Extract price constraints from message.

        Looks for patterns like "under $100", "max 50", etc.

        Args:
            message: User message

        Returns:
            Dictionary with budget_max/budget_min or None
        """
        constraints = {}

        # Pattern: "under $100", "max $50", "below 100"
        under_pattern = r"(?:under|max|below|less than)[\s\$]+(\d+(?:\.\d{2})?)"
        under_match = re.search(under_pattern, message, re.IGNORECASE)
        if under_match:
            constraints["budget_max"] = float(under_match.group(1))

        # Pattern: "over $50", "min $20", "above 20"
        over_pattern = r"(?:over|min|above|more than)[\s\$]+(\d+(?:\.\d{2})?)"
        over_match = re.search(over_pattern, message, re.IGNORECASE)
        if over_match:
            constraints["budget_min"] = float(over_match.group(1))

        # Pattern: "around $100" (range)
        around_pattern = r"(?:around|about)[\s\$]+(\d+(?:\.\d{2})?)"
        around_match = re.search(around_pattern, message, re.IGNORECASE)
        if around_match:
            price = float(around_match.group(1))
            constraints["budget_min"] = price * 0.8
            constraints["budget_max"] = price * 1.2

        return constraints if constraints else None

    def _extract_preferences(self, message: str) -> dict[str, Any] | None:
        """Extract size, color, brand preferences from message.

        Args:
            message: User message

        Returns:
            Dictionary with preferences or None
        """
        preferences = {}
        message_lower = message.lower()

        # Size patterns: "size 10", "size M", "10.5"
        size_pattern = r"\bsize[\s]+([a-zA-Z0-9\.]+)\b"
        size_match = re.search(size_pattern, message, re.IGNORECASE)
        if size_match:
            preferences["size"] = size_match.group(1).strip()

        # Color patterns
        colors = [
            "red",
            "blue",
            "green",
            "yellow",
            "black",
            "white",
            "pink",
            "purple",
            "orange",
            "brown",
            "gray",
            "grey",
        ]
        for color in colors:
            if re.search(rf"\b{re.escape(color)}\b", message_lower):
                preferences["color"] = color
                break

        # Brand patterns (simple keyword matching)
        for brand in sorted(_VARIATION_BRANDS, key=len, reverse=True):
            if re.search(rf"\b{re.escape(brand)}\b", message_lower):
                preferences["brand"] = brand.title()
                break

        return preferences if preferences else None

    def _extract_cart_mentions(self, message: str) -> list[int] | None:
        """Extract cart item mentions from message.

        Args:
            message: User message

        Returns:
            List of product IDs in cart or None
        """
        cart_pattern = r"(?:add|cart|basket)[\s\w]+(?:#|product\-)(\d+)"
        matches = re.findall(cart_pattern, message, re.IGNORECASE)

        if matches:
            return [int(match) for match in matches]
        return None

    def _extract_dismissals(self, message: str, context: dict[str, Any]) -> list[int] | None:
        """Extract product dismissals from message (Story 11-6).

        Detects phrases like "don't show me that", "not interested",
        "don't like", "no thanks", "skip", "next" referring to a product.

        Args:
            message: User message
            context: Current conversation context (for resolving product references)

        Returns:
            List of product IDs to dismiss, or None
        """
        lower = message.lower().strip()

        dismissal_phrases = [
            r"don'?t\s+(?:show|recommend|suggest)\s+me",
            r"not\s+interested",
            r"don'?t\s+like",
            r"no\s+thanks",
            r"skip\s+(?:that|this|it)",
            r"not\s+(?:for\s+me|my\s+style)",
            r"nope",
            r"nah",
            r"never\s+mind",
            r"forget\s+(?:about\s+)?(?:that|this|it)",
            r"something\s+else",
            r"anything\s+else",
            r"next",
            r"no\s+(?:more|longer)",
        ]

        is_dismissal = any(re.search(phrase, lower) for phrase in dismissal_phrases)
        if not is_dismissal:
            return None

        dismissed_ids: list[int] = []

        viewed = context.get("last_viewed_products") or []
        if viewed:
            dismissed_ids.append(viewed[0].get("id")) if viewed and isinstance(
                viewed[0], dict
            ) else None

        product_ids = self._extract_product_ids(message)
        if product_ids:
            dismissed_ids.extend(product_ids)

        existing_dismissed = context.get("dismissed_products") or []
        dismissed_ids = list(
            set(existing_dismissed + [pid for pid in dismissed_ids if pid is not None])
        )

        return dismissed_ids if dismissed_ids else None
