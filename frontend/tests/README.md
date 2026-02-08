# Frontend Tests

Test suite for the Shop frontend application using Playwright (E2E, API) and Vitest (Unit, Service, Store).

---

## Test Structure

```
tests/
├── e2e/                    # End-to-end browser tests
│   └── story-*.spec.ts     # Story-based E2E test suites
├── api/                    # API-level tests
│   └── *.spec.ts           # API contract tests
├── services/               # Service layer tests
│   └── *.spec.ts           # Business logic tests
├── stores/                 # State management tests
│   └── *.spec.ts           # Zustand store tests
├── unit/                   # Unit tests
│   └── *.spec.ts           # Pure function/utility tests
├── component/              # Component tests (if using CT)
│   └── *.spec.ts           # Isolated component tests
└── support/                # Test utilities
    ├── fixtures/           # Reusable test fixtures
    ├── factories/          # Data factories using faker
    └── helpers/            # Helper utilities
```

---

## Running Tests

### Run All Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run all unit/service/store tests
npm test
```

### Run Specific Test Levels

```bash
# E2E tests only
npm run test:e2e

# API tests only
npm run test:api

# Service tests only
npm run test:services

# Store tests only
npm run test:stores

# Unit tests only
npm run test:unit
```

### Run With UI

```bash
# Playwright UI mode
npm run test:e2e:ui

# Vitest UI mode
npm run test:ui
```

### Debug Tests

```bash
# Debug Playwright tests
npm run test:e2e:debug

# Run tests in headed mode
npm run test:e2e:headed
```

---

## Test Priorities

Tests are tagged with priority levels to enable selective execution:

| Priority | Meaning | When to Run |
|----------|---------|-------------|
| **[P0]** | Critical paths | Every commit |
| **[P1]** | High importance | Every PR |
| **[P2]** | Medium importance | Nightly |
| **[P3]** | Low importance | Manual/Ad-hoc |

### Running by Priority

```bash
# Run only P0 tests (critical paths)
npx playwright test --grep "@p0"

# Run P0 and P1 tests
npx playwright test --grep "@p0|@p1"
```

---

## Test Conventions

### Given-When-Then Format

All tests follow the Given-When-Then structure for clarity:

```ts
test('[P1] should display cost summary', async ({ page }) => {
  // Given: User is on the costs page
  await page.goto('/costs');

  // When: Data has loaded
  await page.waitForLoadState('networkidle');

  // Then: Cost summary should be visible
  await expect(page.getByText('Total Cost')).toBeVisible();
});
```

### Test Naming

Test names should:
- Start with priority tag: `[P0]`, `[P1]`, `[P2]`, `[P3]`
- Describe what is being tested
- Be descriptive but concise
- Use "should" for positive tests

```ts
// ✅ Good
test('[P1] should fetch cost summary successfully', async () => {});

// ❌ Bad
test('test summary', async () => {});
```

---

## Using Fixtures

### Cost Tracking Fixtures

Import fixtures from `@/tests/support/fixtures/costTracking`:

```ts
import {
  mockConversationCostResponse,
  mockCostSummaryResponse,
  mockEmptyCostSummaryResponse,
  mockAuthToken,
  clearMockAuth,
} from '@/tests/support/fixtures/costTracking';

// Mock a successful response
global.fetch = mockCostTrackingFetch(mockCostSummaryResponse());

// Setup auth token
mockAuthToken('my-test-token');

// Cleanup after test
clearMockAuth();
```

---

## Using Data Factories

Factories generate realistic test data using `@faker-js/faker`:

```ts
import {
  createConversationCost,
  createCostSummary,
  createCostSummaryParams,
  createManyConversationCosts,
} from '@/tests/support/factories/costFactory';

// Create a conversation cost with defaults
const cost = createConversationCost();

// Create with overrides
const cost = createConversationCost({
  provider: 'openai',
  model: 'gpt-4o-mini',
  totalCostUsd: 0.5,
});

// Create multiple
const costs = createManyConversationCosts(5, { provider: 'ollama' });
```

---

## Using Helpers

Helper utilities for common test operations:

```ts
import { waitFor, retry, assertions, cleanup } from '@/tests/support/helpers/testHelpers';

