# Party Mode Testing Strategy - Comprehensive Testability Review

**Test Architect**: Murat
**Date**: 2026-02-02
**Platform**: FastAPI + React Shop Bot
**Version**: v1.0 MVP

---

## Executive Summary

This document provides a comprehensive testing strategy for the Party Mode implementation patterns. The strategy emphasizes **testability first**, **contract-driven development**, and **confidence through automation**.

### Key Recommendations

- **70/20/10 Test Pyramid**: 70% unit, 20% integration, 10% E2E
- **Contract Testing**: OpenAPI-driven validation between frontend and backend
- **Test Data Management**: Factory pattern + pytest fixtures + MSW
- **Coverage Targets**: 90% unit, 80% integration, critical path E2E
- **Parallel Execution**: pytest-xdist + vitest worker farms
- **E2E Tracing**: Playwright trace files + request_id correlation

---

## 1. Test Pyramid Implementation

### 1.1 Distribution Strategy

```
                    ┌─────────────┐
                    │   E2E (10%) │  ← Critical user journeys
                    │  Playwright │
                    └──────┬──────┘
                           │
                ┌──────────┴──────────┐
                │  Integration (20%)  │  ← API + DB + External
                │   pytest + fixtures │
                └──────────┬──────────┘
                           │
      ┌────────────────────┴────────────────────┐
      │             Unit (70%)                   │
      │  pytest (backend) + vitest (frontend)   │
      │  - Domain logic                          │
      │  - Pure functions                        │
      │  - React components                      │
      │  - Hooks                                 │
      └─────────────────────────────────────────┘
```

### 1.2 Backend Unit Tests (pytest)

**Structure**: Co-located `test_*.py` files

```python
# tests/unit/domain/test_cart.py
import pytest
from app.domain.cart import Cart, CartItem

class TestCartAddItem:
    """Unit tests for cart item addition"""

    def test_add_item_to_empty_cart(self):
        """Test adding item to empty cart creates new cart"""
        cart = Cart()
        item = CartItem(product_id="prod_123", quantity=1)

        result = cart.add_item(item)

        assert result.total_items == 1
        assert result.total_value == 0

    def test_add_item_updates_existing(self):
        """Test adding existing item increments quantity"""
        cart = Cart(items=[CartItem(product_id="prod_123", quantity=1)])

        result = cart.add_item(CartItem(product_id="prod_123", quantity=2))

        assert result.total_items == 3

    @pytest.mark.parametrize("quantity,expected", [
        (0, False),
        (-1, False),
        (100, True),
    ])
    def test_add_item_validates_quantity(self, quantity, expected):
        """Test quantity validation rules"""
        cart = Cart()
        item = CartItem(product_id="prod_123", quantity=quantity)

        result = cart.add_item(item)

        assert result.success == expected
```

**Target**: 90% coverage on domain logic

### 1.3 Frontend Unit Tests (vitest)

**Structure**: Co-located `*.test.tsx` files

```typescript
// src/components/Cart/CartItem.test.tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { CartItem } from './CartItem'

describe('CartItem', () => {
  const mockItem = {
    id: 'item_123',
    product: {
      id: 'prod_123',
      title: 'Test Product',
      price: 29.99,
    },
    quantity: 2,
  }

  it('renders product title and price', () => {
    render(<CartItem item={mockItem} onUpdate={vi.fn()} onRemove={vi.fn()} />)

    expect(screen.getByText('Test Product')).toBeInTheDocument()
    expect(screen.getByText('$29.99')).toBeInTheDocument()
  })

  it('displays correct quantity', () => {
    render(<CartItem item={mockItem} onUpdate={vi.fn()} onRemove={vi.fn()} />)

    expect(screen.getByDisplayValue('2')).toBeInTheDocument()
  })

  it('calls onUpdate when quantity changes', async () => {
    const onUpdate = vi.fn()
    const user = userEvent.setup()

    render(<CartItem item={mockItem} onUpdate={onUpdate} onRemove={vi.fn()} />)

    await user.click(screen.getByLabelText('Increase quantity'))

    expect(onUpdate).toHaveBeenCalledWith('item_123', 3)
  })
})
```

