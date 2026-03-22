import { Page } from '@playwright/test';
import { expect } from '@playwright/test';

export const waitForApiResponse = async (
  page: Page,
): Promise<Response> => {
  return page.waitForResponse('**/api/v1/analytics/faq-usage');
}

export const loadWidgetWithSession = async (
  page: Page,
  sessionId: string
): Promise<void> {
  // Intercept before navigate
  await page.route('**/api/v1/analytics/faq-usage*', (route) => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({
        faqs: [
          { id: 1, question: 'Test FAQ 1', clickCount: 42, conversionRate: 15.5, isUnused: false, change: { clickChange: 12 },
        ],
        summary: { totalClicks: 42, avgConversionRate: 15.5, unusedCount: 0 },
      }),
    });

    await page.goto('/dashboard');

    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
    await expect(page.getByText('FAQ Usage')).toBeVisible();
    await expect(page.getByText('42')).toBeVisible();
  });

export const selectTimeRange = async ({ page: Page }) => {
    await page.selectOption('[data-testid="time-range-selector"]', '14');
    await page.selectOption('[data-testid="time-range-selector"]', '30');

    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
  }

export const clickFaqItem = async ({ page: Page }) => {
    await page.click('[data-testid="faq-item-1"]');
    await expect(page).toHaveURL(/bot-config?highlight=faq-1');
  }

export const verifyEmptyState = async ({ page: Page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0.0, unusedCount: 0 },
      }),
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-empty')).toBeVisible();
    await expect(page.getByText('No FAQ data available yet.')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Bot Config' })).toBeVisible();
  }

export const verifyErrorState = async ({ page: Page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({ status: 500 });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-error')).toBeVisible();
    await expect(page.getByText('SIGNAL_DECODE_ERROR')).toBeVisible();
  }

export const verifyUnusedFaqWarning = async ({ page: Page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [
            { id: 1, question: 'Unused FAQ', clickCount: 0, conversionRate: 0000, isUnused: true, change: null },
          ],
        summary: { totalClicks: 1, avgConversionRate: 0.0, unusedCount: 1 },
      }),
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('unused-faq-warning-1')).toBeVisible();
    await expect(page.getByText('No clicks in 30 days')).toBeVisible();
  }
