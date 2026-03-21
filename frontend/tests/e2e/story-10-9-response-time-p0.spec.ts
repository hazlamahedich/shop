/**
 * E2E P0 Tests for Story 10-9: Response Time Distribution Widget
 *
 * Critical path tests verifying widget displays percentile metrics
 * and histogram visualization.
 */
import { test, expect } from '@playwright/test';
import { mockResponseTimeApi } from '../helpers/response-time-fixture';

async function setupDashboardMocks(page: import('@playwright/test').Page) {
  await page.addInitScript(() => {
    const mockAuthState = {
      isAuthenticated: true,
      merchant: {
        id: 1,
        email: 'test@test.com',
        name: 'Test Merchant',
        has_store_connected: true,
        store_provider: 'shopify',
        onboardingMode: 'general',
      },
      sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
      isLoading: false,
      error: null,
    };
    localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
  });

  await page.route('**/api/v1/csrf-token', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ csrf_token: 'test-csrf-token' }),
    });
  });

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          merchant: {
            id: 1,
            email: 'test@test.com',
            name: 'Test Merchant',
            has_store_connected: true,
            store_provider: 'shopify',
            onboardingMode: 'general',
          },
        },
      }),
    });
  });
}

test.describe('[Story 10-9] Response Time Distribution Widget - P0 Tests', () => {
  test('[P0][10.9-E2E-001] widget displays in General mode with correct metrics', async ({ page }) => {
    await setupDashboardMocks(page);
    await mockResponseTimeApi(page, {
      percentiles: { p50: 850, p95: 2100, p99: 4500 },
    });

    await page.goto('/dashboard');

    const widget = page.getByTestId('response-time-widget');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const p95Metric = page.getByTestId('p95-metric');
    await expect(p95Metric).toBeVisible();
  });

  test('[P0][10.9-E2E-002] widget displays histogram visualization', async ({ page }) => {
    await setupDashboardMocks(page);
    await mockResponseTimeApi(page, {
      histogram: [
        { label: '0-1s', count: 150, color: 'green' },
        { label: '1-2s', count: 80, color: 'green' },
        { label: '2-3s', count: 45, color: 'green' },
        { label: '3-5s', count: 20, color: 'yellow' },
        { label: '5s+', count: 5, color: 'red' },
      ],
    });

    await page.goto('/dashboard');

    const widget = page.getByTestId('response-time-widget');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const histogramBars = page.locator('[data-testid^="histogram-bar"]');
    await expect(histogramBars.first()).toBeVisible();
  });
});
