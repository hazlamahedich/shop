"""E-Commerce Provider Abstract Interface.

Sprint Change Proposal 2026-02-13: Make Shopify Optional Integration

Defines the abstract interface for e-commerce platform integrations.
All store providers (Shopify, WooCommerce, etc.) must implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StoreNotConnectedError(Exception):
    """Exception raised when e-commerce operations are attempted without a store.

    This exception should be raised by NullStoreProvider and caught by
    API endpoints to return appropriate 503 Service Unavailable responses.
    """

    def __init__(
        self,
        message: str = "No e-commerce store connected. Please connect a store to use shopping features.",
        provider: str = "none",
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            provider: The provider name that raised the error
        """
        self.message = message
        self.provider = provider
        super().__init__(self.message)


class CurrencyCode(str, Enum):
    """Supported currency codes."""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    AUD = "AUD"
    JPY = "JPY"


class ProductVariant(BaseModel):
    """Product variant with pricing and availability."""

    id: str = Field(..., description="Variant ID from the e-commerce platform")
    title: str = Field(..., description="Variant title (e.g., 'Small / Red')")
    price: float = Field(..., ge=0, description="Variant price")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    available: bool = Field(default=True, description="Whether variant is in stock")
    sku: Optional[str] = Field(default=None, description="Stock keeping unit")
    options: list[dict[str, str]] = Field(
        default_factory=list,
        description="Variant options (e.g., [{'name': 'Size', 'value': 'Small'}])",
    )
    weight: Optional[float] = Field(default=None, description="Weight in grams")
    weight_unit: Optional[str] = Field(default=None, description="Weight unit (g, kg, oz, lb)")


class Product(BaseModel):
    """Product from an e-commerce store."""

    id: str = Field(..., description="Product ID from the e-commerce platform")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(default=None, description="Product description")
    product_type: Optional[str] = Field(default=None, description="Product category/type")
    vendor: Optional[str] = Field(default=None, description="Product vendor/brand")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    image_url: Optional[str] = Field(default=None, description="Main product image URL")
    price_min: float = Field(..., ge=0, description="Minimum price across variants")
    price_max: float = Field(..., ge=0, description="Maximum price across variants")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    variants: list[ProductVariant] = Field(
        default_factory=list,
        description="Product variants (sizes, colors, etc.)",
    )
    available: bool = Field(default=True, description="Whether product is available for purchase")
    url: Optional[str] = Field(default=None, description="Product page URL")


class CartItem(BaseModel):
    """Item in a shopping cart."""

    product_id: str = Field(..., description="Product ID")
    variant_id: str = Field(..., description="Variant ID")
    title: str = Field(..., description="Product title")
    price: float = Field(..., ge=0, description="Item price")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    quantity: int = Field(default=1, ge=1, le=99, description="Quantity")
    image_url: Optional[str] = Field(default=None, description="Product image URL")
    added_at: Optional[datetime] = Field(default=None, description="When item was added")


class Cart(BaseModel):
    """Shopping cart from an e-commerce store."""

    id: str = Field(..., description="Cart ID from the e-commerce platform")
    items: list[CartItem] = Field(default_factory=list, description="Cart items")
    subtotal: float = Field(default=0.0, ge=0, description="Cart subtotal")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    item_count: int = Field(default=0, ge=0, description="Total number of items")
    checkout_url: Optional[str] = Field(default=None, description="Checkout URL if available")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class OrderItem(BaseModel):
    """Item in an order."""

    product_id: str = Field(..., description="Product ID")
    variant_id: str = Field(..., description="Variant ID")
    title: str = Field(..., description="Product title")
    price: float = Field(..., ge=0, description="Item price at time of purchase")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    quantity: int = Field(default=1, ge=1, description="Quantity ordered")
    image_url: Optional[str] = Field(default=None, description="Product image URL")