**Target**: 90% coverage on components and hooks

### 1.4 Integration Tests

**Backend Integration** (pytest + fixtures):

```python
# tests/integration/test_checkout_flow.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client(db_session):
    """Test client with database fixture"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_checkout_link_integration(client, test_user, test_product):
    """Test full checkout creation flow with DB"""
    # Create cart
    response = client.post(
        "/api/v1/cart",
        json={"product_id": test_product.id, "quantity": 1},
        headers={"X-User-Id": str(test_user.id)}
    )
    assert response.status_code == 201

    # Create checkout
    response = client.post(
        "/api/v1/checkout",
        headers={"X-User-Id": str(test_user.id)}
    )
    assert response.status_code == 200
    assert "checkout_url" in response.json()["data"]
```

**Frontend Integration** (MSW + vitest):

```typescript
// src/api/cart.test.ts
import { describe, it, expect, beforeAll } from 'vitest'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { addToCart } from './cart'

const server = setupServer(
  http.post('/api/v1/cart', async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      data: {
        cart_id: 'cart_123',
        items: [{ product_id: body.product_id, quantity: body.quantity }]
      },
      meta: { request_id: 'req_123', timestamp: '2026-02-02T00:00:00Z' }
    })
  })
)

beforeAll(() => server.listen())

describe('addToCart API', () => {
  it('sends correct request format', async () => {
    const result = await addToCart({ productId: 'prod_123', quantity: 2 })

    expect(result.data.items[0].quantity).toBe(2)
    expect(result.meta.request_id).toBeDefined()
  })
})
```

**Target**: 80% coverage on integration points

### 1.5 E2E Tests (Playwright)

**Critical Journeys Only**:

```typescript
// tests/e2e/checkout.spec.ts
import { test, expect } from '@playwright/test'

test.describe('Checkout Flow', () => {
  test('complete purchase journey', async ({ page }) => {
    // Start trace
    await page.context().tracing.start({ screenshots: true, snapshots: true })

    try {
      // Browse products
      await page.goto('/browse')
      await page.click('text=Shop Now')

      // Add to cart
      await page.click('[data-testid="product-card-123"]')
      await page.click('text=Add to Cart')
      await expect(page.locator('[data-testid="cart-count"]')).toHaveText('1')

      // Checkout
      await page.click('text=Checkout')
      await page.click('text=Complete Purchase')

      // Verify redirect to Shopify
      await expect(page).toHaveURL(/checkout\.shopify\.com/)

      // Verify request_id in logs
      const logs = await page.evaluate(() =>
        (window as any).requestLogs
      )
      expect(logs).toHaveLength(3) // browse, add, checkout

    } finally {
      // Save trace for debugging
      await page.context().tracing.stop({ path: 'trace.zip' })
    }
  })
})
```

**Target**: Cover critical paths only (checkout, cart, order tracking)

---

## 2. Contract Testing Strategy

### 2.1 OpenAPI-Driven Contract Tests

**Backend**: Use `openapi-spec-validator` + `schemathesis`

```python
# tests/contract/test_api_contract.py
import pytest
from schemathesis import Case, from_path
from fastapi.testclient import TestClient

# Load OpenAPI spec
schema = from_path("/path/to/openapi.json")

@schema.parametrize()
def test_api_contract(case: Case, client: TestClient):
    """Test all API endpoints against OpenAPI contract"""
    response = case.call_asgi(app)

    # Validate response matches contract
    case.validate_response(response)

    # Verify standard envelope
    assert "data" in response.json()
    assert "meta" in response.json()
    assert "request_id" in response.json()["meta"]
```

**Frontend**: Use `openapi-typescript` + runtime validation

```typescript
// src/api/__tests__/contract.test.ts
import { describe, it, expect } from 'vitest'
import { createClient } from './client'
import type { paths } from './openapi.types'

describe('API Contract Validation', () => {
  it('cart endpoint returns expected shape', async () => {
    const client = createClient()
    const response = await client.POST('/api/v1/cart', {
      body: { product_id: 'prod_123', quantity: 1 }
    })

    // TypeScript compile-time check + runtime validation
    expect(response).toMatchObject({
      data: expect.any(Object),
      meta: {
        request_id: expect.any(String),
        timestamp: expect.any(String)
      }
    })
  })
})
```

