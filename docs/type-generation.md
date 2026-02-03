# Type Generation

This document describes the automated type generation process for keeping Python and TypeScript types in sync.

## Overview

The Shopping Assistant Bot uses Pydantic schemas for the backend API. TypeScript types are automatically generated from these schemas to ensure type safety across the full stack.

## Process Flow

```
┌─────────────────────┐
│ backend/app/schemas/ │  (Pydantic schemas)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ FastAPI /openapi.json │  (Auto-generated)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────┐
│ scripts/generate_types.py │  (Type generation script)
└──────────┬──────────────┘
           │
           ▼
┌───────────────────────────────────┐
│ frontend/src/lib/types/generated.ts │  (TypeScript types)
└───────────────────────────────────┘
```

## Type Generation Script

**Location:** `scripts/generate_types.py`

**Usage:**
```bash
python scripts/generate_types.py
```

**What it does:**
1. Imports FastAPI app from `backend/app/main.py`
2. Exports OpenAPI schema via `app.openapi()`
3. Runs `openapi-typescript` to generate TypeScript types
4. Outputs to `frontend/src/lib/types/generated.ts`

## Automated Execution

### Pre-commit Hook

The type generation runs automatically on every commit that touches `backend/app/schemas/`:

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: openapi-generator
      name: Generate OpenAPI spec
      entry: bash -c 'cd backend && python -m scripts.hooks.openapi_gen'
      files: ^backend/app/schemas/.*\.py$
```

### Manual Trigger

```bash
# Regenerate types manually
python scripts/generate_types.py
```

## TypeScript Type Structure

Generated types follow this structure:

```typescript
// frontend/src/lib/types/generated.ts
export interface paths {
  "/api/v1/chat": {
    post: operations["Chat"];
  };
  "/api/v1/cart/{cart_id}": {
    get: operations["GetCart"];
    // ...
  };
}

export interface components {
  schemas: {
    User: {
      id: string;
      email: string;
      name: string;
    };
    Product: {
      id: string;
      title: string;
      price: number;
    };
    // ... more schemas
  };
}
```

## Using Generated Types

### Importing Types

```typescript
import type { components, paths } from "@/lib/types/generated";

// Type alias for convenience
type User = components["schemas"]["User"];
type Product = components["schemas"]["Product"];
```

### Typed API Calls

```typescript
import type { paths } from "@/lib/types/generated";

async function sendMessage(message: string) {
  const response = await fetch("/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  });

  const data = await response.json() as paths["/api/v1/chat"]["post"]["responses"]["200"]["content"]["application/json"];
  return data;
}
```

### React Component Props

```typescript
import type { components } from "@/lib/types/generated";

type Product = components["schemas"]["Product"];

interface ProductCardProps {
  product: Product;
  onAddToCart: (productId: string) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  return (
    <div className="product-card">
      <h3>{product.title}</h3>
      <p>${product.price}</p>
      <button onClick={() => onAddToCart(product.id)}>
        Add to Cart
      </button>
    </div>
  );
}
```

## OpenAPI Schema

The OpenAPI schema is available at:
- **Development:** `http://localhost:8000/openapi.json`
- **File:** `backend/openapi.json`
- **Interactive Docs:** `http://localhost:8000/docs` (Swagger UI)

## Adding New Schemas

When adding new Pydantic schemas:

1. **Create schema in backend:**
   ```python
   # backend/app/schemas/order.py
   from pydantic import BaseModel

   class Order(BaseModel):
       id: str
       status: str
       total: float
   ```

2. **Add to FastAPI app:**
   ```python
   from backend.app.schemas.order import Order

   @app.post("/api/v1/orders", response_model=Order)
   async def create_order(order: Order):
       return order
   ```

3. **Generate types:**
   ```bash
   python scripts/generate_types.py
   ```

4. **Use in frontend:**
   ```typescript
   import type { components } from "@/lib/types/generated";
   type Order = components["schemas"]["Order"];
   ```

## Troubleshooting

### Types Not Updating

If generated types are out of sync:

```bash
# Force regeneration
rm backend/openapi.json
python scripts/generate_types.py
```

### Import Errors

If `openapi-typescript` is missing:

```bash
# Install globally
npm install -g openapi-typescript

# Or locally in frontend
cd frontend && npm install --save-dev openapi-typescript
```

### Type Mismatches

If TypeScript types don't match Pydantic schemas:

1. Check backend schema definitions
2. Regenerate OpenAPI spec: Restart FastAPI server
3. Clear TypeScript cache: `rm -rf frontend/node_modules/.cache`
4. Regenerate types: `python scripts/generate_types.py`

## Tool Versions

- **openapi-typescript:** ^6.0.0
- **TypeScript:** ^5.3.0

## Related Documentation

- [Testing Patterns](./testing-patterns.md)
- [Pre-commit Hooks](./pre-commit-hooks.md)
- [API Documentation](../backend/openapi.json)
