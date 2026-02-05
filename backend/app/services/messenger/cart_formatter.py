"""Cart Formatter Service for Facebook Messenger.

Formats shopping cart contents for display in Facebook Messenger using
Generic Template and Button Template structured messages.
"""

from __future__ import annotations

from typing import Any, Dict

import structlog

from app.core.config import settings
from app.schemas.cart import Cart, CartItem, CurrencyCode


class CartFormatter:
    """Format cart for Messenger display.

    Displays cart as:
    - Cart summary header (total items, subtotal)
    - Item list with images, titles, quantities, prices
    - Remove button per item
    - Quantity adjustment buttons (+/-)
    - Checkout and Continue Shopping buttons
    """

    MAX_QUANTITY = 10  # Maximum quantity per item (must match CartService)

    # Currency symbols for formatting
    CURRENCY_SYMBOLS: Dict[str, str] = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "CAD": "C$",
        "AUD": "A$"
    }

    # Default placeholder image when product image is unavailable
    DEFAULT_IMAGE_URL = "https://via.placeholder.com/300x300/CCCCCC/666666?text=No+Image"

    def __init__(self, shop_domain: str) -> None:
        """Initialize cart formatter.

        Args:
            shop_domain: Shopify store domain for product links
        """
        self.shop_domain = shop_domain
        self.logger = structlog.get_logger(__name__)

    def format_cart(self, cart: Cart, psid: str) -> Dict[str, Any]:
        """Format cart for Messenger display.

        Args:
            cart: Cart object with items and subtotal
            psid: Facebook Page-Scoped ID for button payloads

        Returns:
            Messenger message payload with cart display

        Raises:
            APIError: If formatting fails
        """
        if not cart.items:
            return self._format_empty_cart()

        elements: list[Dict[str, Any]] = []

        # Cart summary as first element
        summary_element = {
            "title": f"🛒 Your Cart ({cart.item_count} items)",
            "subtitle": f"Subtotal: {self._format_price(cart.subtotal, cart.currency_code.value)}",
            "image_url": None,  # No image for summary
            "default_action": {
                "type": "web_url",
                "url": f"https://{self.shop_domain}/cart",
                "webview_height_ratio": "tall",
            },
            "buttons": [
                {
                    "type": "postback",
                    "title": "🛍️ Continue Shopping",
                    "payload": "continue_shopping"
                },
                {
                    "type": "postback",
                    "title": "💳 Checkout",
                    "payload": "checkout"
                }
            ]
        }
        elements.append(summary_element)

        # Each cart item as an element
        for item in cart.items:
            element = self._format_cart_item(item, psid)
            elements.append(element)

        # Checkout reminder as last element
        checkout_element = {
            "title": "Ready to checkout?",
            "subtitle": f"Total: {self._format_price(cart.subtotal, cart.currency_code.value)}",
            "buttons": [
                {
                    "type": "postback",
                    "title": "💳 Proceed to Checkout",
                    "payload": "checkout"
                },
                {
                    "type": "postback",
                    "title": "🛍️ Continue Shopping",
                    "payload": "continue_shopping"
                }
            ]
        }
        elements.append(checkout_element)

        self.logger.info(
            "cart_formatted",
            item_count=cart.item_count,
            subtotal=cart.subtotal
        )

        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements,
                    "image_aspect_ratio": "square"
                },
            },
        }

    def _format_empty_cart(self) -> Dict[str, Any]:
        """Format empty cart message.

        Returns:
            Messenger message for empty cart
        """
        return {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "🛒 Your cart is empty.\n\nLet's find some products for you!",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "🛍️ Browse Products",
                            "payload": "browse_products"
                        },
                        {
                            "type": "postback",
                            "title": "🔍 Search Products",
                            "payload": "search_products"
                        }
                    ]
                }
            }
        }

    def _format_cart_item(self, item: CartItem, psid: str) -> Dict[str, Any]:
        """Format single cart item for display.

        Args:
            item: CartItem to format
            psid: Facebook Page-Scoped ID for button payloads

        Returns:
            Messenger element for cart item
        """
        # Remove button payload
        remove_payload = f"remove_item:{item.variant_id}"

        # Quantity adjustment payloads
        increase_payload = f"increase_quantity:{item.variant_id}"
        decrease_payload = f"decrease_quantity:{item.variant_id}"

        # Use default image if URL is empty
        image_url = item.image_url or self.DEFAULT_IMAGE_URL

        element: Dict[str, Any] = {
            "title": item.title,
            "subtitle": self._format_item_details(item),
            "image_url": image_url,
            "default_action": {
                "type": "web_url",
                "url": f"https://{self.shop_domain}/products/{item.product_id}",
                "webview_height_ratio": "tall",
            },
            "buttons": [
                {
                    "type": "postback",
                    "title": "➕ Increase",
                    "payload": increase_payload
                },
                {
                    "type": "postback",
                    "title": "➖ Decrease",
                    "payload": decrease_payload
                },
                {
                    "type": "postback",
                    "title": "🗑️ Remove",
                    "payload": remove_payload
                }
            ]
        }

        # Disable decrease button if quantity is 1
        if item.quantity <= 1:
            element["buttons"][1]["title"] = "➖ (Min)"

        # Disable increase button if at max quantity
        if item.quantity >= self.MAX_QUANTITY:
            element["buttons"][0]["title"] = "➕ (Max)"

        return element

    def _format_item_details(self, item: CartItem) -> str:
        """Format item details subtitle.

        Args:
            item: CartItem to format

        Returns:
            Formatted subtitle string
        """
        price = self._format_price(item.price, item.currency_code.value)
        quantity_str = f"Qty: {item.quantity}"
        total = self._format_price(
            item.price * item.quantity,
            item.currency_code.value
        )

        return f"{quantity_str} | {price} each | Total: {total}"

    def _format_price(self, amount: float, currency: str) -> str:
        """Format price with currency symbol.

        Args:
            amount: Price amount
            currency: Currency code (USD, EUR, etc.)

        Returns:
            Formatted price string
        """
        symbol = self.CURRENCY_SYMBOLS.get(currency, currency)
        return f"{symbol}{amount:.2f}"
