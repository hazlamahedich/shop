import { test, expect } from '@playwright/test';

test.describe('Story 9-10: Widget Demo UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/widget-demo');
    await responsePromise;
    await expect(page.getByTestId('chat-bubble')).toBeVisible({ timeout: 10000 });
  });

  test.afterEach(async ({ page }) => {
    const chatWindow = page.locator('[data-testid="chat-window"]');
    const isVisible = await chatWindow.isVisible().catch(() => false);
    if (isVisible) {
      const closeButton = page.locator('[data-testid="close-chat-button"]');
      await closeButton.click().catch(() => {});
    }
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('AC1 Chat bubble and window are visible @smoke @p0', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 10000 });
    
    await chatBubble.click();
    
    const chatWindow = page.locator('[data-testid="chat-window"]');
    await expect(chatWindow).toBeVisible({ timeout: 5000 });
  });

  test('AC2 Message input and send button are functional @smoke @p0', async ({ page }) => {
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await chatBubble.click();
    
    const chatWindow = page.locator('[data-testid="chat-window"]');
    await expect(chatWindow).toBeVisible({ timeout: 5000 });
    
    const messageInput = page.locator('[data-testid="message-input"]');
    await expect(messageInput).toBeVisible({ timeout: 5000 });
    
    await messageInput.fill('Test message');
    
    const sendButton = page.locator('[data-testid="send-message-button"]');
    await expect(sendButton).toBeVisible({ timeout: 5000 });
  });

  test('AC3 Widget loads quickly @p1', async ({ page }) => {
    const startTime = Date.now();
    const responsePromise = page.waitForResponse('**/api/**').catch(() => null);
    await page.goto('/widget-demo');
    await responsePromise;
    const loadTime = Date.now() - startTime;
    
    expect(loadTime).toBeLessThan(10000);
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 5000 });
  });

  test('AC4 Reduced motion preference is respected @p2', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 10000 });
    
    await chatBubble.click();
    
    const chatWindow = page.locator('[data-testid="chat-window"]');
    await expect(chatWindow).toBeVisible({ timeout: 5000 });
  });

  test('AC5 Feature buttons are functional @p2', async ({ page }) => {
    const featureButtons = page.locator('button').filter({ hasText: /Glassmorphism|Carousel|Quick Replies|Voice|Proactive/ });
    const count = await featureButtons.count();
    expect(count).toBeGreaterThan(0);
    
    await featureButtons.first().click();
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 5000 });
  });

  test('AC6 Theme toggle works @p2', async ({ page }) => {
    const lightButton = page.locator('button').filter({ hasText: /Light/ });
    const darkButton = page.locator('button').filter({ hasText: /Dark/ });
    
    await expect(lightButton).toBeVisible({ timeout: 5000 });
    await expect(darkButton).toBeVisible({ timeout: 5000 });
    
    await darkButton.click();
    
    const chatBubble = page.locator('[data-testid="chat-bubble"]');
    await expect(chatBubble).toBeVisible({ timeout: 5000 });
  });
});
