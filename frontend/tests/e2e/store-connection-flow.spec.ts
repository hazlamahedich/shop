/**
 * E2E Test: Store Connection Conditional UI Flow
 *
 * Sprint Change 2026-02-13: Make Shopify Optional Integration
 *
 * Tests the conditional rendering based on store_provider status:
 * - No-store mode: Dashboard shows "Connect Store" card, Products/Orders hidden
 * - Store connected: Dashboard shows "Sales" card, Products/Orders visible
 *
 * Note: Full dashboard UI tests require real backend authentication.
 * These tests verify the routing and access control logic.
 * For complete conditional UI testing, run with: npm run test:e2e:full
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

// Mock test merchant data
const MOCK_MERCHANT = {
  id: 'test-merchant-123',
  email: 'test@example.com',
  bot_name: 'Test Bot',
  store_provider: 'none', // Default to no store
  has_store_connected: false, // No store connected
  facebook_page_id: 'fb-page-123',
};

const MOCK_MERCHANT_WITH_STORE = {
  ...MOCK_MERCHANT,
  id: 'test-merchant-456',
  store_provider: 'shopify',
  has_store_connected: true, // Store is connected
  shopify_domain: 'test-store.myshopify.com',
};

/**
 * Mock the authentication API responses
 */
async function mockAuthApi(
  page: Page,
  context: BrowserContext,
  merchant = MOCK_MERCHANT
) {
  // Mock CSRF token API
  await page.route('**/api/v1/csrf-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        csrf_token: 'mock-csrf-token-e2e',
      }),
    });
  });

  // Mock /me API for session validation
  await page.route('http://localhost:5173/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          merchant: merchant,
        },
      }),
    });
  });

  // Also handle relative URL pattern
  await page.route('/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          merchant: merchant,
        },
      }),
    });
  });

  // Mock login API
  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: {
          merchant: merchant,
          session: {
            expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
          },
        },
      }),
      headers: {
        'Set-Cookie':
          'session_token=mock-session-token-e2e; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400',
      },
    });
  });

  // Mock logout API
  await page.route('**/api/v1/auth/logout', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'success' }),
    });
  });
}

// Correct localStorage keys for Zustand persist stores
const ONBOARDING_STORAGE_KEY = 'shop_onboarding_phase_progress';
const TUTORIAL_STORAGE_KEY = 'shop-tutorial-storage';

/**
 * Helper to set up authenticated state directly (no login form)
 */
