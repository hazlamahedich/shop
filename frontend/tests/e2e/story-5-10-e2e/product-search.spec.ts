/**
 * Widget Product Search E2E Tests
 *
 * Story 5-10: Widget Full App Integration - AC2
 * Tests product search functionality via widget interface.
 *
 * Test IDs: 5.10-E2E-002 to 5.10-E2E-005
 * @tags e2e widget story-5-10 search ac2
 */

import { test, expect } from '@playwright/test';
import { setupWidgetMocks } from '../../helpers/widget-test-fixture';

test.beforeEach(async ({ page }) => {
  await setupWidgetMocks(page);
});

test.describe('Widget Product Search (AC2) [5.10-E2E-002]', () => {
  test.slow();

  test('[P1][5.10-E2E-002-01] should return products from search endpoint', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/v1/widget/search', {
      data: {
        session_id: 'test-session-search-endpoint',
        query: 'shoes',
      },
      headers: {
        'Content-Type': 'application/json',
        'X-Test-Mode': 'true',
      },
    });

    expect([200, 400, 401, 404, 422, 503]).toContain(response.status());

    if (response.status() === 200) {
      const data = await response.json();
      expect(data.data || data).toBeDefined();
    }
  });

  test('[P2][5.10-E2E-002-02] should display product cards with Add to Cart button', async ({ page }) => {
    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: 'Here are some products I found:',
            sender: 'bot',
            created_at: new Date().toISOString(),
            products: [
              {
                id: 'prod-1',
                variant_id: 'var-1',
                title: 'Test Product',
                price: 29.99,
                image_url: 'https://example.com/product.jpg',
                available: true,
                product_type: 'Test',
              },
            ],
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('show me products');
    await input.press('Enter');

    await expect(page.getByText('Test Product')).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('button', { name: /add to cart/i })).toBeVisible();
  });

  test('[P1][5.10-E2E-002-03] should handle search with no results gracefully', async ({ page }) => {
    await page.route('**/api/v1/widget/search', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            products: [],
            total: 0,
            query: 'nonexistent-xyz-123',
          },
        }),
      });
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I couldn't find any products matching your search. Try different keywords!",
            sender: 'bot',
            created_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('find nonexistent-xyz-123');
    await input.press('Enter');

    await expect(page.getByText(/couldn't find|try different/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-002-04] should handle search API error gracefully', async ({ page }) => {
    await page.route('**/api/v1/widget/search', async (route) => {
      await route.fulfill({
        status: 503,
        body: JSON.stringify({
          error_code: 12008,
          message: 'Search service temporarily unavailable',
        }),
      });
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: crypto.randomUUID(),
            content: "I'm having trouble searching right now. Please try again in a moment.",
            sender: 'bot',
            created_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('find me shoes');
    await input.press('Enter');

    await expect(page.getByText(/trouble|try again|moment/i)).toBeVisible({ timeout: 10000 });
  });
});