### 2.2 Type Synchronization Tests

**Automated Type Sync Check**:

```bash
# scripts/test-type-sync.sh
#!/bin/bash

# Generate TypeScript types from OpenAPI
npx openapi-typescript http://localhost:8000/openapi.json -o src/api/openapi.types.ts

# Compare with committed version
if ! git diff --exit-code src/api/openapi.types.ts; then
  echo "❌ API types out of sync! Regenerate and commit."
  exit 1
fi

echo "✅ API types in sync"
```

### 2.3 Breaking Change Detection

**Pre-commit Hook**:

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Run contract tests before push
pytest tests/contract/ --only-failed

# Check for breaking changes
npx openapi-diff spec/openapi.v1.json spec/openapi.v2.json || {
  echo "❌ Breaking API changes detected!"
  exit 1
}
```

---

## 3. Test Data Management

### 3.1 Backend Fixtures (pytest)

**Factory Pattern**:

```python
# tests/factories.py
import factory
from datetime import datetime, timedelta
from app.models import User, Product, Cart

class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Faker('uuid4')
    messenger_id = factory.Faker('numerify', text='##########')
    created_at = factory.LazyFunction(datetime.utcnow)

class ProductFactory(factory.Factory):
    class Meta:
        model = Product

    id = factory.Faker('uuid4')
    title = factory.Faker('sentence', nb_words=3)
    price = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True)
    shopify_id = factory.Faker('numerify', text='gid://shopify/Product/########')
    created_at = factory.LazyFunction(datetime.utcnow)

class CartFactory(factory.Factory):
    class Meta:
        model = Cart

    id = factory.Faker('uuid4')
    user = factory.SubFactory(UserFactory)
    items = factory.List([
        factory.SubFactory('tests.factories.CartItemFactory')
    ])
```

**Usage in Tests**:

```python
# tests/unit/test_cart.py
def test_cart_total_with_multiple_items():
    cart = CartFactory(
        items=[
            CartItemFactory(price=10.00, quantity=2),
            CartItemFactory(price=5.00, quantity=1),
        ]
    )

    assert cart.total_value == 25.00
```

**Custom Builders**:

```python
# tests/builders.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class CartBuilder:
    """Fluent builder for complex test data"""
    product_id: str = "prod_123"
    quantity: int = 1
    price: float = 29.99
    discount: Optional[float] = None

    with_discount(self, amount: float):
        self.discount = amount
        return self

    build(self) -> Cart:
        return Cart(
            items=[CartItem(
                product_id=self.product_id,
                quantity=self.quantity,
                price=self.price,
                discount=self.discount
            )]
        )

# Usage
def test_cart_with_discount():
    cart = (CartBuilder()
        .with_quantity(3)
        .with_discount(0.1)
        .build())

    assert cart.discounted_total == 80.97
```

### 3.2 Frontend Test Data (MSW Handlers)

**Handler Factories**:

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse, delay } from 'msw'
import { factory } from '@faker-js/faker'

export const productHandlers = [
  http.get('/api/v1/products', async ({ request }) => {
    const url = new URL(request.url)
    const category = url.searchParams.get('category')

    await delay(100) // Simulate network

    return HttpResponse.json({
      data: [
        {
          id: faker.string.uuid(),
          title: faker.commerce.productName(),
          price: parseFloat(faker.commerce.price()),
          category: category || 'all',
        },
      ],
      meta: {
        request_id: faker.string.uuid(),
        timestamp: new Date().toISOString(),
      }
    })
  })
]
```

**Scenario-Based Fixtures**:

```typescript
// src/mocks/scenarios.ts
export const scenarios = {
  emptyCart: {
    cart: { items: [], total: 0 }
  },

  cartWithItems: {
    cart: {
      items: [
        { id: '1', product: mockProduct, quantity: 2 }
      ],
      total: 59.98
    }
  },

  checkoutError: {
    error: 'OUT_OF_STOCK',
    message: 'Product no longer available'
  }
}
```

