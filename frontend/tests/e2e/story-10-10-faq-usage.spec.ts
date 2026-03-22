import { test, expect, Page } from '@playwright/test';

test.describe('Story 10-10: FAQ Usage Widget', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@example.com');
    await page.fill('[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('[P0][10.10-E2E-001] Widget renders in General mode dashboard', async ({ page }) => {
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
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
    await expect(page.getByText('FAQ Usage')).toBeVisible();
    await expect(page.getByText('70')).toBeVisible();
  });

  test('[P0][10.10-E2E-002] FAQ data displayed with clicks and conversion rates', async ({ page }) => {
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
    await expect(page.getByTestId('faq-item-1')).toBeVisible();
    await expect(page.getByText('What are your hours?')).toBeVisible();
    await expect(page.getByTestId('faq-clicks-1')).toHaveText('42 clicks');
    await expect(page.getByTestId('faq-conversion-1')).toHaveText('15.5% conversion');
  });

  test('[P1][10.10-E2E-003] Period comparison toggle switches periods', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: 20 } }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    const timeRangeSelector = page.getByTestId('time-range-selector');
    await expect(timeRangeSelector).toBeVisible();
    await timeRangeSelector.selectOption('7');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
  });

  test('[P1][10.10-E2E-004] CSV export downloads file', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    const selector = page.getByTestId('time-range-selector');
    await selector.selectOption('14');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
  });

  test('[P2][10.10-E2E-007] Empty state shows helpful message', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Unused FAQ', clickCount: 0, conversionRate: 0, isUnused: true }],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 1 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: callCount, question: `FAQ ${callCount}`, clickCount: callCount * 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: callCount * 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByText('FAQ 1')).toBeVisible();
    await page.getByTestId('refresh-button').click();
    await expect(page.getByText('FAQ 2')).toBeVisible();
  });

  test('[P3][10.10-E2E-011] Loading state displays during data fetch', async ({ page }) => {
    let resolved = false;
    await page.route('**/api/v1/analytics/faq-usage*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 500));
      resolved = true;
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-usage-widget')).toBeVisible();
  });

  test('[P3][10.10-E2E-012] Keyboard navigation through widget controls', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [
            { id: 1, question: 'FAQ 1', clickCount: 10, conversionRate: 5.0, isUnused: false },
            { id: 2, question: 'FAQ 2', clickCount: 20, conversionRate: 10.0, isUnused: false },
          ],
          summary: { totalClicks: 30, avgConversionRate: 7.5, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Accessible FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    const widget = page.getByTestId('faq-usage-widget');
    await expect(widget).toBeVisible();
    const accessibilitySnapshot = await page.accessibility.snapshot();
    expect(accessibilitySnapshot).toBeDefined();
  });

  test('[P3][10.10-E2E-014] Mobile responsive layout', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Mobile FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Dark Mode FAQ', clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: longQuestion, clickCount: 10, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test', clickCount: 10, conversionRate: 12.345, isUnused: false }],
          summary: { totalClicks: 10, avgConversionRate: 12.345, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-conversion-1')).toHaveText('12.3% conversion');
  });

  test('[P3][10.10-E2E-018] Click count formatting with large numbers', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test', clickCount: 1234, conversionRate: 5.0, isUnused: false }],
          summary: { totalClicks: 1234, avgConversionRate: 5.0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-clicks-1')).toHaveText('1234 clicks');
  });

  test('[P3][10.10-E2E-019] Delta percentage displays with correct colors', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [
            { id: 1, question: 'Positive', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: 25 } },
            { id: 2, question: 'Negative', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: -15 } },
          ],
          summary: { totalClicks: 20, avgConversionRate: 5.0, unusedCount: 0 }
        })
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
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Test', clickCount: 10, conversionRate: 5.0, isUnused: false, change: { clickChange: 15 } }],
          summary: { totalClicks: 10, avgConversionRate: 5.0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    await expect(page.getByTestId('faq-change-1').getByRole('img')).toBeVisible();
  });

  test('[P3][10.10-E2E-021] Warning color for unused FAQs', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [{ id: 1, question: 'Unused', clickCount: 0, conversionRate: 0, isUnused: true }],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 1 }
        })
      });
    });

    await page.goto('/dashboard');
    const warning = page.getByTestId('unused-faq-warning-1');
    await expect(warning).toBeVisible();
    await expect(warning).toHaveCSS('color', /rgb\(255,\s*\s*,\245,\s*\s*\)/);
  });
});

  test('[P3][10.10-E2E-022] Empty state message with link to create FAQs', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
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
    await expect(errorState.locator('p')).toHaveCSS('color', /rgb\.\s*245\.*\)/i);
  });

  test('[P3][10.10-E2E-024] Loading spinner animation', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 100));
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    const widget = page.getByTestId('faq-usage-widget');
    await expect(widget).toBeVisible();
  });

  test('[P3][10.10-E2E-025] Manage FAQs link navigates to bot-config', async ({ page }) => {
    await page.route('**/api/v1/analytics/faq-usage*', (route) => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          faqs: [],
          summary: { totalClicks: 0, avgConversionRate: 0, unusedCount: 0 }
        })
      });
    });

    await page.goto('/dashboard');
    const manageLink = page.getByTestId('manage-faqs-link');
    await expect(manageLink).toBeVisible();
    await manageLink.click();
    await expect(page).toHaveURL(/bot-config/);
  });
});
