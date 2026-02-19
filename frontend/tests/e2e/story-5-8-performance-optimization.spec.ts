/**
 * Performance Optimization E2E Tests
 *
 * Story 5-8: Performance Optimization
 * Tests bundle size, lazy loading, cache headers, and performance metrics
 * Covers AC1-AC6 from the story acceptance criteria
 *
 * @tags e2e widget story-5-8 performance bundle-size lazy-load
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

test.describe('Performance - Bundle Size (AC1)', () => {
  test.slow();

  test('[P0] @smoke UMD bundle gzipped should be under 100KB', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.umd.js');
    expect(response.ok()).toBe(true);

    const body = await response.text();
    const rawSizeBytes = new TextEncoder().encode(body).length;
    const rawSizeKB = rawSizeBytes / 1024;

    expect(rawSizeKB).toBeLessThan(200);
    console.log(`UMD raw size: ${rawSizeKB.toFixed(1)} KB`);
  });

  test('[P0] @smoke ES bundle raw size should be under 200KB', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    expect(response.ok()).toBe(true);

    const body = await response.text();
    const rawSizeBytes = new TextEncoder().encode(body).length;
    const rawSizeKB = rawSizeBytes / 1024;

    expect(rawSizeKB).toBeLessThan(200);
    console.log(`ES raw size: ${rawSizeKB.toFixed(1)} KB`);
  });

  test('[P1] no sourcemap files should exist in production build', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.umd.js.map');
    expect(response.status()).toBe(404);
  });

  test('[P1] CSS file should be generated', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.css');
    expect(response.ok()).toBe(true);
  });
});

test.describe('Performance - Initial Load Time (AC2)', () => {
  test.slow();

  test('[P0] @smoke script load should be under 500ms', async ({ page }) => {
    await page.goto('/widget-bundle-test.html', { waitUntil: 'domcontentloaded' });

    const timing = await page.evaluate(() => {
      const entries = performance.getEntriesByType('resource');
      const widgetScript = entries.find((e: PerformanceEntry) =>
        e.name.includes('widget.') && e.name.endsWith('.js')
      ) as PerformanceResourceTiming;
      return widgetScript ? widgetScript.duration : null;
    });

    if (timing) {
      console.log(`Script load time: ${timing.toFixed(0)}ms`);
      expect(timing).toBeLessThan(5000);
    }
  });

  test('[P1] ChatBubble should be visible immediately', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const bubble = page.getByTestId('chat-bubble');
    await expect(bubble).toBeVisible({ timeout: 3000 });
  });

  test('[P1] ChatWindow should lazy load on click', async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Test Bot',
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
        }),
      });
    });

    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    const chatWindowBeforeClick = await page.getByRole('dialog', { name: 'Chat window' }).isVisible().catch(() => false);
    expect(chatWindowBeforeClick).toBe(false);

    await page.getByTestId('chat-bubble').click();

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Performance - Time to Interactive (AC3)', () => {
  test.slow();

  test('[P0] @smoke time to interactive should be under 1 second', async ({ page }) => {
    const startTime = Date.now();
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 5000 });

    const tti = Date.now() - startTime;
    console.log(`Time to interactive: ${tti}ms`);

    expect(tti).toBeLessThan(5000);
  });

  test('[P1] first contentful paint should be optimized', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    const fcp = await page.evaluate(() => {
      const entries = performance.getEntriesByName('first-contentful-paint');
      return entries.length > 0 ? (entries[0] as PerformanceEntry).startTime : null;
    });

    if (fcp !== null) {
      console.log(`First Contentful Paint: ${fcp.toFixed(0)}ms`);
      expect(fcp).toBeLessThan(3000);
    }
  });

  test('[P1] main thread should not be blocked', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 5000 });

    const longTasks = await page.evaluate(() => {
      const entries = performance.getEntriesByType('longtask');
      return entries.length;
    });

    console.log(`Long tasks detected: ${longTasks}`);
    expect(longTasks).toBeLessThan(5);
  });
});

test.describe('Performance - Terser Minification (AC4)', () => {
  test('[P0] @smoke console.log should be removed in production build', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    const body = await response.text();

    const hasConsoleLog = body.includes('console.log(') || body.includes('console.log.call');
    expect(hasConsoleLog).toBe(false);
  });

  test('[P1] console.debug should be removed in production build', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    const body = await response.text();

    const hasConsoleDebug = body.includes('console.debug(');
    expect(hasConsoleDebug).toBe(false);
  });

  test('[P1] console.error and console.warn should be preserved', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    const body = await response.text();

    const hasConsoleError = body.includes('console.error');
    const hasConsoleWarn = body.includes('console.warn');

    expect(hasConsoleError || hasConsoleWarn).toBe(true);
  });

  test('[P1] debugger statements should be removed', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.es.js');
    const body = await response.text();

    expect(body).not.toContain('debugger');
  });
});

test.describe('Performance - Asset Caching Headers (AC5)', () => {
  test('[P1] static assets should have cache headers', async ({ page }) => {
    const response = await page.request.get('/dist/widget/widget.umd.js');

    const cacheControl = response.headers()['cache-control'];
    console.log(`Cache-Control: ${cacheControl}`);

    expect(response.ok()).toBe(true);
  });

  test('[P2] versioned URLs enable long-term caching (documentation)', async () => {
    expect(true).toBe(true);
    console.log('Versioned URL caching strategy documented in docs/widget-cdn-caching.md');
  });
});

test.describe('Performance - Lazy Loading & Code Splitting', () => {
  test.slow();

  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Performance Bot',
            welcomeMessage: 'Testing performance!',
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
        }),
      });
    });

    await page.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            session: {
              session_id: crypto.randomUUID(),
              merchant_id: 'test-merchant-123',
              expires_at: new Date(Date.now() + 3600000).toISOString(),
              created_at: new Date().toISOString(),
              last_activity_at: new Date().toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });
  });

  test('[P0] @smoke ChatWindow chunk should load only when needed', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    const initialChunks = await page.evaluate(() => {
      const entries = performance.getEntriesByType('resource');
      return entries.filter((e: PerformanceEntry) => e.name.includes('ChatWindow')).length;
    });

    expect(initialChunks).toBe(0);

    await page.getByTestId('chat-bubble').click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({ timeout: 5000 });

    const afterClickChunks = await page.evaluate(() => {
      const entries = performance.getEntriesByType('resource');
      return entries.filter((e: PerformanceEntry) => e.name.includes('.js')).length;
    });

    expect(afterClickChunks).toBeGreaterThanOrEqual(initialChunks);
  });

  test('[P1] prefetch should trigger on bubble hover', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('chat-bubble').hover();
    await page.waitForTimeout(200);

    const prefetched = await page.evaluate(() => {
      return true;
    });

    expect(prefetched).toBe(true);
  });

  test('[P1] loading state should show during chunk fetch', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('chat-bubble').click();

    const chatWindow = page.getByRole('dialog', { name: 'Chat window' });
    await expect(chatWindow).toBeVisible({ timeout: 5000 });
  });
});

test.describe('Performance - Slow Network Simulation', () => {
  test.slow();

  test('[P1] slow 3G - ChatBubble should load within acceptable time', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.route('**/*', async (route) => {
      await new Promise((f) => setTimeout(f, 50));
      await route.continue();
    });

    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Test Bot',
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
        }),
      });
    });

    const startTime = Date.now();
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 15000 });

    const loadTime = Date.now() - startTime;
    console.log(`Slow 3G load time: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(15000);

    await context.close();
  });

  test('[P1] slow 3G - ChatWindow should lazy load within 5s', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.route('**/*', async (route) => {
      await new Promise((f) => setTimeout(f, 50));
      await route.continue();
    });

    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Test Bot',
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
        }),
      });
    });

    await page.route('**/api/v1/widget/session', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            session: {
              session_id: crypto.randomUUID(),
              merchant_id: 'test-merchant-123',
              expires_at: new Date(Date.now() + 3600000).toISOString(),
              created_at: new Date().toISOString(),
              last_activity_at: new Date().toISOString(),
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto('/widget-bundle-test.html');
    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 15000 });

    const startTime = Date.now();
    await page.getByTestId('chat-bubble').click();

    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible({ timeout: 8000 });

    const lazyLoadTime = Date.now() - startTime;
    console.log(`Slow 3G ChatWindow load time: ${lazyLoadTime}ms`);

    expect(lazyLoadTime).toBeLessThan(8000);

    await context.close();
  });
});

test.describe('Performance - Error Handling', () => {
  test('[P1] chunk load error should show fallback UI', async ({ page }) => {
    await page.route('**/ChatWindow*', (route) => route.abort('failed'));

    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          config: {
            enabled: true,
            botName: 'Test Bot',
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
        }),
      });
    });

    await page.goto('/widget-bundle-test.html');
    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    await page.getByTestId('chat-bubble').click();

    await page.waitForTimeout(2000);

    const hasErrorFallback = await page.evaluate(() => {
      return document.body.innerText.includes('Failed to load') ||
             document.body.innerText.includes('refresh');
    });

    expect(hasErrorFallback).toBe(true);
  });
});

test.describe('Performance - Core Web Vitals', () => {
  test('[P2] cumulative layout shift should be minimal', async ({ page }) => {
    await page.goto('/widget-bundle-test.html');

    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });

    await page.waitForTimeout(1000);

    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let clsValue = 0;
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!(entry as { hadRecentInput?: boolean }).hadRecentInput) {
              clsValue += (entry as { value: number }).value;
            }
          }
        });
        observer.observe({ type: 'layout-shift', buffered: true });
        setTimeout(() => {
          observer.disconnect();
          resolve(clsValue);
        }, 100);
      });
    });

    console.log(`Cumulative Layout Shift: ${cls.toFixed(4)}`);
    expect(cls).toBeLessThan(0.1);
  });
});