### 3.3 Database State Management

**Transaction Rollback**:

```python
# tests/conftest.py
@pytest.fixture
def db_session():
    """Database session that rolls back after test"""
    session = SessionLocal()
    session.begin_nested()

    yield session

    session.rollback()
    session.close()
```

**Clean Slate Strategy**:

```python
# tests/fixtures/db.py
@pytest.fixture(scope="function")
def clean_db(db_session):
    """Ensure clean database state"""
    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    yield db_session
```

---

## 4. Coverage Requirements

### 4.1 Coverage Targets by Layer

| Layer | Tool | Target | Enforcement |
|-------|------|--------|-------------|
| Domain Logic | pytest-cov | 95% | `--cov-fail-under=95` |
| API Routes | pytest-cov | 85% | `--cov-fail-under=85` |
| Components | vitest | 90% | `--coverage.enabled=true` |
| Hooks | vitest | 90% | Enforced |
| Integration | pytest-cov | 80% | `--cov-fail-under=80` |
| E2E | playwright | N/A | Critical paths only |

### 4.2 Configuration

**Backend (pytest)**:

```ini
# pytest.ini
[pytest]
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --splitting-algorithm=least_duration
    --numprocesses=auto

cov-report =
    html:htmlcov
    term-missing
    xml

[coverage:run]
omit =
    */tests/*
    */migrations/*
    */__init__.py
    */conftest.py

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

**Frontend (vitest)**:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json'],
      exclude: [
        'node_modules/',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/dist/**',
        '**/build/**',
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 85,
        statements: 90,
      },
    },
  },
})
```

### 4.3 CI Enforcement

**GitHub Actions**:

```yaml
# .github/workflows/test.yml
name: Test Coverage

on: [pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov

      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-fail-under=85

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Run tests with coverage
        run: |
          npm run test:coverage -- --threshold.lines=90

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 5. E2E Strategy

### 5.1 Tracing & Debugging

**Trace on Failure**:

```typescript
// tests/e2e/helpers.ts
import { test } from '@playwright/test'

export const testWithTracing = test.extend({
  page: async ({ page }, use) => {
    await page.context().tracing.start({
      screenshots: true,
      snapshots: true
    })

    try {
      await use(page)
    } catch (error) {
      await page.context().tracing.stop({
        path: `traces/${test.info().title.replace(/\s+/g, '_')}.zip`
      })
      throw error
    }

    await page.context().tracing.stop({ path: `traces/${test.info().title}.zip` })
  }
})
```

**Request ID Correlation**:

```typescript
// src/utils/request-tracker.ts
class RequestTracker {
  private logs: Array<{
    url: string
    method: string
    requestId: string
    timestamp: number
  }> = []

  track(request: Request) {
    const requestId = request.headers.get('x-request-id')
    if (requestId) {
      this.logs.push({
        url: request.url,
        method: request.method,
        requestId,
        timestamp: Date.now(),
      })
    }
  }

  getLogs() {
    return this.logs
  }
}

// Attach to window for E2E access
if (typeof window !== 'undefined') {
  (window as any).requestTracker = new RequestTracker()
}
```

**Backend Correlation**:

```python
# app/middleware/correlation.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
```

### 5.2 E2E Test Stability

**Wait Strategies**:

```typescript
// tests/e2e/support/wait.ts
export const waitForCartUpdate = async (page: Page, expectedCount: number) => {
  await page.waitForFunction(
    (count) => {
      const cartCount = document.querySelector('[data-testid="cart-count"]')
      return cartCount?.textContent === count.toString()
    },
    expectedCount,
    { timeout: 5000 }
  )
}

export const waitForApiResponse = async (page: Page, url: string) => {
  return await page.waitForResponse(
    (response) => response.url().includes(url) && response.status() === 200,
    { timeout: 10000 }
  )
}
```

**Retry Flaky Tests**:

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
  timeout: 30000,
  workers: process.env.CI ? 2 : 4,
})
```

**Test Isolation**:

