import { test, expect } from '@playwright/test';

test.describe('Story 9-1 Visual Regression Tests', () => {
  test('[Visual] Light mode - Chat window', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible();
    
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('story-9-1-light-mode-chat-window.png', {
      maxDiffPixels: 100,
      threshold: 0.2,
    });
  });

  test('[Visual] Dark mode - Chat window', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible();
    
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('story-9-1-dark-mode-chat-window.png', {
      maxDiffPixels: 100,
      threshold: 0.2,
    });
  });

  test('[Visual] Theme toggle interaction', async ({ page }) => {
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const themeToggle = page.getByRole('button', { name: /Theme:/ });
    await expect(themeToggle).toBeVisible();
    
    await expect(page).toHaveScreenshot('story-9-1-theme-toggle-initial.png', {
      maxDiffPixels: 100,
    });
    
    await themeToggle.click();
    await page.waitForTimeout(500);
    
    await expect(page).toHaveScreenshot('story-9-1-theme-toggle-after-click.png', {
      maxDiffPixels: 100,
    });
  });

  test('[Visual] Message bubbles with glow effect', async ({ page }) => {
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const input = page.getByLabel('Type a message');
    await input.fill('Test message with glow effect');
    await page.getByRole('button', { name: 'Send message' }).click();
    
    const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Test message with glow effect' });
    await expect(userMessage).toBeVisible();
    
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('story-9-1-glow-effect-message-bubble.png', {
      maxDiffPixels: 100,
    });
  });

  test('[Visual] Mobile responsive - Dark mode', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible();
    
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('story-9-1-mobile-dark-mode.png', {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test('[Visual] Glassmorphism effect - Desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible();
    
    await page.waitForTimeout(1000);
    
    await expect(page).toHaveScreenshot('story-9-1-glassmorphism-desktop.png', {
      maxDiffPixels: 150,
      threshold: 0.2,
    });
  });
});
