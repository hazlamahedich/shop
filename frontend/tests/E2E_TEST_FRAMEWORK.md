# E2E Test Framework Documentation

## Overview

This E2E test framework implements a production-ready testing infrastructure aligned with the 70/20/10 test pyramid philosophy. It provides a scalable, maintainable foundation for end-to-end testing of the shop application.

## Test Count

- **Total E2E Tests**: 876 tests (includes variations across browsers/viewports)
- **Core Unique Tests**: ~40 test scenarios
- **Test Types**: Critical path (smoke), regression, accessibility, cross-browser

## Directory Structure

```
frontend/tests/
├── e2e/
│   ├── critical/                    # Smoke/critical path tests
│   │   ├── onboarding.spec.ts       # Complete onboarding journey
│   │   ├── integration-setup.spec.ts # Multi-integration workflows
│   │   └── authentication.spec.ts   # Authentication flows (mocked)
│   ├── journeys/                    # Multi-step user journeys
│   │   └── webhook-verification.spec.ts
│   ├── regression/                  # Regression & cross-browser
│   │   ├── cross-browser/
│   │   │   ├── firefox.spec.ts
│   │   │   ├── webkit.spec.ts
│   │   │   └── mobile.spec.ts
│   │   ├── error-recovery.spec.ts
│   │   └── accessibility.spec.ts
│   └── migrated/                    # Original tests migrated to new patterns
│       ├── onboarding.spec.ts
│       ├── webhook-verification.spec.ts
│       └── integrations.spec.ts
├── fixtures/                        # TEA-style fixture composition
│   ├── base.fixture.ts              # Core fixture composition using mergeTests
│   ├── auth.fixture.ts              # Mock authentication fixtures
│   ├── merchant.fixture.ts          # Merchant context fixtures
│   ├── api-client.fixture.ts        # API-first setup helpers
│   └── test-helper.ts               # Legacy helpers (backward compatible)
├── factories/                       # Data factories using @faker-js/faker
│   ├── merchant.factory.ts          # Parallel-safe merchant data generation
│   ├── facebook.factory.ts          # Facebook integration test data
│   └── shopify.factory.ts           # Shopify integration test data
├── helpers/                         # API client, selectors, assertions
│   ├── api-client.ts                # API-first setup (10-50x faster than UI)
│   ├── selectors.ts                 # Enhanced PageObjects pattern
│   ├── assertions.ts                # Custom assertions for common scenarios
│   ├── performance-monitor.ts       # Performance metrics and baselines
│   └── flaky-test-wrapper.ts        # Retry logic for flaky tests
├── templates/                       # Test templates and patterns
│   └── test-template.spec.ts        # ATDD checklist template
└── test-setup.ts                    # Global setup (future)
```

## Key Features

### 1. TEA-Style Fixture Composition

```typescript
// Use base fixtures in tests
import { test } from '../fixtures/base.fixture';

test('my test', async ({ authenticatedPage, merchant }) => {
  // Test with authenticated page and merchant context
});
```

### 2. Data Factories with Faker

```typescript
import { createMerchantData, createMultipleMerchants } from '../factories/merchant.factory';

// Generate single merchant with overrides
const merchant = createMerchantData({ platform: 'railway' });

// Generate multiple unique merchants
const merchants = createMultipleMerchants(5);
```

### 3. API-First Setup

```typescript
import { quickSetup } from '../helpers/api-client';

// 10-50x faster than UI setup
const merchant = await quickSetup(request, ['facebook', 'shopify']);
```

### 4. PageObjects Pattern

```typescript
import { PrerequisiteChecklist, DeploymentWizard } from '../helpers/selectors';

await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);
const wizard = page.locator(DeploymentWizard.container);
```

### 5. Custom Assertions

```typescript
import { assertPrerequisiteComplete, assertDeployButtonEnabled } from '../helpers/assertions';

await assertPrerequisiteComplete(page, 'cloudAccount');
await assertDeployButtonEnabled(page);
```

### 6. Performance Monitoring

