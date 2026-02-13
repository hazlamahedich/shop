# E-Commerce Abstraction Layer Architecture

**Date:** 2026-02-13  
**Status:** Approved  
**Related:** Sprint Change Proposal 2026-02-13

---

## Overview

The E-Commerce Abstraction Layer enables pluggable store provider support, making Shopify an optional integration rather than a required dependency.

## Design Goals

1. **Optional Integration** - Bot works fully without e-commerce store
2. **Extensibility** - Easy to add new providers (WooCommerce, BigCommerce)
3. **Graceful Degradation** - Clear error messages when features unavailable
4. **Testability** - Mock provider for development without real credentials

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │  AuthStore   │  │  ProductPage │  │  StoreRequiredGuard      │   │
│  │              │  │              │  │                          │   │
│  │ storeProvider│  │ (conditional)│  │ if (!hasStoreConnected)  │   │
│  │ hasStore     │  │              │  │   → /connect-store       │   │
│  │ Connected()  │  └──────────────┘  └──────────────────────────┘   │
│  └──────┬───────┘                                                    │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          │ HTTP API
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API Layer                                 │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │   │
│  │  │/products │  │  /cart   │  │/checkout │  │ /store-status│ │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │   │
│  │       │             │             │                │         │   │
│  │       └─────────────┴──────┬──────┴────────────────┘         │   │
│  │                            │                                 │   │
│  └────────────────────────────┼─────────────────────────────────┘   │
│                               │                                     │
│                               ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Provider Factory                                │   │
│  │                                                              │   │
│  │   get_provider(merchant) → ECommerceProvider                │   │
│  │                                                              │   │
│  └────────────────────────────┬────────────────────────────────┘   │
│                               │                                     │
│         ┌─────────────────────┼─────────────────────┐               │
│         │                     │                     │               │
│         ▼                     ▼                     ▼               │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │NullProvider │    │ShopifyProvider  │    │ MockProvider    │     │
│  │             │    │                 │    │                 │     │
│  │ provider:   │    │ provider:       │    │ provider:       │     │
│  │   "none"    │    │   "shopify"     │    │   "mock"        │     │
│  │             │    │                 │    │                 │     │
│  │ is_connected│    │ ShopifyClient   │    │ Test data       │     │
│  │   = false   │    │ Storefront API  │    │ when IS_TESTING │     │
│  │             │    │                 │    │                 │     │
│  │ raises:     │    │ Features:       │    │ Features:       │     │
│  │ StoreNot    │    │ - Products      │    │ - Products      │     │
│  │ Connected   │    │ - Cart          │    │ - Cart          │     │
│  │             │    │ - Checkout      │    │ - Checkout      │     │
│  └─────────────┘    │ - Orders        │    │ - Orders        │     │
│                     └─────────────────┘    └─────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    External APIs    │
                    │                     │
                    │  ┌───────────────┐  │
                    │  │ Shopify API   │  │
                    │  │ Storefront    │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

---

## Component Details

### ECommerceProvider Interface

Abstract base class defining the contract for all store providers.

```python
class ECommerceProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...
    
    @abstractmethod
    def is_connected(self) -> bool: ...
    
    @abstractmethod
    async def search_products(self, query: str, limit: int = 10) -> List[Product]: ...
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]: ...
    
    @abstractmethod
    async def create_cart(self) -> Cart: ...
    
    @abstractmethod
    async def add_to_cart(self, cart_id: str, product_id: str, quantity: int) -> Cart: ...
    
    @abstractmethod
    async def create_checkout_url(self, cart_id: str) -> str: ...
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]: ...
```

### Provider Implementations

| Provider | Class | Use Case |
|----------|-------|----------|
| Null | `NullStoreProvider` | Default. No store connected. |
| Shopify | `ShopifyStoreProvider` | Real Shopify integration. |
| Mock | `MockStoreProvider` | Testing without real credentials. |

### Provider Factory

```python
def get_provider(merchant: Merchant) -> ECommerceProvider:
    """Factory function to get appropriate provider."""
    
    if IS_TESTING and MOCK_STORE_ENABLED:
        return MockStoreProvider()
    
    match merchant.store_provider:
        case "shopify":
            return ShopifyStoreProvider(
                domain=merchant.shopify_domain,
                token=merchant.shopify_token
            )
        case "none" | _:
            return NullStoreProvider()
```

---

## Directory Structure

