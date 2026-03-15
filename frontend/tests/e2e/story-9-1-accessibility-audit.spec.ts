import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

test.describe('Story 9-1 Accessibility Audit', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/widget-test');
    
    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    
    const dialog = page.getByRole('dialog', { name: 'Chat window' });
    await expect(dialog).toBeVisible({ timeout: 10000 });
  });

  test('[A11Y] should have no accessibility violations in light mode', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'light' });
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('[A11Y] should have no accessibility violations in dark mode', async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark' });
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('[A11Y] should pass accessibility audit on theme toggle', async ({ page }) => {
    const themeToggle = page.getByRole('button', { name: /Theme:/ });
    await themeToggle.click();
    
    await page.waitForTimeout(500);
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('[A11Y] should have no critical violations with messages', async ({ page }) => {
    const input = page.getByLabel('Type a message');
    await input.fill('Test message for accessibility');
    await page.getByRole('button', { name: 'Send message' }).click();
    
    const userMessage = page.locator('.message-bubble--user').filter({ hasText: 'Test message for accessibility' });
    await expect(userMessage).toBeVisible();
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    const criticalViolations = accessibilityScanResults.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );
    
    expect(criticalViolations).toEqual([]);
  });
});
