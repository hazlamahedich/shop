import { test, expect } from '@playwright/test';

test.describe('Story 10-10: FAQ Usage Widget - States', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });
    await page.goto('/dashboard');
  });

  test.afterEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  interface MockFaq {
  id: number;
  question: string;
  clickCount: number;
  conversionRate: number;
  isUnused: boolean;
  change?: { clickChange: number };
}

function createMockFaqResponse(faqs: MockFaq[] = [], summary = null): { faqs: MockFaq[]; summary: { totalClicks: number; avgConversionRate: number; unusedCount: number } } {
  const defaultSummary = {
    totalClicks: faqs.reduce((sum, f) => sum + f.clickCount, 0),
    avgConversionRate: faqs.length > 0 
      ? faqs.reduce((sum, f) => sum + f.conversionRate, 0) / faqs.length
        : 0,
    unusedCount: faqs.filter(f => f.isUnused).length,
  };
  return { faqs, summary: summary ?? defaultSummary };
}

  test('[P2][10.10-E2E-007] Empty state shows helpful message', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-empty')).toBeVisible();
    await expect(page.getByText('No FAQ data available yet')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Bot Config' })).toBeVisible();
  });

  test('[P2][10.10-E2E-008] Unused FAQ warning indicator displays', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Unused FAQ', clickCount: 0, conversionRate: 0, isUnused: true }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('unused-faq-warning-1')).toBeVisible();
    await expect(page.getByText('No clicks in 30 days')).toBeVisible();
  });

  test('[P2][10.10-E2E-009] Error state displays on network failure', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({ status: 500, body: 'Internal Server Error' });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-error')).toBeVisible();
    await expect(page.getByText('SIGNAL_DECODE_ERROR')).toBeVisible();
  });

  test('[P2][10.10-E2E-010] Refresh button triggers data refetch', async ({ page }) => {
    let callCount = 0;
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      callCount++;
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: callCount, question: `FAQ ${callCount}`, clickCount: callCount * 10, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByText('FAQ 1')).toBeVisible();
    await page.getByTestId('refresh-button').click();
    await expect(page.getByText('FAQ 2')).toBeVisible();
  });
});
