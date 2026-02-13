"""Mock Store Provider - Testing Without Real Credentials.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

This provider provides predictable mock data for development and testing.
It allows full feature testing without requiring real Shopify credentials.

Enabled via environment variables:
- IS_TESTING=true
- MOCK_STORE_ENABLED=true
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.services.ecommerce.base import (
    Cart,
    CartItem,
    CurrencyCode,
    ECommerceProvider,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    ProductVariant,
    StoreNotConnectedError,
)


def _generate_mock_products() -> list[Product]:
    """Generate mock product data for testing.

    Returns:
        List of mock Product objects
    """
    return [
        Product(
            id="mock_prod_001",
            title="Running Shoes Pro",
            description="Professional running shoes for marathons and daily training",
            product_type="Footwear",
            vendor="AthleticGear",
            tags=["shoes", "running", "sports"],
            image_url="https://cdn.shopify.com/s/files/shoes-pro.jpg",
            price_min=99.99,
            price_max=129.99,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_001_a",
                    title="Size 8 / Red",
                    price=99.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[
                        {"name": "Size", "value": "8"},
                        {"name": "Color", "value": "Red"},
                    ],
                ),
                ProductVariant(
                    id="mock_var_001_b",
                    title="Size 10 / Blue",
                    price=129.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[
                        {"name": "Size", "value": "10"},
                        {"name": "Color", "value": "Blue"},
                    ],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_002",
            title="Wireless Earbuds",
            description="Premium noise-cancelling earbuds with 30hr battery life",
            product_type="Electronics",
            vendor="AudioTech",
            tags=["electronics", "audio", "wireless"],
            image_url="https://cdn.shopify.com/s/files/earbuds.jpg",
            price_min=89.99,
            price_max=89.99,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_002_a",
                    title="Black",
                    price=89.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Color", "value": "Black"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_003",
            title="Yoga Mat Premium",
            description="Extra thick eco-friendly yoga mat with alignment lines",
            product_type="Fitness Equipment",
            vendor="ZenFitness",
            tags=["fitness", "yoga", "wellness"],
            image_url="https://cdn.shopify.com/s/files/yoga-mat.jpg",
            price_min=45.00,
            price_max=45.00,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_003_a",
                    title="Purple",
                    price=45.00,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Color", "value": "Purple"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_004",
            title="Stainless Steel Water Bottle",
            description="Insulated 24oz water bottle keeps drinks cold for 6 hours",
            product_type="Accessories",
            vendor="EcoDrink",
            tags=["accessories", "eco-friendly", "hydration"],
            image_url="https://cdn.shopify.com/s/files/water-bottle.jpg",
            price_min=24.99,
            price_max=24.99,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_004_a",
                    title="Silver",
                    price=24.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Color", "value": "Silver"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_005",
            title="Bluetooth Speaker Portable",
            description="Waterproof portable speaker with 360deg sound",
            product_type="Electronics",
            vendor="SoundWave",
            tags=["electronics", "audio", "outdoor"],
            image_url="https://cdn.shopify.com/s/files/speaker.jpg",
            price_min=79.99,
            price_max=79.99,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_005_a",
                    title="Black",
                    price=79.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Color", "value": "Black"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_006",
            title="Organic Coffee Beans 1kg",
            description="Fair trade single-origin Ethiopian coffee beans",
            product_type="Food & Drink",
            vendor="BeanRoasters",
            tags=["food", "coffee", "organic"],
            image_url="https://cdn.shopify.com/s/files/coffee.jpg",
            price_min=28.00,
            price_max=28.00,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_006_a",
                    title="Whole Bean",
                    price=28.00,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Grind", "value": "Whole Bean"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_007",
            title="Hiking Backpack 40L",
            description="Lightweight hiking backpack with rain cover",
            product_type="Outdoor Gear",
            vendor="TrailReady",
            tags=["outdoor", "hiking", "travel"],
            image_url="https://cdn.shopify.com/s/files/backpack.jpg",
            price_min=89.00,
            price_max=89.00,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_007_a",
                    title="Forest Green",
                    price=89.00,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[{"name": "Color", "value": "Forest Green"}],
                ),
            ],
            available=True,
        ),
        Product(
            id="mock_prod_008",
            title="Smart Fitness Watch",
            description="Heart rate monitoring and GPS tracking watch",
            product_type="Electronics",
            vendor="FitTech",
            tags=["electronics", "fitness", "wearable"],
            image_url="https://cdn.shopify.com/s/files/smart-watch.jpg",
            price_min=199.99,
            price_max=249.99,
            currency_code=CurrencyCode.USD,
            variants=[
                ProductVariant(
                    id="mock_var_008_a",
                    title="42mm / Black",
                    price=199.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[
                        {"name": "Size", "value": "42mm"},
                        {"name": "Color", "value": "Black"},
                    ],
                ),
                ProductVariant(
                    id="mock_var_008_b",
                    title="46mm / Silver",
                    price=249.99,
                    currency_code=CurrencyCode.USD,
                    available=True,
                    options=[
                        {"name": "Size", "value": "46mm"},
                        {"name": "Color", "value": "Silver"},
                    ],
                ),
            ],
            available=True,
        ),
    ]


class MockStoreProvider(ECommerceProvider):
    """Provider for testing without real e-commerce credentials.

    This provider implements the full ECommerceProvider interface with
    predictable mock data, enabling full feature testing without
    requiring real Shopify credentials.

    Features:
    - In-memory product catalog
    - In-memory cart storage
    - In-memory order storage
    - Checkout URL generation (mock)
    - Order status tracking

    Environment Variables:
    - IS_TESTING: Set to "true" to enable mock provider
    - MOCK_STORE_ENABLED: Set to "true" to enable mock provider

    Example:
        provider = MockStoreProvider()
        if provider.is_connected():
            products = await provider.search_products("shoes")
            # Returns mock products matching "shoes"
    """

    def __init__(self) -> None:
        """Initialize the mock provider with sample data."""
        self._products = _generate_mock_products()
        self._carts: dict[str, Cart] = {}
        self._orders: dict[str, Order] = {}
        self._checkout_token_to_order: dict[str, str] = {}

    @property
    def provider_name(self) -> str:
        """Return provider identifier.

        Returns:
            "mock" to indicate testing mode
        """
        return "mock"

    def is_connected(self) -> bool:
        """Check if mock provider is enabled.

        Returns:
            True if IS_TESTING or MOCK_STORE_ENABLED is set
        """
        is_testing = os.getenv("IS_TESTING", "false").lower() == "true"
        mock_enabled = os.getenv("MOCK_STORE_ENABLED", "false").lower() == "true"
        return is_testing or mock_enabled

    # ==================== Product Operations ====================

    async def search_products(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_price: Optional[float] = None,
        **kwargs: Any,
    ) -> list[Product]:
        """Search for products matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results
            category: Optional category filter
            max_price: Optional maximum price filter
            min_price: Optional minimum price filter

        Returns:
            List of matching mock products
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled. Set IS_TESTING=true or MOCK_STORE_ENABLED=true",
                provider=self.provider_name,
            )

        query_lower = query.lower()
        results = []

        for product in self._products:
            # Match against title, description, tags, and product type
            matches_query = (
                query_lower in product.title.lower()
                or (product.description and query_lower in product.description.lower())
                or any(query_lower in tag.lower() for tag in product.tags)
                or (product.product_type and query_lower in product.product_type.lower())
            )

            if not matches_query:
                continue

            # Apply filters
            if category and product.product_type:
                if category.lower() not in product.product_type.lower():
                    continue

            if max_price is not None and product.price_min > max_price:
                continue

            if min_price is not None and product.price_max < min_price:
                continue

            results.append(product)

        return results[:limit]

    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID.

        Args:
            product_id: Product ID to find

        Returns:
            Product if found, None otherwise
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        for product in self._products:
            if product.id == product_id:
                return product
        return None

    async def get_product_variants(self, product_id: str) -> list[ProductVariant]:
        """Get all variants for a product.

        Args:
            product_id: Product ID

        Returns:
            List of product variants
        """
        product = await self.get_product(product_id)
        if product:
            return product.variants
        return []

    # ==================== Cart Operations ====================

    async def create_cart(self) -> Cart:
        """Create a new shopping cart.

        Returns:
            Empty Cart object with generated ID
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        cart_id = f"mock_cart_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        cart = Cart(
            id=cart_id,
            items=[],
            subtotal=0.0,
            currency_code=CurrencyCode.USD,
            item_count=0,
            created_at=now,
            updated_at=now,
        )

        self._carts[cart_id] = cart
        return cart

    async def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get an existing cart by ID.

        Args:
            cart_id: Cart ID

        Returns:
            Cart if found, None otherwise
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        return self._carts.get(cart_id)

    async def add_to_cart(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int = 1,
    ) -> Cart:
        """Add an item to the cart.

        Args:
            cart_id: Cart ID
            variant_id: Variant ID to add
            quantity: Quantity to add

        Returns:
            Updated Cart
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        cart = self._carts.get(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")

        # Find the variant across all products
        product_found = None
        variant_found = None

        for product in self._products:
            for variant in product.variants:
                if variant.id == variant_id:
                    product_found = product
                    variant_found = variant
                    break
            if variant_found:
                break

        if not variant_found or not product_found:
            raise ValueError(f"Variant {variant_id} not found")

        # Check if item already exists in cart
        existing_item = None
        for item in cart.items:
            if item.variant_id == variant_id:
                existing_item = item
                break

        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                product_id=product_found.id,
                variant_id=variant_id,
                title=f"{product_found.title} - {variant_found.title}",
                price=variant_found.price,
                currency_code=variant_found.currency_code,
                quantity=quantity,
                image_url=product_found.image_url,
                added_at=datetime.now(timezone.utc),
            )
            cart.items.append(new_item)

        # Update cart totals
        cart.subtotal = sum(item.price * item.quantity for item in cart.items)
        cart.item_count = sum(item.quantity for item in cart.items)
        cart.updated_at = datetime.now(timezone.utc)

        return cart

    async def update_cart_item(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Update quantity of an item in the cart.

        Args:
            cart_id: Cart ID
            variant_id: Variant ID to update
            quantity: New quantity (0 to remove)

        Returns:
            Updated Cart
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        cart = self._carts.get(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")

        if quantity <= 0:
            # Remove item
            cart.items = [item for item in cart.items if item.variant_id != variant_id]
        else:
            # Update quantity
            found = False
            for item in cart.items:
                if item.variant_id == variant_id:
                    item.quantity = quantity
                    found = True
                    break

            if not found:
                raise ValueError(f"Item with variant {variant_id} not found in cart")

        # Update cart totals
        cart.subtotal = sum(item.price * item.quantity for item in cart.items)
        cart.item_count = sum(item.quantity for item in cart.items)
        cart.updated_at = datetime.now(timezone.utc)

        return cart

    async def remove_from_cart(
        self,
        cart_id: str,
        variant_id: str,
    ) -> Cart:
        """Remove an item from the cart.

        Args:
            cart_id: Cart ID
            variant_id: Variant ID to remove

        Returns:
            Updated Cart
        """
        return await self.update_cart_item(cart_id, variant_id, 0)

    # ==================== Checkout Operations ====================

    async def create_checkout_url(
        self,
        cart_id: str,
        custom_attributes: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Generate a mock checkout URL for a cart.

        Args:
            cart_id: Cart ID to checkout
            custom_attributes: Optional custom attributes

        Returns:
            Mock checkout URL
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        cart = self._carts.get(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} not found")

        if not cart.items:
            raise ValueError("Cannot checkout an empty cart")

        # Generate mock checkout token
        checkout_token = f"mock_checkout_{uuid.uuid4().hex[:12]}"

        # Create a pending order
        order_id = f"mock_order_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        order = Order(
            id=order_id,
            order_number=f"#{1000 + len(self._orders)}",
            status=OrderStatus.PENDING,
            items=[
                OrderItem(
                    product_id=item.product_id,
                    variant_id=item.variant_id,
                    title=item.title,
                    price=item.price,
                    currency_code=item.currency_code,
                    quantity=item.quantity,
                    image_url=item.image_url,
                )
                for item in cart.items
            ],
            subtotal=cart.subtotal,
            total=cart.subtotal,  # Mock doesn't include tax/shipping
            currency_code=cart.currency_code,
            created_at=now,
            updated_at=now,
        )

        self._orders[order_id] = order
        self._checkout_token_to_order[checkout_token] = order_id

        # Return mock checkout URL
        return f"https://mock-checkout.example.com/checkout/{checkout_token}"

    # ==================== Order Operations ====================

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        return self._orders.get(order_id)

    async def get_order_by_checkout_token(self, checkout_token: str) -> Optional[Order]:
        """Get an order by checkout token.

        Args:
            checkout_token: Checkout token from URL

        Returns:
            Order if found, None otherwise
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        order_id = self._checkout_token_to_order.get(checkout_token)
        if order_id:
            return self._orders.get(order_id)
        return None

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Order:
        """Update order status.

        Args:
            order_id: Order ID to update
            status: New status
            tracking_number: Optional tracking number
            tracking_url: Optional tracking URL

        Returns:
            Updated Order
        """
        if not self.is_connected():
            raise StoreNotConnectedError(
                message="Mock store not enabled",
                provider=self.provider_name,
            )

        order = self._orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        order.status = status
        order.updated_at = datetime.now(timezone.utc)

        if tracking_number:
            order.tracking_number = tracking_number
        if tracking_url:
            order.tracking_url = tracking_url

        return order

    # ==================== Testing Helpers ====================

    def add_mock_product(self, product: Product) -> None:
        """Add a custom product for testing.

        Args:
            product: Product to add
        """
        self._products.append(product)

    def clear_carts(self) -> None:
        """Clear all carts (for test cleanup)."""
        self._carts.clear()

    def clear_orders(self) -> None:
        """Clear all orders (for test cleanup)."""
        self._orders.clear()
        self._checkout_token_to_order.clear()
