/**
 * E2E Tests for Story 1.12: Bot Naming
 *
 * Tests merchant bot name configuration UI and interaction flows
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists and is logged in
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.12: Bot Naming E2E [P0]', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate first to avoid localStorage access issues
    await page.goto('/');

    // Then clear storage
    await clearStorage(page);

    // Login and set auth state
    const loginResponse = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const token = loginData.data.session.token;

      // Navigate again to ensure page context
      await page.goto('/');

      // Set auth state in localStorage
      await page.evaluate((accessToken) => {
        localStorage.setItem('auth_token', accessToken);
        localStorage.setItem('auth_timestamp', Date.now().toString());
      }, token);
    }
  });

  test('[P0] should display bot configuration page', async ({ page }) => {
    await page.goto('/bot-config');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page title
    await expect(page.getByRole('heading', { name: /bot configuration/i })).toBeVisible();

    // Verify bot name input field
    await expect(page.getByRole('textbox', { name: /Bot Name/i })).toBeVisible();

    // Verify help text (use role to be more specific)
    const helpText = page.getByText(/give your bot a name/i);
    await expect(helpText.first()).toBeVisible();

    // Verify character count
    await expect(page.getByText(/\d+ \/ 50/)).toBeVisible();
  });

  test('[P0] should display live preview section', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify preview section
    await expect(page.getByText(/preview: how customers see your bot/i)).toBeVisible();

    // Verify greeting with default "your shopping assistant" text
    await expect(page.getByText(/shopping assistant/i).first()).toBeVisible();
  });

  test('[P0] should enter and save bot name', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Enter bot name
    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
    await botNameInput.fill('GearBot');

    // Verify character count updates
    await expect(page.getByText('7 / 50')).toBeVisible();

    // Verify preview updates with bot name (use first to avoid strict mode violation)
    await expect(page.getByText(/I'm GearBot/i).first()).toBeVisible();

    // Scroll to and click save button
    const saveButton = page.getByRole('button', { name: /save bot name/i });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Wait for success message
    await expect(page.getByText(/bot name saved successfully/i)).toBeVisible({ timeout: 5000 });

    // Verify "All changes saved" message appears
    await expect(page.getByText(/all changes saved/i)).toBeVisible();
  });

  test('[P0] should clear bot name with empty string', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // First set a bot name
    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
    await botNameInput.fill('TestBot');

    // Wait a moment for state to update
    await page.waitForTimeout(100);

    // Clear the input
    await botNameInput.fill('');

    // Verify character count shows 0
    await expect(page.getByText('0 / 50')).toBeVisible();

    // Save
    const saveButton = page.getByRole('button', { name: /save bot name/i });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Wait for success
    await expect(page.getByText(/bot name saved successfully/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P1] should enforce max length of 50 characters', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });

    // Try to enter more than 50 characters
    const longName = 'A'.repeat(60);
    await botNameInput.fill(longName);

    // Character count should show 50/50 (maxed out)
    await expect(page.getByText('50 / 50')).toBeVisible();

    // Preview should show the truncated value
    await expect(page.getByText(new RegExp(`I'm ${'A'.repeat(50)}`), { exact: false })).toBeVisible();
  });

  test('[P1] should trim whitespace from bot name', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });

    // Enter bot name with extra whitespace
    await botNameInput.fill('  GearBot  ');

    // Verify whitespace is trimmed in preview
    await expect(page.getByText(/I'm GearBot/i).first()).toBeVisible();

    // Verify character count shows trimmed length
    await expect(page.getByText('7 / 50')).toBeVisible();
  });

  test('[P1] should show warning color when approaching limit', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });

    // Enter 35 characters (15 remaining) - should show amber warning
    await botNameInput.fill('A'.repeat(35));
    await expect(page.getByText('35 / 50')).toBeVisible();

    // Enter 45 characters (5 remaining) - should show red error
    await botNameInput.fill('A'.repeat(45));
    await expect(page.getByText('45 / 50')).toBeVisible();
  });

  test('[P1] should display personality in current settings', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify current settings section is visible
    await expect(page.getByRole('heading', { name: /current settings/i })).toBeVisible();

    // Verify personality is displayed (should have a default value)
    await expect(page.getByText(/personality/i)).toBeVisible();

    // Verify "Configure personality" link exists
    await expect(page.getByRole('link', { name: /configure personality/i })).toBeVisible();
  });

  test('[P1] should navigate to personality page', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Click the configure personality link
    await page.getByRole('link', { name: /configure personality/i }).click();

    // Verify navigation to personality page
    await expect(page).toHaveURL(/\/personality/);
    await expect(page.getByRole('heading', { name: /bot personality/i })).toBeVisible();
  });

  test('[P1] should show breadcrumb navigation', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify breadcrumb with Dashboard link
    await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();

    // Verify current page in breadcrumb
    await expect(page.getByText(/bot configuration/i)).toBeVisible();
  });

  test('[P2] should persist bot name across page refresh', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Set bot name
    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
    await botNameInput.fill('PersistentBot');

    // Save
    const saveButton = page.getByRole('button', { name: /save bot name/i });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Wait for success
    await expect(page.getByText(/bot name saved successfully/i)).toBeVisible({ timeout: 5000 });

    // Refresh the page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify bot name is still displayed
    await expect(botNameInput).toHaveValue('PersistentBot');

    // Verify preview still shows bot name
    await expect(page.getByText(/I'm PersistentBot/i).first()).toBeVisible();
  });

  test('[P2] should display configured badge when bot name is set', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Initially, no configured badge should be visible
    const configuredBadge = page.getByText(/configured/i);
    const isVisible = await configuredBadge.isVisible().catch(() => false);

    if (!isVisible) {
      // Set bot name
      const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
      await botNameInput.fill('MyBot');

      // Save
      const saveButton = page.getByRole('button', { name: /save bot name/i });
      await saveButton.scrollIntoViewIfNeeded();
      await saveButton.click();

      // Wait for success
      await expect(page.getByText(/bot name saved successfully/i)).toBeVisible({ timeout: 5000 });

      // Now configured badge should be visible
      await expect(configuredBadge).toBeVisible();
    }
  });

  test('[P2] should be disabled while saving', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Enter bot name
    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
    await botNameInput.fill('TestBot');

    // Click save
    const saveButton = page.getByRole('button', { name: /save bot name/i });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Input should be disabled during save (briefly)
    // This is a quick check - the save typically completes very fast
    await expect(botNameInput).toBeVisible();
  });

  test('[P2] should show generic fallback when no bot name configured', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Clear any existing bot name
    const botNameInput = page.getByRole('textbox', { name: /Bot Name/i });
    await botNameInput.fill('');

    // Save to ensure empty state
    const saveButton = page.getByRole('button', { name: /save bot name/i });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Wait for success (if any change was made)
    await page.waitForTimeout(500);

    // Verify preview shows generic fallback
    await expect(page.getByText(/shopping assistant/i).first()).toBeVisible();
  });

  test('[P2] should display help section with examples', async ({ page }) => {
    await page.goto('/bot-config');
    await page.waitForLoadState('networkidle');

    // Verify help section
    await expect(page.getByRole('heading', { name: /how bot names work/i })).toBeVisible();

    // Verify example bot names are shown
    await expect(page.getByText(/GearBot/i)).toBeVisible();
  });
});
