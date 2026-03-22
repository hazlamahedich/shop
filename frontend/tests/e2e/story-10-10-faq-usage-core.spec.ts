import { test, expect } from '@playwright/test';

test.describe('Story 10-10: FAQ Usage Widget - Core', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [
            { id: 1, question: 'What are your hours?', clickCount: 42, conversionRate: 15.5, isUnused: false, change: { clickChange: 12 } },
            { id: 2, question: 'How do I return items?', clickCount: 28, conversionRate: 8.2, isUnused: false, change: { clickChange: -5 } },
          ],
          summary: { totalClicks: 70, avgConversionRate: 11.85, unusedCount: 0 }
        })
      });
    });
    await page.goto('/dashboard');
  });

  test.afterEach(async ({ page }) => {
    await page.context().clearCookies();
  });

  function createMockFaq(overrides = {}) {
    return {
      id: 1,
      question: 'Test FAQ Question',
      clickCount: 10,
      conversionRate: 5.0,
      isUnused: false,
      change: { clickChange: 0 },
      ...overrides
    };
  }

  function createMockFaqResponse(faqs = [createMockFaq()]) {
    return {
      faqs,
      summary: {
        totalClicks: faqs.reduce((sum, f) => sum + f.clickCount, 0),
        avgConversionRate: faqs.length > 0 
          ? faqs.reduce((sum, f) => sum + f.conversionRate, 0) / faqs.length 
          : 0,
        unusedCount: faqs.filter(f => f.isUnused).length
      }
    };
  }

  test('[P0][10.10-E2E-001] Widget renders in General mode dashboard', async ({ page }) => {
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('FAQ Usage')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('70')).toBeVisible({ timeout: 10000 });
  });

  test('[P0][10.10-E2E-002] FAQ data displayed with clicks and conversion rates', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          createMockFaq({ id: 1, question: 'What are your hours?', clickCount: 42, conversionRate: 15.5, change: { clickChange: 12 } }),
          createMockFaq({ id: 2, question: 'How do I return items?', clickCount: 28, conversionRate: 8.2, change: { clickChange: -5 } }),
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-item-1')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('What are your hours?')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('faq-clicks-1')).toHaveText('42 clicks', { timeout: 10000 });
    await expect(page.getByTestId('faq-conversion-1')).toHaveText('15.5% conversion', { timeout: 10000 });
  });

  test('[P1][10.10-E2E-003] Period comparison toggle switches periods', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([createMockFaq({ change: { clickChange: 20 } })]))
      });
    });

    await page.goto('/dashboard');
    const timeRangeSelector = page.getByTestId('time-range-selector');
    await expect(timeRangeSelector).toBeVisible({ timeout: 10000 });
    await timeRangeSelector.selectOption('7');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][10.10-E2E-004] CSV export downloads file', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse())
      });
    });

    await page.route('**/api/v1/analytics/faq-usage/export*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'text/csv',
        body: 'FAQ Question,Clicks,Conversion Rate\nTest FAQ,10,5.0%'
      });
    });

    await page.goto('/dashboard');
    const downloadPromise = page.waitForEvent('download');
    await page.getByTestId('csv-export-button').click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('faq-usage');
  });

  test('[P1][10.10-E2E-005] FAQ click navigates to management page', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse())
      });
    });

    await page.goto('/dashboard');
    await page.getByTestId('faq-item-1').click();
    await expect(page).toHaveURL(/bot-config/);
  });

  test('[P1][10.10-E2E-006] Time range selector changes period', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });

    await page.goto('/dashboard');
    const selector = page.getByTestId('time-range-selector');
    await selector.selectOption('14');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible({ timeout: 10000 });
  });
});
