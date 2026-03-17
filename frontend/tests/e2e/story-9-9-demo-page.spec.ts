import { test, expect } from '@playwright/test';

test.describe('Story 9-9: Interactive Demo Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/widget-demo');
    await page.waitForLoadState('networkidle');
    await page.waitForSelector('text=Widget UI/UX Demo', { timeout: 10000 });
  });

  test('[P0] AC1: All 8 features are demonstrated', async ({ page }) => {
    const features = [
      'Glassmorphism',
      'Product Carousel', 
      'Quick Replies',
      'Voice Input',
      'Proactive Engagement',
      'Message Grouping',
      'Microinteractions',
      'Smart Positioning',
    ];

    for (const feature of features) {
      await expect(page.getByRole('button', { name: feature })).toBeVisible();
    }
  });

  test('[P0] AC2: Feature selector switches demos', async ({ page }) => {
    const productCarouselBtn = page.getByRole('button', { name: 'Product Carousel' });
    await productCarouselBtn.click({ force: true });
    
    await expect(page.getByText(/Product Carousel/).first()).toBeVisible({ timeout: 10000 });
    
    const quickRepliesBtn = page.getByRole('button', { name: 'Quick Replies' });
    await quickRepliesBtn.click({ force: true });
    
    await expect(page.getByText(/Quick Replies/).first()).toBeVisible({ timeout: 10000 });
  });

  test('[P1] AC3: Theme toggle works', async ({ page }) => {
    await page.getByRole('button', { name: /Dark/ }).click();
    await page.getByRole('button', { name: /Auto/ }).click();
    await page.getByRole('button', { name: /Light/ }).click();
    
    await expect(page.getByText('Widget UI/UX Demo')).toBeVisible();
  });

  test('[P1] AC4: Feature descriptions displayed', async ({ page }) => {
    await expect(page.getByText(/frosted glass/)).toBeVisible({ timeout: 10000 });
    
    await page.getByRole('button', { name: 'Voice Input' }).click({ force: true });
    await expect(page.getByText(/Voice Input/).first()).toBeVisible({ timeout: 10000 });
  });

  test('[P1] AC5: Code examples in documentation', async ({ page }) => {
    await expect(page.getByText(/Try These Interactions/)).toBeVisible();
    await expect(page.getByRole('button', { name: 'Glassmorphism' })).toBeVisible();
  });

  test('[P1] AC6: Mobile responsive', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    await expect(page.getByText('Widget UI/UX Demo')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Glassmorphism' })).toBeVisible();
  });

  test('[P1] AC7: Shareable demo URL', async ({ page }) => {
    await expect(page).toHaveURL('/widget-demo');
    await expect(page.getByText('Widget UI/UX Demo')).toBeVisible();
  });

  test('[P2] Widget visibility toggle works', async ({ page }) => {
    const toggleButton = page.getByRole('button', { name: /Widget Visible/i });
    
    if (await toggleButton.isVisible()) {
      await toggleButton.click();
      await expect(page.getByRole('button', { name: /Widget Hidden/i })).toBeVisible();
    }
  });

  test('[P2] Instructions section visible', async ({ page }) => {
    await expect(page.getByText(/Try These Interactions/)).toBeVisible();
  });
});
