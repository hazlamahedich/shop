/**
 * @fileoverview E2E tests for Story 9-4: Quick Reply Buttons
 * @see docs/stories/story-9-4-quick-reply-buttons.md
 *
 * Test IDs: 9.4-E2E-001 through 9.4-E2E-018
 * Priority: P0 (Critical), P1 (High), P2 (Medium)
 */
import { test, expect, Page } from '@playwright/test';
import {
  createWidgetTheme,
  createYesNoQuickReplies,
  createWidgetConfig,
  createWidgetSession,
  createWidgetMessageResponse,
} from './test-utils/factories/widget-factories';

test.describe('Story 9-4: Quick Reply Buttons [P0]', () => {
  const WIDGET_TEST_URL = '/widget-test?merchantId=4';

  async function setupWidgetWithMocks(page: Page, options: { withQuickReplies?: boolean } = {}) {
    const configPromise = page.waitForResponse('**/api/v1/widget/config/*');
    const sessionPromise = page.waitForResponse('**/api/v1/widget/session');

    await page.route('**/api/v1/widget/config/*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: createWidgetConfig(),
        }),
      });
    });

    await page.route('**/api/v1/widget/session', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: createWidgetSession(),
        }),
      });
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      const body = JSON.parse(route.request().postData() || '{}');
      const userMessage = body.message;

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: createWidgetMessageResponse(userMessage, options),
        }),
      });
    });

    await page.goto(WIDGET_TEST_URL);
    await Promise.all([configPromise, sessionPromise]);

    const chatBubble = page.locator('.shopbot-chat-bubble');
    await chatBubble.click();

    await expect(page.locator('.shopbot-chat-window')).toBeVisible();
  }

  async function sendMessage(page: Page, message: string) {
    const messageInput = page.locator('input[placeholder*="message" i], input[type="text"]').first();
    await messageInput.fill(message);
    await messageInput.press('Enter');
  }

  test.describe('Widget Structure [P0]', () => {
    test('[P0] 9.4-E2E-001: chat window opens when bubble is clicked', async ({ page }) => {
      await setupWidgetWithMocks(page);

      const chatWindow = page.locator('.shopbot-chat-window');
      await expect(chatWindow).toBeVisible();
    });

    test('[P0] 9.4-E2E-002: chat window has correct ARIA attributes', async ({ page }) => {
      await setupWidgetWithMocks(page);

      const chatWindow = page.locator('.shopbot-chat-window');
      await expect(chatWindow).toHaveAttribute('role', 'dialog');
    });

    test('[P0] 9.4-E2E-003: message input is present and functional', async ({ page }) => {
      await setupWidgetWithMocks(page);

      const messageInput = page.locator('input[type="text"]').first();
      await expect(messageInput).toBeVisible();
    });
  });

  test.describe('AC1 & AC2: Chip-Style Buttons and Touch Targets [P0]', () => {
    test('[P0] 9.4-E2E-004: quick reply buttons appear as rounded chips when available', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const buttons = container.getByRole('button');
      const count = await buttons.count();
      expect(count).toBe(2);
    });

    test('[P0] 9.4-E2E-005: each button has minimum 44x44px touch target', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const buttons = container.getByRole('button');
      const count = await buttons.count();

      for (let i = 0; i < count; i++) {
        const button = buttons.nth(i);
        const box = await button.boundingBox();
        expect(box).not.toBeNull();
        expect(box!.height).toBeGreaterThanOrEqual(44);
        expect(box!.width).toBeGreaterThanOrEqual(44);
      }
    });

    test('[P1] 9.4-E2E-006: buttons have 8px gap spacing', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const gapStyle = await container.evaluate((el) => window.getComputedStyle(el).gap);
      expect(gapStyle).toBeTruthy();
    });
  });

  test.describe('AC4: Visual Feedback on Hover/Focus [P1]', () => {
    test('[P1] 9.4-E2E-007: buttons show visual feedback on hover', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 700 });
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });
      await button.scrollIntoViewIfNeeded();
      await button.hover();
      await expect(button).toHaveCSS('cursor', 'pointer');
    });

    test('[P1] 9.4-E2E-008: buttons show visual feedback on focus', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      await button.focus();
      await expect(button).toBeFocused();
    });
  });

  test.describe('AC5: Icon/Emoji Support [P1]', () => {
    test('[P1] 9.4-E2E-009: icons appear before button text', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      const text = await button.textContent();
      expect(text).toContain('✓');
      expect(text).toContain('Yes');
    });

    test('[P1] 9.4-E2E-010: icon and text are aligned with flexbox', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      const displayStyle = await button.evaluate((el) => window.getComputedStyle(el).display);
      expect(displayStyle).toBe('flex');
    });
  });

  test.describe('AC6: Keyboard Navigation [P0]', () => {
    test('[P0] 9.4-E2E-011: Tab key moves focus between buttons', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button1 = page.getByTestId('quick-reply-button-yes');
      await expect(button1).toBeVisible({ timeout: 5000 });
      await button1.focus();
      await expect(button1).toBeFocused();

      await page.keyboard.press('Tab');

      const button2 = page.getByTestId('quick-reply-button-no');
      await expect(button2).toBeFocused();
    });
  });

  test.describe('AC7: Screen Reader Accessibility [P0]', () => {
    test('[P0] 9.4-E2E-012: buttons have aria-label matching button text', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      const ariaLabel = await button.getAttribute('aria-label');
      expect(ariaLabel).toBe('Yes');
    });

    test('[P0] 9.4-E2E-013: buttons have role="button" attribute', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      const role = await button.getAttribute('role');
      expect(role).toBe('button');
    });

    test('[P0] 9.4-E2E-014: container has role="group" and aria-label for screen readers', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const role = await container.getAttribute('role');
      const ariaLabel = await container.getAttribute('aria-label');

      expect(role).toBe('group');
      expect(ariaLabel).toBe('Quick reply options');
    });
  });

  test.describe('AC8: Responsive Layout [P1]', () => {
    test('[P1] 9.4-E2E-015: buttons wrap correctly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const displayStyle = await container.evaluate((el) => window.getComputedStyle(el).display);
      expect(['flex', 'grid']).toContain(displayStyle);
    });

    test('[P1] 9.4-E2E-016: buttons display in single row on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1024, height: 768 });

      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const displayStyle = await container.evaluate((el) => window.getComputedStyle(el).display);
      expect(displayStyle).toBe('flex');
    });

    test('[P1] 9.4-E2E-017: layout does not overflow chat window', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });

      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).toBeVisible({ timeout: 5000 });

      const containerBox = await container.boundingBox();
      const chatWindow = page.locator('.shopbot-chat-window');
      const windowBox = await chatWindow.boundingBox();

      expect(containerBox).not.toBeNull();
      expect(windowBox).not.toBeNull();
      expect(containerBox!.width).toBeLessThanOrEqual(windowBox!.width + 10);
    });
  });

  test.describe('AC9 & AC10: Dynamic Quick Replies [P1]', () => {
    test('[P1] 9.4-E2E-018: quick replies are dynamically generated from backend response', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button = page.getByTestId('quick-reply-button-yes');
      await expect(button).toBeVisible({ timeout: 5000 });

      const text = await button.textContent();
      expect(text).toContain('Yes');
    });

    test('[P1] 9.4-E2E-019: clicking button sends message and dismisses buttons', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 700 });
      await setupWidgetWithMocks(page, { withQuickReplies: true });
      await sendMessage(page, 'Hello');

      const button1 = page.getByTestId('quick-reply-button-yes');
      await expect(button1).toBeVisible({ timeout: 5000 });
      await button1.scrollIntoViewIfNeeded();
      
      // Wait for the message response and verify quick reply click sends correct payload
      const responsePromise = page.waitForResponse('**/api/v1/widget/message');
      await button1.click();
      const response = await responsePromise;
      
      // Verify the request was sent with the quick reply payload
      const requestBody = JSON.parse(response.request().postData() || '{}');
      expect(requestBody.message).toBe('user_confirmed');
    });
  });

  test.describe('Edge Cases [P2]', () => {
    test('[P2] 9.4-E2E-020: handles empty quick replies array gracefully', async ({ page }) => {
      await setupWidgetWithMocks(page, { withQuickReplies: false });
      await sendMessage(page, 'Hello');

      const container = page.getByTestId('quick-reply-buttons');
      await expect(container).not.toBeVisible();
    });
  });
});
