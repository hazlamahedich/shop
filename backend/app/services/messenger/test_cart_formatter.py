"""Tests for CartFormatter service.

Tests cart display formatting for Facebook Messenger including:
- Cart summary with total items and subtotal
- Item list with images, titles, quantities, prices
- Remove button per item
- Quantity adjustment buttons (+/-) with limits
- Empty cart handling
- Checkout and Continue Shopping buttons
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.schemas.cart import Cart, CartItem, CurrencyCode
from app.services.messenger.cart_formatter import CartFormatter


class TestCartFormatter:
    """Test suite for CartFormatter service."""

    @pytest.fixture
    def formatter(self) -> CartFormatter:
        """Create CartFormatter instance for testing."""
        return CartFormatter(shop_domain="example.myshopify.com")

    @pytest.fixture
    def sample_cart_items(self) -> list[CartItem]:
        """Create sample cart items for testing."""
        return [
            CartItem(
                product_id="prod_1",
                variant_id="var_1",
                title="Test Product 1",
                price=29.99,
                image_url="http://example.com/image1.jpg",
                quantity=2,
                currency_code=CurrencyCode.USD,
                added_at=datetime.now(timezone.utc).isoformat()
            ),
            CartItem(
                product_id="prod_2",
                variant_id="var_2",
                title="Test Product 2",
                price=49.99,
                image_url="http://example.com/image2.jpg",
                quantity=1,
                currency_code=CurrencyCode.USD,
                added_at=datetime.now(timezone.utc).isoformat()
            )
        ]

    @pytest.fixture
    def sample_cart(self, sample_cart_items: list[CartItem]) -> Cart:
        """Create sample cart for testing."""
        return Cart(
            items=sample_cart_items,
            subtotal=109.97,  # (29.99 * 2) + 49.99
            currency_code=CurrencyCode.USD,
            item_count=3,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat()
        )

    @pytest.fixture
    def empty_cart(self) -> Cart:
        """Create empty cart for testing."""
        return Cart(
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
            item_count=0
        )

    def test_format_cart_with_items(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test formatting cart with multiple items.

        Should include:
        - Cart summary element (total items, subtotal)
        - Individual item elements
        - Checkout reminder element
        """
        result = formatter.format_cart(sample_cart, "test_psid")

        assert "attachment" in result
        assert result["attachment"]["type"] == "template"
        assert result["attachment"]["payload"]["template_type"] == "generic"

        elements = result["attachment"]["payload"]["elements"]

        # Should have: summary + 2 items + checkout reminder = 4 elements
        assert len(elements) == 4

        # First element is cart summary
        assert "Your Cart" in elements[0]["title"]
        assert "3 items" in elements[0]["title"]
        assert "Subtotal" in elements[0]["subtitle"]
        assert "$109.97" in elements[0]["subtitle"]

        # Summary should have Continue Shopping and Checkout buttons
        summary_buttons = elements[0]["buttons"]
        assert len(summary_buttons) == 2
        button_titles = [b["title"] for b in summary_buttons]
        assert any("Continue Shopping" in title for title in button_titles)
        assert any("Checkout" in title for title in button_titles)

    def test_format_empty_cart(self, formatter: CartFormatter, empty_cart: Cart) -> None:
        """Test formatting empty cart.

        Should display friendly message with browse/search options.
        """
        result = formatter.format_cart(empty_cart, "test_psid")

        assert "attachment" in result
        assert result["attachment"]["type"] == "template"
        assert result["attachment"]["payload"]["template_type"] == "button"

        text = result["attachment"]["payload"]["text"]
        assert "Your cart is empty" in text
        assert "Let's find some products" in text

        # Should have Browse Products and Search Products buttons
        buttons = result["attachment"]["payload"]["buttons"]
        assert len(buttons) == 2
        button_payloads = [b["payload"] for b in buttons]
        assert "browse_products" in button_payloads
        assert "search_products" in button_payloads

    def test_cart_item_element_structure(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test cart item element has correct structure.

        Each item should have:
        - Title
        - Subtitle with quantity, price each, total
        - Image URL
        - Default action (web URL)
        - Buttons: Increase, Decrease, Remove
        """
        result = formatter.format_cart(sample_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # First item element (index 1, after summary)
        item_element = elements[1]

        # Check structure
        assert "title" in item_element
        assert item_element["title"] == "Test Product 1"

        assert "subtitle" in item_element
        assert "Qty: 2" in item_element["subtitle"]
        assert "$29.99" in item_element["subtitle"]
        assert "Total: $59.98" in item_element["subtitle"]

        assert "image_url" in item_element
        assert item_element["image_url"] == "http://example.com/image1.jpg"

        assert "default_action" in item_element
        assert item_element["default_action"]["type"] == "web_url"

        # Check buttons
        buttons = item_element["buttons"]
        assert len(buttons) == 3

        button_payloads = [b["payload"] for b in buttons]
        assert "increase_quantity:var_1" in button_payloads
        assert "decrease_quantity:var_1" in button_payloads
        assert "remove_item:var_1" in button_payloads

    def test_quantity_button_disabled_at_minimum(self, formatter: CartFormatter) -> None:
        """Test decrease button shows (Min) when quantity is 1."""
        cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="Single Item",
                    price=29.99,
                    image_url="http://example.com/image1.jpg",
                    quantity=1,  # At minimum
                    currency_code=CurrencyCode.USD
                )
            ],
            subtotal=29.99,
            currency_code=CurrencyCode.USD,
            item_count=1
        )

        result = formatter.format_cart(cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Item element (index 1, after summary)
        item_element = elements[1]
        buttons = item_element["buttons"]

        # Find decrease button
        decrease_button = [b for b in buttons if "decrease" in b["payload"].lower()][0]
        assert decrease_button["title"] == "➖ (Min)"

    def test_price_formatting_different_currencies(self, formatter: CartFormatter) -> None:
        """Test price formatting with different currencies."""
        # EUR cart
        eur_cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="European Product",
                    price=25.50,
                    image_url="http://example.com/image.jpg",
                    quantity=2,
                    currency_code=CurrencyCode.EUR
                )
            ],
            subtotal=51.00,
            currency_code=CurrencyCode.EUR,
            item_count=2
        )

        result = formatter.format_cart(eur_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Should use € for EUR
        assert "€51.00" in elements[0]["subtitle"]
        assert "€25.50" in elements[1]["subtitle"]

        # GBP cart
        gbp_cart = Cart(
            items=[
                CartItem(
                    product_id="prod_1",
                    variant_id="var_1",
                    title="British Product",
                    price=19.99,
                    image_url="http://example.com/image.jpg",
                    quantity=1,
                    currency_code=CurrencyCode.GBP
                )
            ],
            subtotal=19.99,
            currency_code=CurrencyCode.GBP,
            item_count=1
        )

        result = formatter.format_cart(gbp_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Should use £ for GBP
        assert "£19.99" in elements[0]["subtitle"]

    def test_checkout_reminder_element(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test checkout reminder element at end of cart display."""
        result = formatter.format_cart(sample_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Last element is checkout reminder
        checkout_element = elements[-1]

        assert "checkout" in checkout_element["title"].lower()
        assert "Total:" in checkout_element["subtitle"]
        assert "$109.97" in checkout_element["subtitle"]

        # Should have Checkout and Continue Shopping buttons
        buttons = checkout_element["buttons"]
        assert len(buttons) == 2
        button_payloads = [b["payload"] for b in buttons]
        assert "checkout" in button_payloads
        assert "continue_shopping" in button_payloads

    def test_button_payloads_include_variant_id(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test button payloads correctly reference variant IDs."""
        result = formatter.format_cart(sample_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # First item buttons
        first_item_buttons = elements[1]["buttons"]
        payloads = [b["payload"] for b in first_item_buttons]

        # All buttons should reference var_1
        assert all("var_1" in payload for payload in payloads)

        # Second item buttons
        second_item_buttons = elements[2]["buttons"]
        payloads = [b["payload"] for b in second_item_buttons]

        # All buttons should reference var_2
        assert all("var_2" in payload for payload in payloads)

    def test_default_action_links_to_store(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test default action links to Shopify store."""
        result = formatter.format_cart(sample_cart, "test_psid")
        elements = result["attachment"]["payload"]["elements"]

        # Check summary default action
        summary_action = elements[0]["default_action"]
        assert summary_action["type"] == "web_url"
        assert "example.myshopify.com/cart" in summary_action["url"]

        # Check item default action
        item_action = elements[1]["default_action"]
        assert item_action["type"] == "web_url"
        assert "example.myshopify.com/products/prod_1" in item_action["url"]

    def test_max_quantity_constant(self, formatter: CartFormatter) -> None:
        """Test MAX_QUANTITY constant is defined."""
        assert hasattr(formatter, "MAX_QUANTITY")
        assert formatter.MAX_QUANTITY == 10

    def test_image_aspect_ratio_setting(self, formatter: CartFormatter, sample_cart: Cart) -> None:
        """Test image aspect ratio is set to square."""
        result = formatter.format_cart(sample_cart, "test_psid")

        payload = result["attachment"]["payload"]
        assert "image_aspect_ratio" in payload
        assert payload["image_aspect_ratio"] == "square"