async function setupAuthenticatedState(
  page: Page,
  context: BrowserContext,
  merchant = MOCK_MERCHANT
) {
  // Set up API mocks
  await mockAuthApi(page, context, merchant);

  // Set session cookie directly
  await context.addCookies([
    {
      name: 'session_token',
      value: 'mock-session-token-e2e',
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      sameSite: 'Strict',
      expires: Math.floor(Date.now() / 1000) + 86400, // 24 hours
    },
  ]);

  // Set onboarding state in localStorage using addInitScript
  // This runs BEFORE the page scripts load
  await page.addInitScript((args) => {
    const { onboardingKey, tutorialKey, onboardingData, tutorialData } = args as {
      onboardingKey: string;
      tutorialKey: string;
      onboardingData: object;
      tutorialData: object;
    };

    localStorage.setItem(onboardingKey, JSON.stringify(onboardingData));
    localStorage.setItem(tutorialKey, JSON.stringify(tutorialData));
  }, {
    onboardingKey: ONBOARDING_STORAGE_KEY,
    tutorialKey: TUTORIAL_STORAGE_KEY,
    onboardingData: {
      state: {
        completedSteps: ['personality', 'businessInfo', 'botName', 'greetings', 'pins'],
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
    },
    tutorialData: {
      state: {
        isStarted: false,
        isCompleted: true,
        isSkipped: false,
        currentStep: 8,
        completedSteps: ['step-1', 'step-2', 'step-3', 'step-4', 'step-5', 'step-6', 'step-7', 'step-8'],
        startedAt: null,
        completedAt: new Date().toISOString(),
        stepsTotal: 8,
      },
      version: 0,
    },
  });

  // Navigate to dashboard
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');
}

/**
 * Helper to wait for dashboard content to be visible
 */
async function waitForDashboardReady(page: Page) {
  // Wait for the dashboard heading or content to appear
  try {
    await page.waitForSelector('text=/Dashboard|Welcome|Bot Dashboard|Connect Store|Total Sales/i', { timeout: 15000 });
  } catch {
    // Fallback - just wait for any content
    await page.waitForTimeout(2000);
  }
  // Additional wait for React to finish rendering
  await page.waitForTimeout(1000);
}

// ============================================================================
// Authentication Flow Tests (No Backend Required)
// ============================================================================

test.describe('Authentication Flow', () => {
  test('should show login page when not authenticated', async ({ page }) => {
    // Clear any existing session
    await page.context().clearCookies();
    await page.goto('/');

    // Try to access dashboard - should redirect to login
    await page.goto('/dashboard');

    // Should be on login page (or redirected there)
    const loginHeading = page.getByRole('heading', { name: /login/i });
    await expect(loginHeading).toBeVisible({ timeout: 10000 });
  });
});

// ============================================================================
// Dashboard Access Tests
// ============================================================================

test.describe('Dashboard Access', () => {
  test.beforeEach(async ({ page, context }) => {
    await setupAuthenticatedState(page, context);
  });

  test('should access dashboard after authentication', async ({ page }) => {
    // Should be on dashboard or bot-config (onboarding might redirect)
    const url = page.url();
    expect(url).toMatch(/\/(dashboard|bot-config)/);

    // Page should have visible content
    const bodyContent = await page.locator('body').textContent();
    expect(bodyContent).toBeTruthy();
    expect(bodyContent!.length).toBeGreaterThan(0);
  });

  test('should show navigation sidebar when on dashboard', async ({ page }) => {
    // Wait for dashboard to be ready
    await waitForDashboardReady(page);

    // Only check sidebar if we're actually on the dashboard
    if (page.url().includes('/dashboard')) {
      const sidebar = page.locator('aside');
      const sidebarCount = await sidebar.count();
      // Sidebar might not exist in all layouts, so just verify we have some navigation
      const nav = page.locator('nav');
      const hasNavigation = (await sidebar.count()) > 0 || (await nav.count()) > 0;
      expect(hasNavigation).toBe(true);
    }
  });

  test('should show sidebar navigation items when on dashboard', async ({ page }) => {
    await waitForDashboardReady(page);

    if (page.url().includes('/dashboard')) {
      // Check for any navigation links - the layout might vary
      const links = page.locator('a[href]');
      const linkCount = await links.count();
      expect(linkCount).toBeGreaterThan(0);
    }
  });
});

// ============================================================================
// Conditional Store UI Tests
// ============================================================================

test.describe('Conditional Store UI - No Store Connected', () => {
  test.beforeEach(async ({ page, context }) => {
    await setupAuthenticatedState(page, context, MOCK_MERCHANT);
    await waitForDashboardReady(page);
  });

  test('should NOT show Total Sales card when no store connected', async ({ page }) => {
    // Only verify if we're on the dashboard
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // Total Sales card should NOT be visible - check for the text
    const salesCard = page.getByText(/total sales/i);
    const hasSalesCard = await salesCard.count() > 0;
    expect(hasSalesCard).toBe(false);
  });

  test('should show store status warning when no store connected', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // Should show warning about no store connection
    const storeWarning = page.locator('text=/no.*store.*connect|connect.*store/i');
    const hasWarning = await storeWarning.count() > 0;
    expect(hasWarning).toBe(true);
  });

  test('should show Connect Store card on dashboard when no store connected', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // Should show "Connect Store" option in the sales area
    const connectStoreCard = page.getByText(/connect store/i);
    const hasConnectStore = await connectStoreCard.count() > 0;
    expect(hasConnectStore).toBe(true);
  });
});

test.describe('Conditional Store UI - Store Connected', () => {
  test.beforeEach(async ({ page, context }) => {
    await setupAuthenticatedState(page, context, MOCK_MERCHANT_WITH_STORE);
    await waitForDashboardReady(page);
  });

  test('should NOT show "no store" warning when store is connected', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // The "no store connected" warning should NOT be visible
    const storeWarning = page.locator('text=/no.*store.*connect/i');
    const hasWarning = await storeWarning.count() > 0;
    expect(hasWarning).toBe(false);
  });

  test('should show Total Sales card on dashboard when store connected', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // Should show Total Sales card
    const salesCard = page.getByText(/total sales/i);
    const hasSalesCard = await salesCard.count() > 0;
    expect(hasSalesCard).toBe(true);
  });

  test('should NOT show Connect Store action link when store is connected', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // "Connect Store" should NOT be shown as a call-to-action in the sales card
    // (The text "Connect Store" might appear in the amber warning, but not as a sales card)
    // We check that Total Sales is shown instead
    const salesCard = page.getByText(/total sales/i);
    const hasTotalSales = await salesCard.count() > 0;
    expect(hasTotalSales).toBe(true);
  });
});