```typescript
import { assertPageLoadBaseline } from '../helpers/performance-monitor';

await assertPageLoadBaseline(page, {
  domContentLoaded: 2000,
  loadComplete: 5000,
});
```

## Running Tests

### Local Development

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI mode
npm run test:e2e:ui

# Run with headed mode (see browser)
npm run test:e2e:headed

# Debug tests
npm run test:e2e:debug

# Run specific project
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
npx playwright test --project="Mobile Chrome"
```

### CI/CD (GitHub Actions)

The `.github/workflows/e2e-tests.yml` file defines:

- **e2e-chromium**: Parallel sharding (3 shards)
- **e2e-firefox**: Firefox compatibility
- **e2e-webkit**: Safari (runs on macOS)
- **smoke-tests**: Quick feedback (@smoke tag)
- **mobile-tests**: Mobile viewport testing

## Writing New Tests

### Using the Test Template

```bash
cp tests/templates/test-template.spec.ts tests/e2e/critical/my-new-test.spec.ts
```

### Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { PrerequisiteChecklist } from '../../helpers/selectors';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.afterEach(async ({ page }) => {
    // Cleanup
  });

  test('should do something specific @smoke', async ({ page }) => {
    // ARRANGE
    // ACT
    // ASSERT
  });
});
```

### ATDD Checklist

Each test should include:

- [ ] Test covers the complete user journey
- [ ] All acceptance criteria are validated
- [ ] Edge cases are considered
- [ ] Error handling is tested
- [ ] State persistence is verified
- [ ] Accessibility: Keyboard navigation works
- [ ] Accessibility: Screen reader announcements work
- [ ] WCAG 2.1 AA compliance validated
- [ ] Cleanup: Test data cleared after test

## Test Tags

- `@smoke`: Quick critical path test
- `@regression`: Prevents future breaks
- `@a11y`: Accessibility-focused test
- `@mobile`: Mobile-specific test
- `@cross-browser`: Cross-browser compatibility

## Performance Baselines

Default thresholds (can be customized):

- DOM Content Loaded: 2000ms
- Page Load Complete: 5000ms
- First Paint: 1000ms
- First Contentful Paint: 1800ms
- Click Response: 100ms
- Form Submission: 500ms

## Success Metrics

### Quantitative
- Test Count: 876 tests (all variations)
- Execution Time: ~5-15 minutes (depending on scope)
- Coverage: All critical user paths validated
- Cross-Browser: Chromium, Firefox, WebKit, mobile

### Qualitative
- Maintainability: Clear patterns and structure
- Debuggability: Rich artifacts (traces, videos, screenshots)
- Documentation: ATDD checklists and inline comments

## Best Practices

1. **Use API-first setup** - Much faster than UI interactions
2. **Parallel-safe data** - Factories generate unique data
3. **Clean up after tests** - Prevent test pollution
4. **Tag your tests** - Use @smoke for quick feedback
5. **Follow the template** - Consistent test structure
6. **Test critical paths** - Focus on user journeys, not implementation
7. **Mock external services** - Facebook, Shopify, LLM providers
8. **Test accessibility** - Keyboard navigation and screen readers

## Troubleshooting

### Flaky Tests

Use the flaky test wrapper:

```typescript
import { stableTest } from '../../helpers/flaky-test-wrapper';

stableTest('potentially flaky test', async ({ page }) => {
  // Test code with automatic retry
});
```

### Test Isolation Issues

Ensure proper cleanup in `afterEach`:

```typescript
test.afterEach(async ({ page }) => {
  await clearStorage(page);
  await cleanupTestData(request);
});
```

### Slow Tests

Consider:
- Using API-first setup instead of UI
- Reducing wait times
- Running tests in parallel
- Focusing on critical paths only

## Dependencies

- `@playwright/test`: E2E test framework
- `@faker-js/faker`: Data generation

## References

- [Playwright Documentation](https://playwright.dev)
- [Testing Best Practices](https://kentcdodds.com/blog/common-mistakes-with-react-testing-library)
- [WCAG 2.1 AA Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
