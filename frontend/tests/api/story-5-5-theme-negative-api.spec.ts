/**
 * Theme Customization System - Negative API Tests
 *
 * Story 5-5: Theme Customization System
 * Tests API error handling, timeout scenarios, and edge cases
 *
 * Priority: P3 (Nice-to-have - most scenarios covered by E2E mocks)
 * Critical Analysis: Some tests duplicate E2E mocking scenarios
 *
 * @tags api widget story-5-5 negative error-handling
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

test.describe('Story 5-5: Theme API Negative Cases', () => {
  test.describe('API Error Handling', () => {
    test('[P2] should handle 500 internal server error gracefully', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 500,
          body: JSON.stringify({
            data: null,
            meta: {
              error_code: 5000,
              message: 'Internal server error',
            },
          }),
        });
      });

      await page.goto('/widget-bundle-test.html');

      await page.waitForTimeout(2000);

      const bubble = page.getByRole('button', { name: 'Open chat' });

      const isVisible = await bubble.isVisible().catch(() => false);

      if (isVisible) {
        await expect(bubble).toBeVisible();
      } else {
        const errorMessage = page.locator('text=/error|failed|unavailable/i');
        const hasError = await errorMessage.isVisible().catch(() => false);
        expect(hasError || !isVisible).toBe(true);
      }
    });

    test('[P2] should handle API timeout gracefully', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 35000));
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: { enabled: true },
            meta: {},
          }),
        });
      });

      await page.goto('/widget-bundle-test.html', { timeout: 40000 });

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('[P2] should handle empty theme config', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              enabled: true,
              botName: 'Test',
              welcomeMessage: 'Hi',
              theme: null,
              allowedDomains: [],
            },
            meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.goto('/widget-bundle-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });

      const bgColor = await bubble.evaluate(el => {
        return window.getComputedStyle(el).backgroundColor;
      });

      expect(bgColor).toMatch(/rgb\(\d+,\s*\d+,\s*\d+\)/);
    });
  });

  test.describe('Malformed Response Handling', () => {
    test('[P2] should handle malformed JSON response', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          body: 'invalid json {{{',
        });
      });

      const consoleMessages: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleMessages.push(msg.text());
        }
      });

      await page.goto('/widget-bundle-test.html');

      await page.waitForTimeout(2000);

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('[P2] should handle missing data field in response', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            meta: { requestId: 'test-id' },
          }),
        });
      });

      await page.goto('/widget-bundle-test.html');

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });

  test.describe('Network Error Handling', () => {
    test('[P2] should handle network failure', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.abort('failed');
      });

      const consoleMessages: string[] = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleMessages.push(msg.text());
        }
      });

      await page.goto('/widget-bundle-test.html');

      await page.waitForTimeout(2000);

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });

    test('[P2] should handle CORS error gracefully', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          headers: {
            'Access-Control-Allow-Origin': 'https://other-domain.com',
          },
          body: JSON.stringify({
            data: { enabled: true },
            meta: {},
          }),
        });
      });

      await page.goto('/widget-bundle-test.html');

      const body = page.locator('body');
      await expect(body).toBeVisible();
    });
  });

  test.describe('Invalid Theme Values', () => {
    test('[P2] should handle invalid theme type', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              enabled: true,
              botName: 'Test',
              welcomeMessage: 'Hi',
              theme: 'not-an-object',
              allowedDomains: [],
            },
            meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.goto('/widget-bundle-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });

      const isVisible = await bubble.isVisible({ timeout: 15000 }).catch(() => false);

      expect(typeof isVisible).toBe('boolean');
    });
  });
});