```typescript
// tests/e2e/hooks.ts
export const test = base.extend<{
  authenticatedPage: Page
}>({
  authenticatedPage: async ({ page }, use) => {
    // Create unique user per test
    const userId = `test_${Date.now()}`

    // Setup auth state
    await page.goto('/auth/login')
    await page.fill('[name="userId"]', userId)
    await page.click('button[type="submit"]')

    await use(page)

    // Cleanup
    await page.request.post('/api/v1/test/cleanup', { userId })
  }
})
```

### 5.3 E2E Test Organization

**By Feature**:

```
tests/e2e/
├── auth/
│   ├── login.spec.ts
│   ├── logout.spec.ts
│   └── session.spec.ts
├── cart/
│   ├── add-item.spec.ts
│   ├── remove-item.spec.ts
│   └── update-quantity.spec.ts
├── checkout/
│   ├── create-checkout.spec.ts
│   └── shopify-redirect.spec.ts
└── orders/
    ├── track-order.spec.ts
    └── order-history.spec.ts
```

**By User Journey**:

```
tests/e2e/journeys/
├── first-time-purchase.spec.ts
├── returning-customer.spec.ts
└── support-handoff.spec.ts
```

---

## 6. Test Infrastructure

### 6.1 Parallel Execution

**Backend (pytest-xdist)**:

```ini
# pytest.ini
[pytest]
addopts =
    -n auto  # Auto-detect CPU cores
    --dist=loadscope  # Balance by test module
```

**Test Splitting by Duration**:

```python
# conftest.py
def pytest_configure(config):
    """Split tests by duration for parallel execution"""
    config.pluginmanager.register(
        LoadFileSchedulingPlugin(),
        "loadscope_plugin"
    )
```

**Frontend (vitest)**:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    threads: true,
    maxThreads: 4,
    minThreads: 1,
    isolate: true, // Isolate each test file
  },
})
```

### 6.2 CI/CD Pipeline

**Parallel Test Stages**:

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run linters
        run: |
          npm run lint
          npm run typecheck
          pytest --flake8

  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: pytest tests/unit/ --shard-id=${{ matrix.shard }} --num-shards=4

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v3
      - name: Run integration tests
        run: pytest tests/integration/ --cov=app

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload traces on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-traces
          path: traces/
```

### 6.3 Test Environment Management

**Docker Compose for Integration Tests**:

```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-db:
    image: postgres:15
    environment:
      POSTGRES_DB: test_shop
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
    ports:
      - "5433:5432"

  test-redis:
    image: redis:7
    ports:
      - "6380:6379"

  test-api:
    build: .
    command: pytest tests/integration/
    environment:
      DATABASE_URL: postgresql://test:test@test-db:5432/test_shop
      REDIS_URL: redis://test-redis:6379
      TEST_MODE: "true"
    depends_on:
      - test-db
      - test-redis
```

**Environment Variables**:

```bash
# .env.test
DATABASE_URL=postgresql://test:test@localhost:5433/test_shop
REDIS_URL=redis://localhost:6380
SHOPIFY_STOREFRONT_URL=https://test-shop.myshopify.com/api/2024-01
SHOPIFY_ACCESS_TOKEN=test_token
TEST_MODE=true
LOG_LEVEL=DEBUG
```

### 6.4 Test Reporting

**HTML Reports**:

```python
# conftest.py
def pytest_configure(config):
    """Generate HTML test report"""
    config.pluginmanager.register(
        HTMLReport('/tmp/test-report'),
        "htmlreport"
    )
```

**Allure Reports**:

```bash
# Generate Allure report
pytest --alluredir=/tmp/allure-results
allure generate /tmp/allure-results --clean -o /tmp/allure-report
```

**Slack Notifications**:

```yaml
# .github/workflows/notify.yml
- name: Slack notification
  if: always()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "Test Results: ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Test Suite*: ${{ github.event.repository.name }}\n*Status*: ${{ job.status }}\n*Branch*: ${{ github.ref_name }}"
            }
          }
        ]
      }
```

---

## 7. Risk Areas & Mitigations

### 7.1 Fragile Tests

**Symptoms**:
- Tests pass locally but fail in CI
- Flaky tests that intermittently fail
- Slow tests that timeout

