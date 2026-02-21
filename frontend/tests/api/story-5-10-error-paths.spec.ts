/**
 * Error Path Tests for Story 5-10: Widget Full App Integration
 *
 * Tests error handling, timeouts, rate limiting, and malformed responses.
 *
 * @tags api widget story-5-10 error-handling resilience
 */

import { test, expect, Page } from '@playwright/test';

const mockWidgetConfig = {
  config: {
    enabled: true,
    botName: 'Shopping Assistant',
    welcomeMessage: 'Hello!',
    theme: {
      primaryColor: '#6366f1',
      backgroundColor: '#ffffff',
      textColor: '#1f2937',
      botBubbleColor: '#f3f4f6',
      userBubbleColor: '#6366f1',
      position: 'bottom-right',
      borderRadius: 16,
      width: 380,
      height: 600,
      fontFamily: 'Inter, sans-serif',
      fontSize: 14,
    },
  },
};

const TEST_MERCHANT_ID = 1;

test.describe('Story 5-10: Error Path Handling [P1]', () => {
  test.slow();

  test.beforeEach(async ({ page }) => {
    await page.route('**/*.myshopify.com/**', (route) => route.abort());
  });

  test('[P1] should handle checkout 500 error gracefully', async ({ page, context }) => {
    await context.route('**/api/v1/widget/checkout', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 15000,
          message: 'Internal Server Error',
        }),
      })
    );

    await context.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockWidgetConfig),
      });
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ session: { session_id: 'test-session-500' } }),
        });
      } else {
        await route.continue();
      }
    });

    await context.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error_code: 15000, message: 'Internal Server Error' }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('checkout');
    await input.press('Enter');

    await expect(page.locator('.error-toast').first()).toBeVisible({ timeout: 10000 });
  });

  test('[P1] should handle malformed JSON response gracefully', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: 'not valid json{broken',
      })
    );

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 10000,
    });
  });

  test.skip('[P1] should handle network timeout gracefully', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 35000));
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ config: { enabled: true } }),
      });
    });

    await page.goto('/widget-test');

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 40000,
    });
  });

  test('[P1] should handle 429 rate limit response', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', (route) =>
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 14029,
          message: 'Rate limit exceeded',
          retry_after: 60,
        }),
      })
    );

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 10000,
    });
  });

  test('[P1] should handle 401 unauthorized response', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', (route) =>
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 14001,
          message: 'Unauthorized',
        }),
      })
    );

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 10000,
    });
  });

  test('[P1] should handle 404 not found response', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', (route) =>
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 14004,
          message: 'Widget configuration not found',
        }),
      })
    );

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 10000,
    });
  });

  test('[P1] should handle empty cart on checkout', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(mockWidgetConfig) });
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ session: { session_id: 'test-session-empty' } }),
        });
      } else {
        await route.continue();
      }
    });

    await context.route('**/api/v1/widget/checkout', (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 12020,
          message: 'Cart is empty',
        }),
      })
    );

    await context.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: 'msg-empty',
            content: "Your cart is empty. Would you like to browse our products?",
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
    await input.fill('checkout');
    await input.press('Enter');

    await expect(page.locator('.error-toast, .chat-error').first()).toBeVisible({ timeout: 10000 });
  });

  test('[P1] should handle Shopify unavailable error', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(mockWidgetConfig) });
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ session: { session_id: 'test-session-no-shopify' } }),
        });
      } else {
        await route.continue();
      }
    });

    await context.route('**/api/v1/widget/checkout', (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 8010,
          message: 'No Shopify store connected',
        }),
      })
    );

    await context.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: {
            message_id: 'msg-no-shopify',
            content: 'Checkout unavailable. Please visit our store directly.',
            sender: 'bot',
            created_at: new Date().toISOString(),
            fallback_url: 'https://test-store.myshopify.com/cart',
          },
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('checkout');
    await input.press('Enter');

    await expect(page.locator('.error-toast, .chat-error').first()).toBeVisible({ timeout: 10000 });
  });

  test('[P1] should handle search API failure gracefully', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(mockWidgetConfig) });
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({ session: { session_id: 'test-session-search' } }),
        });
      } else {
        await route.continue();
      }
    });

    await context.route('**/api/v1/widget/search', (route) =>
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 15000,
          message: 'Search temporarily unavailable',
        }),
      })
    );

    await context.route('**/api/v1/widget/message', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({
          error_code: 15000,
          message: 'Search temporarily unavailable',
        }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('search for shoes');
    await input.press('Enter');

    await expect(page.locator('.error-toast').first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Story 5-10: Widget Resilience [P2]', () => {
  test.slow();

  test.beforeEach(async ({ page }) => {
    await page.route('**/*.myshopify.com/**', (route) => route.abort());
  });

  test('[P2] widget should remain functional after API error', async ({ page, context }) => {
    let requestCount = 0;

    await context.route('**/api/v1/widget/config/*', async (route) => {
      requestCount++;
      if (requestCount === 1) {
        await route.fulfill({
          status: 500,
          body: JSON.stringify({ error_code: 15000, message: 'Server Error' }),
        });
      } else {
        await route.fulfill({
          status: 200,
          body: JSON.stringify(mockWidgetConfig),
        });
      }
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ session: { session_id: 'test-session-resilience' } }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.locator('.error-toast, .widget-error-boundary').first()).toBeVisible({
      timeout: 10000,
    });

    await page.reload();

    await expect(bubble).toBeVisible({ timeout: 10000 });
    await bubble.click();

    await expect(page.getByPlaceholder('Type a message...')).toBeVisible({ timeout: 5000 });
  });

  test('[P2] widget should handle concurrent errors gracefully', async ({ page, context }) => {
    await context.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockWidgetConfig),
      });
    });

    await context.route('**/api/v1/widget/session', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ session: { session_id: 'test-session-concurrent' } }),
      });
    });

    await context.route('**/api/v1/widget/**', async (route) => {
      await route.fulfill({
        status: 500,
        body: JSON.stringify({ error_code: 15000, message: 'Server Error' }),
      });
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('test');
    await input.press('Enter');

    await expect(page.locator('.error-toast').first()).toBeVisible({ timeout: 10000 });

    const errorToasts = await page.locator('.error-toast').count();
    expect(errorToasts).toBeGreaterThanOrEqual(1);
    expect(errorToasts).toBeLessThanOrEqual(5);
  });
});