class OrderStatus(str, Enum):
    """Order status values."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order(BaseModel):
    """Order from an e-commerce store."""

    id: str = Field(..., description="Order ID from the e-commerce platform")
    order_number: Optional[str] = Field(default=None, description="Human-readable order number")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    items: list[OrderItem] = Field(default_factory=list, description="Order items")
    subtotal: float = Field(default=0.0, ge=0, description="Order subtotal")
    total: float = Field(default=0.0, ge=0, description="Order total including tax/shipping")
    currency_code: CurrencyCode = Field(default=CurrencyCode.USD)
    customer_email: Optional[str] = Field(default=None, description="Customer email")
    shipping_address: Optional[dict[str, Any]] = Field(
        default=None, description="Shipping address"
    )
    tracking_number: Optional[str] = Field(default=None, description="Shipping tracking number")
    tracking_url: Optional[str] = Field(default=None, description="Tracking URL")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class ECommerceProvider(ABC):
    """Abstract interface for e-commerce platform integrations.

    All store providers (Shopify, WooCommerce, BigCommerce, etc.) must implement
    this interface. The system uses this interface to interact with stores
    regardless of the underlying platform.

    The NullStoreProvider is used when no store is connected and raises
    StoreNotConnectedError for all operations.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'shopify', 'woocommerce', 'none').

        Returns:
            Provider name string
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if provider has valid credentials and can make API calls.

        Returns:
            True if connected and operational, False otherwise
        """
        pass

    # ==================== Product Operations ====================

    @abstractmethod
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
            limit: Maximum number of results to return
            category: Optional category filter
            max_price: Optional maximum price filter
            min_price: Optional minimum price filter
            **kwargs: Additional provider-specific filters

        Returns:
            List of matching Product objects

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a specific product by ID.

        Args:
            product_id: Product ID from the e-commerce platform

        Returns:
            Product object if found, None otherwise

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def get_product_variants(self, product_id: str) -> list[ProductVariant]:
        """Get all variants for a product.

        Args:
            product_id: Product ID

        Returns:
            List of ProductVariant objects

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    # ==================== Cart Operations ====================

    @abstractmethod
    async def create_cart(self) -> Cart:
        """Create a new shopping cart.

        Returns:
            Empty Cart object with generated ID

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def get_cart(self, cart_id: str) -> Optional[Cart]:
        """Get an existing cart by ID.

        Args:
            cart_id: Cart ID from the e-commerce platform

        Returns:
            Cart object if found, None otherwise

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def add_to_cart(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int = 1,
    ) -> Cart:
        """Add an item to the cart.

        Args:
            cart_id: Cart ID
            variant_id: Product variant ID to add
            quantity: Quantity to add (default 1)

        Returns:
            Updated Cart object

        Raises:
            StoreNotConnectedError: If no store is connected
            ValueError: If variant not found or quantity invalid
        """
        pass

    @abstractmethod
    async def update_cart_item(
        self,
        cart_id: str,
        variant_id: str,
        quantity: int,
    ) -> Cart:
        """Update quantity of an item in the cart.

        Args:
            cart_id: Cart ID
            variant_id: Product variant ID to update
            quantity: New quantity (0 to remove)

        Returns:
            Updated Cart object

        Raises:
            StoreNotConnectedError: If no store is connected
            ValueError: If item not found in cart
        """
        pass

    @abstractmethod
    async def remove_from_cart(
        self,
        cart_id: str,
        variant_id: str,
    ) -> Cart:
        """Remove an item from the cart.

        Args:
            cart_id: Cart ID
            variant_id: Product variant ID to remove

        Returns:
            Updated Cart object

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    # ==================== Checkout Operations ====================

    @abstractmethod
    async def create_checkout_url(
        self,
        cart_id: str,
        custom_attributes: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """Generate a checkout URL for a cart.

        Args:
            cart_id: Cart ID to checkout
            custom_attributes: Optional custom attributes to attach to checkout

        Returns:
            Checkout URL string

        Raises:
            StoreNotConnectedError: If no store is connected
            ValueError: If cart is empty or not found
        """
        pass

    # ==================== Order Operations ====================

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get an order by ID.

        Args:
            order_id: Order ID from the e-commerce platform

        Returns:
            Order object if found, None otherwise

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def get_order_by_checkout_token(self, checkout_token: str) -> Optional[Order]:
        """Get an order by checkout token (for webhook processing).

        Args:
            checkout_token: Checkout token from the checkout URL

        Returns:
            Order object if found, None otherwise

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    @abstractmethod
    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        tracking_number: Optional[str] = None,
        tracking_url: Optional[str] = None,
    ) -> Order:
        """Update order status (for webhook handlers).

        Args:
            order_id: Order ID to update
            status: New order status
            tracking_number: Optional tracking number
            tracking_url: Optional tracking URL

        Returns:
            Updated Order object

        Raises:
            StoreNotConnectedError: If no store is connected
        """
        pass

    # ==================== Utility Methods ====================

    async def close(self) -> None:
        """Close any open connections/clients.

        Override this method if the provider maintains persistent connections.
        """
        pass

    async def __aenter__(self) -> ECommerceProvider:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.close()