**Root Causes**:
1. **Time-dependent logic**: Dates, timeouts, delays
2. **External dependencies**: Shopify API, Facebook webhooks
3. **Shared state**: Database conflicts between parallel tests
4. **Network latency**: Unreliable in CI environments

**Mitigations**:

```python
# ❌ BAD: Time-dependent
def test_order_created_today():
    order = Order.create()
    assert order.created_at.date() == datetime.now().date()

# ✅ GOOD: Time-controlled
def test_order_created_with_given_date(freezer):
    freezer.move_to('2026-02-02')
    order = Order.create()
    assert order.created_at.isoformat() == '2026-02-02T00:00:00'
```

```python
# ❌ BAD: External dependency
def test_product_sync():
    products = ShopifyClient.fetch_products()  # Real API call
    assert len(products) > 0

# ✅ GOOD: Mocked external
def test_product_sync_with_mock(mock_shopify):
    mock_shopify.return_value = [mock_product]
    products = ShopifyClient.fetch_products()
    assert len(products) == 1
```

```typescript
// ❌ BAD: Fixed timeout
await page.waitForTimeout(5000)

// ✅ GOOD: Wait for condition
await page.waitForSelector('[data-testid="cart-count"]')
await page.waitForFunction(() => window.cartReady === true)
```

### 7.2 Missed Coverage

**High-Risk Areas**:

1. **Error Handling Paths**:
   - API failures (500, 503)
   - Network timeouts
   - Invalid responses

2. **Edge Cases**:
   - Empty cart
   - Out of stock
   - Expired sessions
   - Race conditions

3. **Security**:
   - Webhook signature validation
   - XSS in user inputs
   - SQL injection attempts

4. **Performance**:
   - Large product catalogs
   - High concurrent users
   - Memory leaks

**Mitigation Strategy**:

```python
# tests/integration/test_error_handling.py
@pytest.mark.parametrize("status_code,scenario", [
    (500, "shopify_unavailable"),
    (503, "rate_limited"),
    (404, "product_not_found"),
])
def test_checkout_handles_shopify_errors(client, status_code, scenario):
    """Test checkout handles all Shopify error scenarios"""
    with mock_shopify_error(status_code):
        response = client.post("/api/v1/checkout")

        assert response.status_code == 503
        assert "retryable" in response.json()["meta"]
```

```python
# tests/unit/test_edge_cases.py
def test_cart_with_zero_quantity():
    """Test cart handles invalid quantity"""
    cart = Cart()
    result = cart.add_item(CartItem(quantity=0))

    assert result.success is False
    assert result.error_code == "INVALID_QUANTITY"

def test_cart_with_negative_price():
    """Test cart handles negative price"""
    with pytest.raises(ValidationError):
        CartItem(price=-10.00)
```

### 7.3 Test Data Contamination

**Symptoms**:
- Tests interfere with each other
- Increasing data in test database
- Unpredictable test results

**Mitigations**:

```python
# conftest.py
@pytest.fixture(autouse=True)
def isolation(db_session):
    """Automatically isolate each test"""
    db_session.begin_nested()
    yield
    db_session.rollback()
```

```python
# tests/conftest.py
@pytest.fixture(scope="function")
def clean_redis(redis_client):
    """Clean Redis before each test"""
    redis_client.flushall()
    yield redis_client
    redis_client.flushall()
```

### 7.4 Slow Test Suite

**Symptoms**:
- Tests take >10 minutes
- Developers skip running tests
- Slow feedback loops

**Mitigations**:

1. **Profile Test Duration**:

```bash
# Find slowest tests
pytest --durations=20
```

2. **Split Test Suites**:

```yaml
# .github/workflows/test.yml
jobs:
  quick-tests:
    # Fast unit tests < 2min
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/unit/ -k "not slow"

  full-tests:
    # Only run on main branch
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - run: pytest
```

3. **Optimize Database Operations**:

```python
# ❌ BAD: Separate inserts per test
for i in range(100):
    ProductFactory.create()

# ✅ GOOD: Bulk create
ProductFactory.create_batch(100)
```

### 7.5 E2E Maintenance Burden

**Symptoms**:
- High E2E test maintenance cost
- Frequent selector changes
- Brittle page interactions

