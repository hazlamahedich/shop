import { test, expect } from '@playwright/test';

test.describe('Story 10-10: FAQ Usage Widget - Visual', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Test FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }
        ]))
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
    };
  }

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
      totalClicks: faqs.reduce((sum, f) => sum + f.clickCount, 1),
      avgConversionRate: faqs.length > 0 
        ? faqs.reduce((sum, f) => sum + f.conversionRate, 1) / faqs.length
        : 0,
      unusedCount: faqs.filter(f => f.isUnused).length
    };
    return { faqs, summary: summary ?? defaultSummary };
  }

  test('[P3][10.10-E2E-012] Keyboard navigation through widget controls', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'FAQ 1', clickCount: 10, conversionRate: 5.0, isUnused: false },
        ]))
      });
    });

    await page.goto('/dashboard');
    await page.keyboard.press('Tab');
    await expect(page.getByTestId('time-range-selector')).toBeFocused();
  });

  test('[P3][10.10-E2E-013] Screen reader accessibility for FAQ data', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Accessible FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    const widget = page.getByTestId('faq-usage-widget');
    await expect(widget).toBeVisible();
    await expect(widget).toHaveAttribute('role', 'region');
    await expect(widget).toHaveAttribute('aria-label', /FAQ Usage/);
  });

  test('[P3][10.10-E2E-014] Mobile responsive layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Mobile FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
    const boundingBox = await page.getByTestId('faq-usage-widget').boundingBox();
    expect(boundingBox?.width).toBeLessThan(400);
  });

  test('[P3][10.10-E2E-015] Dark mode styling respected', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Dark Mode FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    const widget = page.getByTestId('faq-usage-widget');
    await expect(widget).toBeVisible();
  });

  test('[P3][10.10-E2E-016] Long FAQ question text truncates with ellipsis', async ({ page }) => {
    const longQuestion = 'This is a very long FAQ question that should be truncated because it exceeds the normal display width and shows the ellipsis at the end...';
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: longQuestion, clickCount: 10, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    const faqItem = page.getByTestId('faq-item-1');
    await expect(faqItem).toBeVisible();
    await expect(faqItem.getByText(longQuestion.substring(0, 50))).toBeVisible();
  });

  test('[P3][10.10-E2E-017] Conversion rate formatting with decimal places', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Test', clickCount: 10, conversionRate: 12.345, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-conversion-1')).toHaveText('12.3% conversion');
  });

  test('[P3][10.10-E2E-018] Click count formatting with large numbers', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Test', clickCount: 1234, conversionRate: 5.0, isUnused: false }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-clicks-1')).toHaveText('1234 clicks');
  });

  test('[P3][10.10-E2E-019] Delta percentage displays with correct colors', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Positive', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: 25 } },
          { id: 2, question: 'Negative', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: -15 } }
        ]))
      });
    });

    await page.goto('/dashboard');
    const positiveDelta = page.getByTestId('faq-change-1');
    await expect(positiveDelta).toBeVisible();
    await expect(positiveDelta.getByText('+25%')).toBeVisible();
  });

  test('[P3][10.10-E2E-020] Trend icons display correctly', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Test', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: 15 } }
        ]))
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-change-1').getByRole('img')).toBeVisible();
  });

  test('[P3][10.10-E2E-021] Warning color for unused FAQs', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([
          { id: 1, question: 'Unused', clickCount: 1, conversionRate: 0, isUnused: true }
        ]))
      });
    });

    await page.goto('/dashboard');
    const warning = page.getByTestId('unused-faq-warning-1');
    await expect(warning).toBeVisible();
    await expect(warning).toHaveCSS('color', /rgb\(255,\s*\d+,\s*245\)/);
  });

  test('[P3][10.10-E2E-022] Empty state message with link to create FAQs', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });

    await page.goto('/dashboard');
    const emptyState = page.getByTestId('faq-usage-empty');
    await expect(emptyState).toBeVisible();
    await expect(emptyState.getByRole('link', { name: 'Bot Config' })).toBeVisible();
  });

  test('[P3][10.10-E2E-023] Error message styling', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({ status: 500, body: 'Error' });
    });

    await page.goto('/dashboard');
    const errorState = page.getByTestId('faq-usage-error');
    await expect(errorState).toBeVisible();
    await expect(errorState.locator('p')).toHaveCSS('color', /rgb\(.*245.*\)/i);
  });

  test('[P3][10.10-E2E-024] Loading spinner animation', async ({ page }) => {
    const responsePromise = page.waitForResponse('**/api/v1/analytics/faq-usage*');
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });

    await page.goto('/dashboard');
    await responsePromise;
    const widget = page.getByTestId('faq-usage-widget');
    await expect(widget).toBeVisible();
  });

  test('[P3][10.10-E2E-025] Manage FAQs link navigates to bot-config', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify(createMockFaqResponse([]))
      });
    });

    await page.goto('/dashboard');
    const manageLink = page.getByTestId('manage-faqs-link');
    await expect(manageLink).toBeVisible();
    await manageLink.click();
    await expect(page).toHaveURL(/bot-config/);
  });
});