// Wait for condition
await waitFor(() => page.getByText('Loaded').isVisible(), {
  timeout: 5000,
  message: 'Element did not appear',
});

// Retry with backoff
await retry(() => {
  await expect(page.getByText('Success')).toBeVisible();
}, { maxAttempts: 3 });

// Custom assertions
await assertions.isVisibleAndEnabled(page, 'button[type="submit"]');
await assertions.hasText(page, '.summary', 'Total Cost');

// Cleanup
cleanup.clearAllStorage();
```

---

## Best Practices

### ✅ Do

- Use `data-testid` attributes for selectors (not CSS classes)
- Apply network-first pattern (intercept routes before navigation)
- Use fixtures and factories (avoid hardcoded data)
- Clean up after tests (timers, storage, mocks)
- Make tests deterministic (no conditional flows)
- Use explicit waits (not hardcoded timeouts)
- Test one thing per test (atomic design)

### ❌ Don't

- Use CSS class selectors (fragile, implementation details)
- Use `page.waitForTimeout()` (flaky, slow)
- Use conditional `if (isVisible())` (non-deterministic)
- Hardcode test data (use factories instead)
- Share state between tests (isolation required)
- Test implementation details (test behavior, not code)
- Use try-catch for test logic (only for cleanup)

---

## Test Writing Guidelines

### E2E Tests

- Focus on critical user journeys
- Test end-to-end flows, not implementation
- Use network-first pattern for API mocking
- Test at the UI level (buttons, forms, navigation)

### API Tests

- Test service contracts
- Validate request/response formats
- Test error scenarios (400, 401, 404, 500)
- Mock responses, don't call real APIs

### Service/Store Tests

- Test business logic in isolation
- Mock external dependencies
- Test state management (actions, getters)
- Test error handling

### Unit Tests

- Test pure functions
- No external dependencies
- Fast, focused tests
- Edge cases and error handling

---

## Common Patterns

### Network-First Pattern

Always intercept routes BEFORE navigation:

```ts
test('should handle API errors', async ({ page }) => {
  // ✅ Correct: Intercept first
  await page.route('**/api/costs/**', route =>
    route.fulfill({ status: 500, body: '{"error": "Server Error"}' })
  );

  // Then navigate
  await page.goto('/costs');

  // ❌ Wrong: Navigate then intercept
  await page.goto('/costs');
  await page.route('**/api/costs/**', ...);
});
```

### Mock Service Pattern

```ts
import { costTrackingService } from '@/services/costTracking';

// Setup mock
global.fetch = jest.fn().mockResolvedValue({
  ok: true,
  status: 200,
  json: async () => ({ data: mockData, meta: {} }),
});

// Test
const result = await costTrackingService.getCostSummary({});

// Verify
expect(global.fetch).toHaveBeenCalledWith('/api/costs/summary', expect.any(Object));
```

### Store Testing Pattern

```ts
import { useCostTrackingStore } from '@/stores/costTrackingStore';

test('should fetch cost summary', async () => {
  // Setup mock
  global.fetch = jest.fn().mockResolvedValue({ data: mockData });

  // Action
  await act(async () => {
    await useCostTrackingStore.getState().fetchCostSummary({});
  });

  // Assert
  const state = useCostTrackingStore.getState();
  expect(state.costSummary).toEqual(mockData);
  expect(state.lastUpdate).not.toBeNull();
});
```

---

## Troubleshooting

### Tests Timeout

- Increase timeout in playwright.config.ts
- Check for race conditions
- Verify server is running

### Tests Flaky

- Remove hard waits (`waitForTimeout`)
- Use explicit waits (`waitForSelector`)
- Apply network-first pattern
- Check for race conditions in state

### Tests Fail Locally

- Ensure dev server is running
- Check environment variables
- Verify database state
- Clear browser cache

### Tests Fail in CI

- Check CI environment configuration
- Verify dependencies are installed
- Check for time zone issues
- Ensure proper cleanup between tests

---

## Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Faker.js](https://fakerjs.dev/)

---

## Questions?

For questions about testing, please refer to:
- Project README for setup instructions
- BMad TEA documentation for test architecture
- Team coding standards for style guidelines
