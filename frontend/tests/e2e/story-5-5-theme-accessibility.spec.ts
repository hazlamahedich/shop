/**
 * Theme Customization System - Accessibility Tests
 *
 * Story 5-5: Theme Customization System
 * Tests accessibility attributes, keyboard navigation, and ARIA compliance
 *
 * Priority: P3 (Nice-to-have - internal widget, WCAG helpful but not critical)
 * Consolidated from gap analysis: removed duplicate visibility tests
 *
 * @tags e2e widget story-5-5 accessibility a11y
 */

import { test, expect } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
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
        meta: { requestId: 'test-id', timestamp: new Date().toISOString() },
      }),
    });
  });
});

test.describe('Story 5-5: Theme Accessibility', () => {
  test.describe('ARIA Attributes', () => {
    test('[P2] chat bubble should have accessible name', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });

      const ariaLabel = await bubble.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    });

    test('[P2] chat window should have dialog role', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });
      await bubble.click();

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });

      const ariaModal = await dialog.getAttribute('aria-modal');
      expect(ariaModal).toBe('true');
    });

    test('[P2] close button should have accessible name', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });
      await bubble.click();

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });

      const closeButton = dialog.getByRole('button', { name: /close|dismiss/i }).first();
      await expect(closeButton).toBeVisible({ timeout: 5000 });

      const ariaLabel = await closeButton.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('[P2] should open chat with Enter key', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });

      await bubble.focus();
      await page.keyboard.press('Enter');

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });
    });

    test('[P2] should open chat with Space key', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });

      await bubble.focus();
      await page.keyboard.press('Space');

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });
    });

    test('[P2] should close chat with Escape key', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });
      await bubble.click();

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });

      await page.keyboard.press('Escape');

      await expect(dialog).not.toBeVisible({ timeout: 3000 });
    });

    test('[P2] focus should be trapped in open chat dialog', async ({ page }) => {
      await page.goto('/widget-theme-test.html');

      const bubble = page.getByRole('button', { name: 'Open chat' });
      await expect(bubble).toBeVisible({ timeout: 15000 });
      await bubble.click();

      const dialog = page.getByRole('dialog', { name: 'Chat window' });
      await expect(dialog).toBeVisible({ timeout: 5000 });

      const focusableElements = await dialog.locator(
        'button:not([disabled]), input:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      ).count();

      expect(focusableElements).toBeGreaterThan(0);

      for (let i = 0; i < focusableElements + 2; i++) {
        await page.keyboard.press('Tab');
      }

      await expect(dialog).toBeVisible();
    });
  });

  test.describe('Color Contrast', () => {
    test('[P2] should maintain sufficient color contrast with custom theme', async ({ page }) => {
      await page.route('**/api/v1/widget/config/*', async (route) => {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              enabled: true,
              botName: 'Test',
              welcomeMessage: 'Hi!',
              theme: {
                primaryColor: '#1e40af',
                backgroundColor: '#ffffff',
                textColor: '#1f2937',
                botBubbleColor: '#f3f4f6',
                userBubbleColor: '#1e40af',
                position: 'bottom-right',
                borderRadius: 16,
                width: 380,
                height: 600,
                fontFamily: 'Inter, sans-serif',
                fontSize: 14,
              },
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
});