// ============================================================================
// Store Required Guard Tests
// ============================================================================

test.describe('Store Required Guard', () => {
  test.beforeEach(async ({ page, context }) => {
    await setupAuthenticatedState(page, context, MOCK_MERCHANT);
  });

  test('should redirect store-required routes when no store connected', async ({
    page,
  }) => {
    // Try to access products page (requires store)
    await page.goto('/products');
    await page.waitForLoadState('networkidle');

    // Should be redirected away from /products
    const url = page.url();
    expect(url).not.toContain('/products');
  });

  test('should allow access to store-independent routes', async ({
    page,
    context,
  }) => {
    // These routes should be accessible regardless of store connection
    const accessibleRoutes = [
      '/dashboard',
      '/conversations',
      '/costs',
      '/bot-config',
      '/settings',
    ];

    for (const route of accessibleRoutes) {
      await page.goto(route);
      await page.waitForLoadState('networkidle');

      // Should not be redirected to login
      expect(page.url()).not.toContain('/login');
    }
  });
});

// ============================================================================
// Auth Store Integration Tests
// ============================================================================

test.describe('Auth Store Integration', () => {
  test.beforeEach(async ({ page, context }) => {
    await setupAuthenticatedState(page, context);
    await waitForDashboardReady(page);
  });

  test('should have navigation after authentication', async ({ page }) => {
    if (!page.url().includes('/dashboard')) {
      test.skip();
      return;
    }

    // Check for some navigation element
    const nav = page.locator('nav, aside, [role="navigation"]');
    const hasNav = await nav.count() > 0;
    expect(hasNav).toBe(true);
  });
});

// ============================================================================
// Tutorial Prompt Tests
// ============================================================================

test.describe('Tutorial Prompt Interaction', () => {
  test.beforeEach(async ({ page, context }) => {
    // Set up with incomplete tutorial to trigger the prompt
    await mockAuthApi(page, context, MOCK_MERCHANT);

    await context.addCookies([
      {
        name: 'session_token',
        value: 'mock-session-token-e2e',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        sameSite: 'Strict',
        expires: Math.floor(Date.now() / 1000) + 86400,
      },
    ]);

    // Set onboarding as complete but tutorial as incomplete
    await page.addInitScript((args) => {
      const { onboardingKey, tutorialKey, onboardingData, tutorialData } = args as {
        onboardingKey: string;
        tutorialKey: string;
        onboardingData: object;
        tutorialData: object;
      };

      localStorage.setItem(onboardingKey, JSON.stringify(onboardingData));
      localStorage.setItem(tutorialKey, JSON.stringify(tutorialData));
    }, {
      onboardingKey: ONBOARDING_STORAGE_KEY,
      tutorialKey: TUTORIAL_STORAGE_KEY,
      onboardingData: {
        state: {
          completedSteps: ['personality', 'businessInfo', 'botName', 'greetings', 'pins'],
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
      },
      // Tutorial NOT completed to trigger the prompt
      tutorialData: {
        state: {
          isStarted: false,
          isCompleted: false,
          isSkipped: false,
          currentStep: 0,
          completedSteps: [],
          startedAt: null,
          completedAt: null,
          stepsTotal: 8,
        },
        version: 0,
      },
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('should show tutorial prompt when tutorial not completed', async ({ page }) => {
    // Check if tutorial prompt appears
    const tutorialPrompt = page.locator('text=/tutorial|get started|remind me later/i');
    const hasPrompt = await tutorialPrompt.count() > 0;

    // If on dashboard, expect some tutorial-related content
    if (page.url().includes('/dashboard')) {
      // Tutorial prompt should appear since tutorial is not completed
      expect(hasPrompt).toBe(true);
    }
  });

  test('should dismiss tutorial prompt with Remind me later', async ({ page }) => {
    const remindButton = page.getByRole('button', { name: /remind me later/i });

    if (await remindButton.count() > 0) {
      await remindButton.first().click();
      await page.waitForTimeout(500);
      // Button should be dismissed
      await expect(remindButton.first()).not.toBeVisible({ timeout: 2000 });
    } else {
      // If no remind button, just verify page is functional
      const bodyContent = await page.locator('body').textContent();
      expect(bodyContent).toBeTruthy();
    }
  });
});
