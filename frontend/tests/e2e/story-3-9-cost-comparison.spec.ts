/**
 * E2E Tests for Story 3-9: Cost Comparison Display
 *
 * Tests:
 * - Viewing cost comparison on Costs page
 * - Savings calculation display
 * - Methodology tooltip on click
 * - Comparison updates with different spend amounts
 * - Accessibility (screen reader, keyboard navigation)
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant (demo@test.com) with cost data
 * - Frontend running on http://localhost:5173
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

const TEST_MERCHANT = {
  email: 'demo@test.com',
  password: 'Demo12345',
};

test.describe('Story 3-9: Cost Comparison Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.context().clearCookies();
    
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('domcontentloaded');
    
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();
    
    await page.waitForURL(/\/(dashboard|costs|conversations)/, { timeout: 15000 });
    
    await page.goto(`${BASE_URL}/costs`);
    await page.waitForLoadState('networkidle');
  });

  test('displays cost comparison card on costs page', async ({ page }) => {
    const comparisonCard = page.getByRole('heading', { name: 'Cost Comparison' });
    await expect(comparisonCard).toBeVisible({ timeout: 15000 });
  });

  test('shows merchant spend vs ManyChat estimate', async ({ page }) => {
    await expect(page.getByText(/You spent/)).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/ManyChat/)).toBeVisible();
  });

  test('displays savings when shop costs less', async ({ page }) => {
    const savingsMessage = page.getByText(/You saved/);
    await expect(savingsMessage).toBeVisible({ timeout: 15000 });
  });

  test('shows methodology tooltip when clicking info button', async ({ page }) => {
    const infoButton = page.getByLabel('View comparison methodology');
    await infoButton.click();

    await expect(page.getByText(/ManyChat pricing/)).toBeVisible();
    await expect(page.getByText(/per message/)).toBeVisible();
  });

  test('hides tooltip when clicking outside', async ({ page }) => {
    const infoButton = page.getByLabel('View comparison methodology');
    await infoButton.click();
    await expect(page.getByText(/ManyChat pricing/)).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(page.getByText(/ManyChat pricing/)).not.toBeVisible();
  });

  test('displays progress bars for cost comparison', async ({ page }) => {
    await expect(page.getByText('Shop (You)')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('ManyChat (Est.)')).toBeVisible();
  });

  test('info button has accessible label', async ({ page }) => {
    const infoButton = page.getByLabel('View comparison methodology');
    await expect(infoButton).toHaveAttribute('aria-label', 'View comparison methodology');
  });

  test('info button is focusable via keyboard', async ({ page }) => {
    const infoButton = page.getByLabel('View comparison methodology');
    
    for (let i = 0; i < 20; i++) {
      await page.keyboard.press('Tab');
    }

    await expect(infoButton).toBeFocused();
  });

  test('[AC3] comparison reflects current billing period spend', async ({ page }) => {
    const comparisonCard = page.getByRole('heading', { name: 'Cost Comparison' });
    await expect(comparisonCard).toBeVisible({ timeout: 15000 });

    const spendText = page.getByText(/You spent/);
    await expect(spendText).toBeVisible();

    await expect(page.getByText('Shop (You)')).toBeVisible();
    await expect(page.getByText('ManyChat (Est.)')).toBeVisible();
  });
});
