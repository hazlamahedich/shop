# E-Commerce Provider API Documentation

**Feature: Optional Shopify Integration with Pluggable Store Providers**

This document describes the E-Commerce Provider abstraction layer that enables optional Shopify integration and supports future platform extensions.

## Overview

The E-Commerce Provider system allows merchants to use the bot with or without an e-commerce store connected. When no store is connected, the bot still provides FAQ, business info, and human handoff functionality.

---

## Provider Types

| Provider | Value | Description |
|----------|-------|-------------|
| None | `none` | Default. No store connected. Bot provides FAQ/support only. |
| Shopify | `shopify` | Connected Shopify store via Storefront API. |
| Mock | `mock` | Testing provider with predictable data (IS_TESTING=true). |

---

## Store Status Endpoint

### Get Store Connection Status

Retrieve the current merchant's e-commerce connection status.

**Endpoint:** `GET /api/v1/merchant/store-status`

**Authentication:** Required

**Request:**
```http
GET /api/v1/merchant/store-status
X-Merchant-Id: 1
```

**Response (200 OK) - No Store:**
```json
{
  "data": {
    "storeProvider": "none",
    "isConnected": false,
    "storeName": null,
    "storeDomain": null
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

**Response (200 OK) - Shopify Connected:**
```json
{
  "data": {
    "storeProvider": "shopify",
    "isConnected": true,
    "storeName": "Alex's Athletic Gear",
    "storeDomain": "alexs-gear.myshopify.com"
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## Store Connection Endpoints

### Connect Shopify Store

Initiate Shopify OAuth flow to connect a store.

**Endpoint:** `GET /api/v1/shopify/connect`

**Authentication:** Required

**Response:** Redirects to Shopify OAuth consent screen.

---

### Disconnect Store

Remove the current store connection. Merchant will switch to `none` provider.

**Endpoint:** `DELETE /api/v1/shopify/connect`

**Authentication:** Required

**Response (200 OK):**
```json
{
  "data": {
    "storeProvider": "none",
    "isConnected": false
  },
  "meta": {
    "requestId": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## Conditional Features

### Features Requiring Store Connection

| Feature | Endpoint Prefix | Behavior Without Store |
|---------|-----------------|------------------------|
| Product Search | `/api/v1/products` | Returns 503 Service Unavailable |
| Product Details | `/api/v1/products/{id}` | Returns 503 Service Unavailable |
| Cart Operations | `/api/v1/cart` | Returns 503 Service Unavailable |
| Checkout | `/api/v1/checkout` | Returns 503 Service Unavailable |
| Order History | `/api/v1/orders` | Returns 503 Service Unavailable |

### Features Available Without Store

| Feature | Endpoint Prefix | Notes |
|---------|-----------------|-------|
| Business Info | `/api/v1/merchant/business-info` | Full functionality |
| FAQ Management | `/api/v1/merchant/faqs` | Full functionality |
| Human Handoff | `/api/v1/handoff` | Full functionality |
| Conversation History | `/api/v1/conversations` | Full functionality |

---

## Error Responses

### Store Not Connected (503)

Returned when requesting e-commerce features without a connected store.

```json
{
  "detail": {
    "error_code": 4001,
    "message": "No e-commerce store connected",
    "details": {
      "provider": "none",
      "required_features": ["products", "cart", "checkout"]
    }
  }
}
```

### Error Codes

| Code | Name | Description |
|------|------|-------------|
| 4000 | STORE_PROVIDER_ERROR | General store provider error |
| 4001 | STORE_NOT_CONNECTED | No store connected for requested feature |
| 4002 | STORE_CONNECTION_FAILED | Failed to connect to store |
| 4003 | STORE_AUTH_EXPIRED | Store credentials expired |
| 4004 | STORE_RATE_LIMITED | Store API rate limit exceeded |

---

## Environment Configuration

### Testing Without Live Store

Set these environment variables for development/testing:

```bash
# Enable testing mode
IS_TESTING=true

# Enable mock store provider
MOCK_STORE_ENABLED=true
```

When enabled, the `MockStoreProvider` returns predictable test data:

```python
# Mock product catalog includes:
- "Test Product A" ($29.99)
- "Test Product B" ($49.99)
- "Test Product C" ($19.99)
```

---

## Data Types

### StoreStatusResponse
```typescript
interface StoreStatusResponse {
  storeProvider: 'none' | 'shopify' | 'mock';
  isConnected: boolean;
  storeName: string | null;
  storeDomain: string | null;
}
```

### ProductResponse
```typescript
interface Product {
  id: string;
  title: string;
  price: number;
  currency: string;
  description?: string;
  imageUrl?: string;
  variants: ProductVariant[];
}

interface ProductVariant {
  id: string;
  title: string;
  price: number;
  available: boolean;
}
```

### CartResponse
```typescript
interface Cart {
  id: string;
  items: CartItem[];
  total: number;
  currency: string;
}

interface CartItem {
  productId: string;
  variantId: string;
  quantity: number;
  title: string;
  price: number;
}
```

---

## Frontend Integration

### Checking Store Connection

```typescript
import { useAuthStore } from '@/stores/authStore';

function MyComponent() {
  const { hasStoreConnected, merchant } = useAuthStore();
  
  if (!hasStoreConnected) {
    return <NoStoreMessage />;
  }
  
  return <ShoppingFeatures />;
}
```

### Route Guard

```tsx
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

export function StoreRequiredGuard({ children }) {
  const { hasStoreConnected } = useAuthStore();
  
  if (!hasStoreConnected) {
    return <Navigate to="/connect-store" replace />;
  }
  
  return <>{children}</>;
}

// Usage in routes
<Route path="/products" element={
  <StoreRequiredGuard>
    <ProductsPage />
  </StoreRequiredGuard>
} />
```

---

## Migration Notes

### Existing Merchants

Merchants with existing Shopify connections are automatically migrated:

```sql
-- Migration sets 'shopify' for existing connections
UPDATE merchants SET store_provider = 'shopify'
WHERE shopify_domain IS NOT NULL;
```

### New Merchants

New merchants start with `store_provider = 'none'` by default.

---

## Related Documentation

- [Architecture: E-Commerce Abstraction Layer](/docs/architecture/ecommerce-abstraction.md)
- [Business Info & FAQ API](/backend/docs/api/business-info-faq.md)
- [Project Context](/docs/project-context.md)
