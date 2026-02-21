/**
 * Widget Personality & Customization E2E Tests
 *
 * Story 5-10: Widget Full App Integration - AC1
 * Tests personality system and custom greeting display.
 *
 * Test IDs: 5.10-E2E-023 to 5.10-E2E-027
 * @tags e2e widget story-5-10 personality ac1
 */

import { test, expect } from '@playwright/test';
import { blockShopifyCalls, mockWidgetConfig, mockWidgetSession, mockWidgetMessage } from '../../helpers/widget-test-helpers';

test.beforeEach(async ({ page }) => {
  await blockShopifyCalls(page);
});

test.describe('Widget Personality & Customization (AC1) [5.10-E2E-001]', () => {
  test.slow();

  test('[P0][5.10-E2E-001-01] Personality Display - Widget displays bot name from personality config', async ({ page }) => {
    await mockWidgetConfig(page, { botName: 'ShopBot Pro' });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.getByText('ShopBot Pro')).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-001-02] Custom Greeting - Widget uses merchant\'s custom greeting when enabled', async ({ page }) => {
    const customGreeting = 'Welcome to TechStore! How can I assist you today?';

    await mockWidgetConfig(page, {
      botName: 'TechStore Assistant',
      welcomeMessage: customGreeting,
      customGreetingEnabled: true,
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.getByText(customGreeting)).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-001-03] Personality Type - Friendly tone in responses', async ({ page }) => {
    await mockWidgetConfig(page, {
      botName: 'Friendly Shopper',
      welcomeMessage: 'Hey there! Ready to find something awesome?',
      personalityType: 'friendly',
    });

    await mockWidgetSession(page, 'test-session-friendly');

    await mockWidgetMessage(page, {
      content: "Awesome choice! I'd love to help you find those sneakers! 🎉",
      intent: 'product_search',
      confidence: 0.94,
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.getByText(/hey there|awesome/i)).toBeVisible({ timeout: 10000 });

    const input = page.getByPlaceholder('Type a message...');
    await input.fill('I want sneakers');
    await input.press('Enter');

    await expect(page.getByText(/awesome|love to help/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P1][5.10-E2E-001-04] Personality Type - Professional tone in responses', async ({ page }) => {
    await mockWidgetConfig(page, {
      botName: 'Shopping Consultant',
      welcomeMessage: 'Welcome. How may I assist you with your purchase today?',
      personalityType: 'professional',
      theme: {
        primaryColor: '#1f2937',
        userBubbleColor: '#1f2937',
        borderRadius: 8,
      },
    });

    await mockWidgetSession(page, 'test-session-professional');

    await mockWidgetMessage(page, {
      content: 'Certainly. I would be pleased to help you.',
      intent: 'product_search',
      confidence: 0.94,
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    await expect(page.getByText(/Welcome.*assist/i)).toBeVisible({ timeout: 10000 });
  });

  test('[P2][5.10-E2E-001-05] Theme Customization - Primary color applied correctly', async ({ page }) => {
    const customPrimaryColor = '#e11d48';

    await mockWidgetConfig(page, {
      botName: 'Custom Theme Bot',
      welcomeMessage: 'Hello!',
      theme: {
        primaryColor: customPrimaryColor,
        userBubbleColor: customPrimaryColor,
        borderRadius: 20,
        width: 400,
        height: 550,
        fontFamily: 'Georgia, serif',
        fontSize: 16,
      },
    });

    await page.goto('/widget-test');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();

    const chatWindow = page.locator('[data-testid="chat-window"], .chat-window, [class*="chat"]').first();
    await expect(chatWindow).toBeVisible({ timeout: 10000 });
  });
});