```
backend/app/services/ecommerce/
├── __init__.py              # Exports
├── base.py                  # ECommerceProvider abstract interface
├── exceptions.py            # StoreNotConnectedError, etc.
├── models.py                # Product, Cart, Order dataclasses
├── null_provider.py         # NullStoreProvider
├── mock_provider.py         # MockStoreProvider
├── provider_factory.py      # Factory function
└── shopify/
    ├── __init__.py
    ├── provider.py          # ShopifyStoreProvider
    ├── client.py            # Shopify API client
    └── webhooks.py          # Shopify webhook handlers
```

---

## Database Schema

### Merchant Table

```sql
CREATE TABLE merchants (
    id SERIAL PRIMARY KEY,
    facebook_page_id VARCHAR(100) UNIQUE,
    store_provider VARCHAR(20) DEFAULT 'none' NOT NULL,
    shopify_domain VARCHAR(255),
    shopify_access_token VARCHAR(255),
    -- ... other fields
);

CREATE INDEX idx_merchants_store_provider ON merchants(store_provider);
```

### StoreProvider Enum

```python
class StoreProvider(str, Enum):
    NONE = "none"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"  # Future
    BIGCOMMERCE = "bigcommerce"  # Future
```

---

## Feature Availability Matrix

| Feature | No Store | Shopify | Mock |
|---------|----------|---------|------|
| FAQ/Business Info | ✅ | ✅ | ✅ |
| Human Handoff | ✅ | ✅ | ✅ |
| Conversation History | ✅ | ✅ | ✅ |
| Product Search | ❌ 503 | ✅ | ✅ |
| Product Details | ❌ 503 | ✅ | ✅ |
| Cart Operations | ❌ 503 | ✅ | ✅ |
| Checkout | ❌ 503 | ✅ | ✅ |
| Order Tracking | ❌ 503 | ✅ | ✅ |

---

## Error Handling Flow

```
┌─────────────────┐
│  API Request    │
│  /products      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Get Provider    │────▶│ merchant.store  │
│                 │     │ _provider       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ provider.       │
│ is_connected()  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌───────┐
│ True  │  │ False │
└───┬───┘  └───┬───┘
    │          │
    ▼          ▼
┌───────┐  ┌────────────────┐
│Execute│  │ Raise          │
│Method │  │ StoreNot       │
│       │  │ ConnectedError │
└───────┘  └───────┬────────┘
                   │
                   ▼
           ┌────────────────┐
           │ 503 Response   │
           │ {              │
           │  error_code:   │
           │    4001,       │
           │  message:      │
           │   "No store"   │
           │ }              │
           └────────────────┘
```

---

## Adding a New Provider

To add a new e-commerce provider (e.g., WooCommerce):

### 1. Create Provider Implementation

```python
# backend/app/services/ecommerce/woocommerce/provider.py

class WooCommerceStoreProvider(ECommerceProvider):
    def __init__(self, store_url: str, api_key: str, api_secret: str):
        self._client = WooCommerceClient(store_url, api_key, api_secret)
    
    @property
    def provider_name(self) -> str:
        return "woocommerce"
    
    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        return await self._client.search_products(query, limit)
    
    # ... implement all abstract methods
```

### 2. Update Enum

```python
class StoreProvider(str, Enum):
    NONE = "none"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"  # Add this
```

### 3. Update Factory

```python
def get_provider(merchant: Merchant) -> ECommerceProvider:
    match merchant.store_provider:
        case "woocommerce":
            return WooCommerceStoreProvider(...)
        # ... other cases
```

### 4. Add Database Fields

```sql
ALTER TABLE merchants ADD COLUMN woocommerce_url VARCHAR(255);
ALTER TABLE merchants ADD COLUMN woocommerce_api_key VARCHAR(255);
ALTER TABLE merchants ADD COLUMN woocommerce_api_secret VARCHAR(255);
```

---

## Testing Strategy

### Unit Tests

```python
@pytest.mark.asyncio
async def test_null_provider_raises_error():
    provider = NullStoreProvider()
    
    with pytest.raises(StoreNotConnectedError):
        await provider.search_products("test")

@pytest.mark.asyncio
async def test_mock_provider_returns_products():
    provider = MockStoreProvider()
    products = await provider.search_products("test")
    
    assert len(products) > 0
    assert products[0].title.startswith("Test Product")
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_products_endpoint_returns_503_without_store(client, merchant_no_store):
    response = await client.get(
        "/api/v1/products",
        headers={"X-Merchant-Id": str(merchant_no_store.id)}
    )
    
    assert response.status_code == 503
    assert response.json()["detail"]["error_code"] == 4001
```

---

## Related Documents

- [API Documentation: E-Commerce Provider](/backend/docs/api/ecommerce-provider.md)
- [Sprint Change Proposal](/_bmad-output/planning-artifacts/sprint-change-proposal-2026-02-13.md)
- [Project Context](/docs/project-context.md)
