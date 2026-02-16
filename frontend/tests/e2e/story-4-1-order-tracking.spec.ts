/**
 * Order Tracking E2E Tests
 *
 * Story 4-1: Natural Language Order Tracking
 * Tests the complete user journey for tracking orders via bot conversation
 *
 * Acceptance Criteria:
 * - AC1: Intent Classification - "Where's my order?" classified as order_tracking with confidence >= 0.80
 * - AC2: Order Lookup by Customer - returns order details by platform_sender_id
 * - AC3: Order Not Found - asks for order number when no orders found
 * - AC4: Order Lookup by Order Number - returns order when order number provided
 * - AC5: Response Time < 2 seconds (P95)
 *
 * NOTE: AC2-AC5 are primarily tested via backend integration tests
 * (backend/tests/integration/test_order_tracking_flow.py) because order tracking
 * is implemented via Messenger message processing, not REST API endpoints.
 * REST API endpoints for order tracking would be a future enhancement.
 *
 * @tags e2e story-4-1 order-tracking bot-conversation
 */

import { test as base, expect, APIRequestContext } from '@playwright/test';

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
  apiContext: APIRequestContext;
};

const test = base.extend<MyFixtures>({
  apiContext: async ({ playwright }, use) => {
    const context = await playwright.request.newContext({
      baseURL: process.env.API_URL || 'http://localhost:8000',
    });
    await use(context);
  },
  authenticatedPage: async ({ page }, use) => {
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'test-merchant-order-tracking',
            email: 'order-tracking-test@test.com',
            name: 'Order Tracking Test Merchant',
            hasStoreConnected: false,
          },
          meta: {
            sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
          },
        }),
      });
    });

    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 'test-merchant-order-tracking',
          email: 'order-tracking-test@test.com',
          name: 'Order Tracking Test Merchant',
          hasStoreConnected: false,
        },
        sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        isLoading: false,
        error: null,
      };

      const mockOnboardingState = {
        state: {
          completedSteps: ['prerequisites', 'deployment', 'integrations', 'bot-config'],
          currentPhase: 'complete',
          personalityConfigured: true,
          businessInfoConfigured: true,
          botNamed: true,
          greetingsConfigured: true,
          pinsConfigured: true,
          isFullyOnboarded: true,
          onboardingCompletedAt: new Date().toISOString(),
        },
        version: 0,
      };

      localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
      localStorage.setItem('shop_onboarding_phase_progress', JSON.stringify(mockOnboardingState));
    });

    await use(page);
  },
});

test.describe.configure({ mode: 'parallel' });

/**
 * ============================================================================
 * AC1: Intent Classification - REST API Endpoint Tests (SKIPPED)
 * ============================================================================
 * 
 * Status: Tests skipped - REST API endpoint not yet implemented
 * 
 * Intent classification is currently implemented as an internal service
 * (backend/app/services/intent/intent_classifier.py) and tested via:
 * - Backend unit tests: backend/app/services/intent/test_intent_classifier.py
 * - Edge case tests: backend/app/services/intent/test_story_2_1_edge_cases.py
 * 
 * To enable these tests:
 * 1. Create POST /api/v1/classify-intent endpoint in backend/app/api/
 * 2. Remove .skip from test.describe below
 * 3. Run: npx playwright test tests/e2e/story-4-1-order-tracking.spec.ts
 * 
 * Priority: P3 (nice-to-have, internal service is tested)
 * ============================================================================
 */
test.describe.skip('Story 4-1: Order Tracking - Intent Classification [AC1] - REST API', () => {
  test('should classify "Where\'s my order?" as order_tracking intent', async ({ apiContext }) => {
    const startTime = Date.now();

    const response = await apiContext.post('/api/v1/classify-intent', {
      data: { message: "Where's my order?" },
    });

    const responseTime = Date.now() - startTime;

    expect(response.ok()).toBeTruthy();

    const result = await response.json();
    expect(result.intent).toBe('order_tracking');
    expect(result.confidence).toBeGreaterThanOrEqual(0.80);

    expect(responseTime).toBeLessThan(2000);
  });

  test('should classify "Order status" as order_tracking intent', async ({ apiContext }) => {
    const response = await apiContext.post('/api/v1/classify-intent', {
      data: { message: 'Order status' },
    });

    expect(response.ok()).toBeTruthy();

    const result = await response.json();
    expect(result.intent).toBe('order_tracking');
    expect(result.confidence).toBeGreaterThanOrEqual(0.80);
  });

  test('should classify "Track my order" as order_tracking intent', async ({ apiContext }) => {
    const response = await apiContext.post('/api/v1/classify-intent', {
      data: { message: 'Track my order' },
    });

    expect(response.ok()).toBeTruthy();

    const result = await response.json();
    expect(result.intent).toBe('order_tracking');
    expect(result.confidence).toBeGreaterThanOrEqual(0.80);
  });

  test('should classify "What happened to order #1234?" as order_tracking intent', async ({ apiContext }) => {
    const response = await apiContext.post('/api/v1/classify-intent', {
      data: { message: 'What happened to order #1234?' },
    });

    expect(response.ok()).toBeTruthy();

    const result = await response.json();
    expect(result.intent).toBe('order_tracking');
    expect(result.confidence).toBeGreaterThanOrEqual(0.80);
  });
});

/**
 * AC5: Response Time - Skipped until REST API endpoint is implemented
 * (see AC1 note above)
 */
test.describe.skip('Story 4-1: Order Tracking - Response Time [AC5] - REST API', () => {
  test('intent classification should respond within 2 seconds', async ({ apiContext }) => {
    const iterations = 5;
    const times: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();
      await apiContext.post('/api/v1/classify-intent', {
        data: { message: "Where's my order?" },
      });
      times.push(Date.now() - startTime);
    }

    const p95Index = Math.ceil(times.length * 0.95) - 1;
    const sortedTimes = [...times].sort((a, b) => a - b);
    const p95Time = sortedTimes[p95Index];

    expect(p95Time).toBeLessThan(2000);
  });
});

test.describe('Story 4-1: Order Tracking - Accessibility', () => {
  test('should have accessible order status announcements', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/conversations');

    const orderStatusElements = authenticatedPage.locator('[data-testid="order-status"]');

    const count = await orderStatusElements.count();

    for (let i = 0; i < count; i++) {
      const element = orderStatusElements.nth(i);
      const ariaLabel = await element.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel).toContain('Order status');
    }
  });
});

/**
 * ============================================================================
 * BACKEND INTEGRATION TEST COVERAGE
 * ============================================================================
 * 
 * The following acceptance criteria are covered by backend integration tests
 * in backend/tests/integration/test_order_tracking_flow.py:
 * 
 * - AC2: Order Lookup by Customer
 *   → TestOrderTrackingByCustomer (3 tests)
 * 
 * - AC3: Order Not Found (asks for order number)
 *   → test_full_flow_no_orders_ask_for_number
 * 
 * - AC4: Order Lookup by Order Number
 *   → TestOrderTrackingByNumber (3 tests)
 * 
 * - Security: Merchant boundary isolation
 *   → TestMerchantSecurityBoundary (2 tests)
 * 
 * - Edge Cases: Unicode/special characters
 *   → TestUnicodeAndSpecialCharacters (4 tests)
 * 
 * - Edge Cases: Multiple orders (returns most recent)
 *   → TestMultipleOrders
 * 
 * - State Management: Pending state timeout (5 minutes)
 *   → TestPendingStateTimeout (3 tests)
 * 
 * Total: 34 backend integration tests covering database and service layer
 * ============================================================================
 */
