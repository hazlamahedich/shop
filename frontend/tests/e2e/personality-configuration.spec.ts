/**
 * E2E Tests for Story 1.10: Bot Personality Configuration
 *
 * Tests merchant personality configuration UI and interaction flows
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
test.describe('Story 1.10: Bot Personality Configuration E2E [P0]', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);

    // Login and set auth state
    const loginResponse = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const token = loginData.data.session.token;

      await page.goto('/');

      // Set auth state in localStorage
      await page.evaluate((accessToken) => {
        localStorage.setItem('auth_token', accessToken);
        localStorage.setItem('auth_timestamp', Date.now().toString());
      }, token);
    }
  });

  test('[P0] should display personality configuration page', async ({ page }) => {
    await page.goto('/personality');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Verify page title
    await expect(page.getByRole('heading', { name: /bot personality/i })).toBeVisible();

    // Verify all three personality cards are displayed
    await expect(page.getByRole('button', { name: /friendly.*casual.*warm/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /professional.*direct.*helpful/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /enthusiastic.*high-energy/i })).toBeVisible();
  });

  test('[P0] should select and save Professional personality', async ({ page }) => {
    await page.goto('/personality');
    await page.waitForLoadState('networkidle');

    // Click Professional personality card
    await page.getByRole('button', { name: /professional.*direct.*helpful/i }).click();

    // Verify selection state
    await expect(page.getByRole('button', { name: /professional.*direct.*helpful/i })).toHaveAttribute('aria-pressed', 'true');

    // Scroll to Save button
    const saveButton = page.getByRole('button', { name: 'Save Configuration' });
    await saveButton.scrollIntoViewIfNeeded();

    // Click save
    await saveButton.click();

    // Wait for success message
    await expect(page.getByText(/personality configuration saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P1] should customize greeting and reset', async ({ page }) => {
    await page.goto('/personality');
    await page.waitForLoadState('networkidle');

    // Select a personality first
    await page.getByRole('button', { name: /professional.*direct.*helpful/i }).click();

    // Wait for greeting editor section to appear
    const customizeSection = page.getByText('Customize Greeting');
    await customizeSection.scrollIntoViewIfNeeded();
    await expect(customizeSection).toBeVisible();

    // Enter custom greeting
    const customGreeting = 'Welcome to the future of shopping!';
    const greetingTextarea = page.getByRole('textbox', { name: 'Custom Greeting' });
    await greetingTextarea.scrollIntoViewIfNeeded();
    await greetingTextarea.fill(customGreeting);

    // Verify character count
    await expect(page.getByText(`${customGreeting.length} / 500`)).toBeVisible();

    // Click reset button
    const resetButton = page.getByRole('button', { name: 'Reset to Default' });
    await resetButton.scrollIntoViewIfNeeded();
    await resetButton.click();

    // Verify greeting is cleared
    await expect(greetingTextarea).toHaveValue('', { timeout: 5000 });
  });

  test('[P1] should enforce character limit on greeting', async ({ page }) => {
    await page.goto('/personality');
    await page.waitForLoadState('networkidle');

    // Select a personality
    await page.getByRole('button', { name: /friendly.*casual.*warm/i }).click();

    // Try to enter more than 500 characters
    const greetingTextarea = page.getByRole('textbox', { name: 'Custom Greeting' });
    await greetingTextarea.scrollIntoViewIfNeeded();

    const longGreeting = 'a'.repeat(600);
    await greetingTextarea.fill(longGreeting);

    // Verify character count shows 500/500 (maxed out)
    await expect(page.getByText('500 / 500')).toBeVisible();

    // Verify textarea value is truncated to 500
    const value = await greetingTextarea.inputValue();
    expect(value.length).toBe(500);
  });

  test('[P1] should persist configuration after page reload', async ({ page }) => {
    await page.goto('/personality');
    await page.waitForLoadState('networkidle');

    // Select and save Enthusiastic personality
    await page.getByRole('button', { name: /enthusiastic.*high-energy/i }).click();

    const saveButton = page.getByRole('button', { name: 'Save Configuration' });
    await saveButton.scrollIntoViewIfNeeded();
    await saveButton.click();

    // Wait for success message
    await expect(page.getByText(/personality configuration saved/i)).toBeVisible();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify Enthusiastic is still selected
    await expect(page.getByRole('button', { name: /enthusiastic.*high-energy/i })).toHaveAttribute('aria-pressed', 'true');
  });

  test('[P2] should switch between personalities', async ({ page }) => {
    await page.goto('/personality');
    await page.waitForLoadState('networkidle');

    // Select Friendly
    await page.getByRole('button', { name: /friendly.*casual.*warm/i }).click();
    await expect(page.getByRole('button', { name: /friendly.*casual.*warm/i })).toHaveAttribute('aria-pressed', 'true');

    // Switch to Professional
    await page.getByRole('button', { name: /professional.*direct.*helpful/i }).click();
    await expect(page.getByRole('button', { name: /professional.*direct.*helpful/i })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('button', { name: /friendly.*casual.*warm/i })).toHaveAttribute('aria-pressed', 'false');

    // Switch to Enthusiastic
    await page.getByRole('button', { name: /enthusiastic.*high-energy/i }).click();
    await expect(page.getByRole('button', { name: /enthusiastic.*high-energy/i })).toHaveAttribute('aria-pressed', 'true');
    await expect(page.getByRole('button', { name: /professional.*direct.*helpful/i })).toHaveAttribute('aria-pressed', 'false');
  });
});
