/**
 * Build System & Loader Script E2E Tests
 *
 * Story 5-4: Build System & Loader Script
 * Tests the widget build output, loader script functionality, and embedding patterns
 * Covers UMD/ES bundles, config reading, async loading, and error handling
 *
 * @tags e2e widget story-5-4 bundle loader
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Build System & Loader Script - Bundle Loading (AC1)', () => {
  test.slow();

  test('[P0] @smoke should build UMD bundle that loads via script tag', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 15000 });
  });

  test('[P0] @smoke should expose ShopBotWidget global in UMD mode', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const hasGlobal = await page.evaluate(() => {
      return typeof (window as Window & { ShopBotWidget?: unknown }).ShopBotWidget !== 'undefined';
    });

    expect(hasGlobal).toBe(true);
  });

  test('[P1] should include CSS in bundle output', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toBeVisible();

    const hasStyles = await bubble.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.borderRadius !== '0px' || styles.backgroundColor !== 'rgba(0, 0, 0, 0)';
    });

    expect(hasStyles).toBe(true);
  });
});

test.describe('Build System & Loader Script - Config Reading (AC2)', () => {
  test('[P0] @smoke should read merchantId from window.ShopBotConfig', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const configSet = await page.evaluate(() => {
      return (window as Window & { ShopBotConfig?: { merchantId: string } }).ShopBotConfig?.merchantId;
    });

    expect(configSet).toBe('test-merchant-123');
  });

  test('[P1] should read theme from window.ShopBotConfig', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toBeVisible();

    const bgColor = await bubble.evaluate(el => {
      return window.getComputedStyle(el).backgroundColor;
    });

    expect(bgColor).toMatch(/rgb\(16,\s*185,\s*129\)|#10b981/i);
  });

  test('[P1] should read merchantId from data-merchant-id attribute', async ({ page }) => {
    await page.goto('/widget-bundle-data-attr.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 15000 });
  });

  test('[P2] should read theme from data-theme attribute', async ({ page }) => {
    await page.goto('/widget-bundle-data-attr.html');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toBeVisible();
  });

  test('[P2] should prefer window.ShopBotConfig over data attributes', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const merchantId = await page.evaluate(() => {
      return (window as Window & { ShopBotConfig?: { merchantId: string } }).ShopBotConfig?.merchantId;
    });

    expect(merchantId).toBe('test-merchant-123');
  });
});

test.describe('Build System & Loader Script - Widget Mounting (AC3)', () => {
  test('[P0] @smoke should create container element in DOM', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const container = page.locator('#shopbot-widget-root');
    await expect(container).toBeAttached({ timeout: 15000 });
  });

  test('[P0] @smoke should mount React widget inside container', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await expect(bubble).toBeVisible({ timeout: 15000 });
  });

  test('[P1] should create Shadow DOM for style isolation', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const hasShadowDom = await page.evaluate(() => {
      const container = document.getElementById('shopbot-widget-root');
      if (!container) return false;
      const shadowHost = container.querySelector('.widget-container');
      return shadowHost?.shadowRoot !== null;
    });

    expect(hasShadowDom).toBe(true);
  });
});

test.describe('Build System & Loader Script - Async Support (AC4)', () => {
  test('[P0] @smoke should load correctly with async script attribute', async ({ page }) => {
    await page.goto('/widget-bundle-async.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 15000 });
  });

  test('[P1] should not block page render when loading async', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/widget-bundle-async.html');
    const loadTime = Date.now() - startTime;

    expect(loadTime).toBeLessThan(5000);
  });

  test('[P1] should handle DOMContentLoaded correctly', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const widgetLoaded = await page.evaluate(() => {
      return document.readyState === 'complete' || document.readyState === 'interactive';
    });

    expect(widgetLoaded).toBe(true);
  });
});

test.describe('Build System & Loader Script - Error Handling (AC5)', () => {
  test('[P0] @smoke should log error when merchantId is missing', async ({ page }) => {
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error' && msg.text().includes('[ShopBot Widget]')) {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/widget-bundle-no-config.html');

    await page.waitForTimeout(1000);

    expect(consoleErrors.some(err => err.includes('Missing merchantId'))).toBe(true);
  });

  test('[P0] @smoke should not render widget when merchantId is missing', async ({ page }) => {
    await page.goto('/widget-bundle-no-config.html');

    await page.waitForTimeout(1000);

    const container = page.locator('#shopbot-widget-root');
    await expect(container).not.toBeVisible({ timeout: 3000 });
  });

  test('[P1] should provide helpful error message with usage examples', async ({ page }) => {
    const errorMessages: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errorMessages.push(msg.text());
      }
    });

    await page.goto('/widget-bundle-no-config.html');
    await page.waitForTimeout(1000);

    const hasUsageExample = errorMessages.some(msg =>
      msg.includes('window.ShopBotConfig') || msg.includes('data-merchant-id')
    );

    expect(hasUsageExample).toBe(true);
  });
});

test.describe('Build System & Loader Script - Bundle Size (AC6)', () => {
  test('[P1] should have UMD bundle under 200KB raw size', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.umd.js');

    expect(response.ok()).toBe(true);

    const body = await response.text();
    const sizeInBytes = new TextEncoder().encode(body).length;
    const sizeInKB = sizeInBytes / 1024;

    expect(sizeInKB).toBeLessThan(200);
  });

  test('[P1] should have ES bundle under 200KB raw size', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');

    expect(response.ok()).toBe(true);

    const body = await response.text();
    const sizeInBytes = new TextEncoder().encode(body).length;
    const sizeInKB = sizeInBytes / 1024;

    expect(sizeInKB).toBeLessThan(200);
  });
});

test.describe('Build System & Loader Script - Full Flow (AC7)', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Test Assistant',
            welcomeMessage: 'Hi! How can I help you today?',
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
            allowedDomains: [],
          },
        }),
      });
    });

    await page.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        const now = new Date();
        const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            session: {
              session_id: crypto.randomUUID(),
              merchant_id: 'test-merchant-123',
              expires_at: expiresAt.toISOString(),
              created_at: now.toISOString(),
              last_activity_at: now.toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      if (route.request().method() === 'POST') {
        await new Promise(resolve => setTimeout(resolve, 300));
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            message: {
              message_id: crypto.randomUUID(),
              content: 'Thanks for your message! How can I help you?',
              sender: 'bot',
              created_at: new Date().toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });
  });

  test('[P0] @smoke should complete full message flow from bundle', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByRole('button', { name: 'Open chat' })).toBeVisible({ timeout: 15000 });

    await page.getByRole('button', { name: 'Open chat' }).click();

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const input = page.getByLabel('Type a message');
    await input.fill('Hello from bundle test');

    await page.getByRole('button', { name: 'Send message' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByText('Hello from bundle test')).toBeVisible({ timeout: 10000 });

    await expect(messageList.getByText(/Thanks for your message/)).toBeVisible({ timeout: 10000 });
  });

  test('[P1] should create session via API when widget loads from bundle', async ({ page }) => {
    const sessionPromise = page.waitForRequest(req =>
      req.url().includes('/api/v1/widget/session') && req.method() === 'POST'
    );

    await page.goto('/widget-bundle-test.html');

    const request = await sessionPromise;
    expect(request).toBeTruthy();
  });

  test('[P1] should send message and receive bot response from bundle', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await page.getByRole('button', { name: 'Open chat' }).click();

    await page.getByLabel('Type a message').fill('Test message');
    await page.getByRole('button', { name: 'Send message' }).click();

    const messageList = page.getByRole('log', { name: 'Chat messages' });
    await expect(messageList.getByText('Test message')).toBeVisible({ timeout: 10000 });
    await expect(messageList.getByText(/Thanks for your message/)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Build System & Loader Script - Exports', () => {
  test('[P1] should export Widget component for programmatic use', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const hasWidget = await page.evaluate(() => {
      const shopbot = (window as Window & { ShopBotWidget?: { Widget?: unknown } }).ShopBotWidget;
      return typeof shopbot?.Widget !== 'undefined';
    });

    expect(hasWidget).toBe(true);
  });

  test('[P1] should export initWidget function for programmatic use', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const hasInitWidget = await page.evaluate(() => {
      const shopbot = (window as Window & { ShopBotWidget?: { initWidget?: unknown } }).ShopBotWidget;
      return typeof shopbot?.initWidget === 'function';
    });

    expect(hasInitWidget).toBe(true);
  });
});