**Mitigations**:

1. **Use Stable Selectors**:

```typescript
// ❌ BAD: CSS classes
await page.click('.btn-primary')

// ✅ GOOD: Test IDs
await page.click('[data-testid="checkout-button"]')
```

2. **Page Object Model**:

```typescript
// pages/CartPage.ts
export class CartPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/cart')
  }

  async addItem(productId: string) {
    await this.page.click(`[data-testid="add-${productId}"]`)
  }

  async getCartCount() {
    return await this.page.textContent('[data-testid="cart-count"]')
  }

  async checkout() {
    await this.page.click('[data-testid="checkout-button"]')
  }
}

// Usage
const cart = new CartPage(page)
await cart.goto()
await cart.addItem('prod_123')
await cart.checkout()
```

3. **Visual Regression Testing**:

```typescript
// tests/visual/checkout.spec.ts
test('checkout page visual', async ({ page }) => {
  await page.goto('/checkout')
  await expect(page).toHaveScreenshot('checkout.png')
})
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

- [ ] Set up pytest with coverage and xdist
- [ ] Set up vitest with coverage
- [ ] Create base fixtures and factories
- [ ] Implement CI pipeline for unit tests
- [ ] Add contract testing framework

### Phase 2: Integration (Week 3-4)

- [ ] Build integration test suite with Docker
- [ ] Add MSW for frontend API mocking
- [ ] Implement OpenAPI contract validation
- [ ] Set up test database fixtures
- [ ] Add parallel execution

### Phase 3: E2E (Week 5-6)

- [ ] Set up Playwright with tracing
- [ ] Implement critical user journeys
- [ ] Add request ID correlation
- [ ] Configure CI for E2E tests
- [ ] Build test reporting dashboard

### Phase 4: Optimization (Week 7-8)

- [ ] Profile and optimize slow tests
- [ ] Implement test splitting strategies
- [ ] Add performance regression tests
- [ ] Set up automated coverage reporting
- [ ] Document testing best practices

---

## 9. Metrics & KPIs

### Test Health Metrics

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| Unit Test Coverage | 90% | - | 📈 |
| Integration Coverage | 80% | - | 📈 |
| E2E Test Pass Rate | 95% | - | - |
| Test Suite Duration | <10min | - | ⬇️ |
| Flaky Test Rate | <2% | - | ⬇️ |
| CI Success Rate | 98% | - | 📈 |

### Coverage by Module

```
domain/         ████████░░ 90%
api/            ███████░░░░ 80%
services/       ███████░░░░ 80%
components/     ████████░░ 90%
hooks/          ████████░░ 90%
```

---

## 10. Conclusion

The Party Mode testing strategy provides a comprehensive, layered approach to quality assurance:

1. **Strong Foundation**: 90% unit coverage ensures business logic correctness
2. **Contract Guarantees**: OpenAPI-driven testing prevents API breakage
3. **Fast Feedback**: Parallel execution keeps test suite under 10 minutes
4. **Critical E2E**: Focus on user journeys, not coverage
5. **Risk Mitigation**: Proactive identification of fragile tests and missed coverage

**Key Success Factors**:

- Testability built into architecture from day one
- Co-located tests for immediate feedback
- Automated type sync prevents contract drift
- Parallel execution keeps CI fast
- Comprehensive tracing for debugging

**Next Steps**:

1. Implement Phase 1 foundation (pytest + vitest)
2. Create base fixtures and factories
3. Set up CI pipeline with coverage gates
4. Begin integration test development
5. Gradually add E2E for critical paths

---

**Appendix A: Tool Versions**

```txt
pytest==7.4.3
pytest-cov==4.1.0
pytest-xdist==3.5.0
pytest-asyncio==0.21.1
vitest==1.0.4
@playwright/test==1.40.1
msw==2.0.0
schemathesis==3.30.0
openapi-typescript==6.7.0
faker==20.1.0
factory-boy==3.3.0
freezegun==1.4.0
```

**Appendix B: Reference Links**

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Contract Testing with Schemathesis](https://schemathesis.readthedocs.io/)
- [Testing Library Guidelines](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
