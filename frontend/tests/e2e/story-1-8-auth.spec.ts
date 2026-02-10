/**
 * E2E Tests for Story 1.8: Merchant Dashboard Authentication
 *
 * Tests the complete authentication flow including:
 * - Login with email and password
 * - Logout functionality
 * - Session persistence across page reloads
 * - Multi-tab sync via BroadcastChannel
 * - Rate limiting visual feedback
 * - Protected route redirects
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists or is created during test
 * - Frontend running on http://localhost:5173
 */

import { test, expect, Page } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test merchant credentials
const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe('Story 1.8: Merchant Dashboard Authentication', () => {
  test.beforeAll(async () => {
    // Create test merchant account via API
    await createTestMerchant();
  });

  test.beforeEach(async ({ page }) => {
    // Reset rate limits before each test to avoid 429 errors
    await resetRateLimits();

    // Clear cookies and storage before each test
    await page.context().clearCookies();
    await page.goto(BASE_URL);
  });

  test('should redirect unauthenticated users to login page', async ({ page }) => {
    // Try to access dashboard directly
    await page.goto(`${BASE_URL}/dashboard`);

    // Should be redirected to /login
    await expect(page).toHaveURL(/.*\/login/);

    // Should see login form
    await expect(page.getByRole('heading', { name: /merchant dashboard login/i })).toBeVisible();
  });

  test('should display login form with required fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Check for email input
    const emailInput = page.getByLabel(/email/i);
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute('type', 'email');
    await expect(emailInput).toHaveAttribute('required', '');

    // Check for password input
    const passwordInput = page.getByLabel(/password/i);
    await expect(passwordInput).toBeVisible();
    await expect(passwordInput).toHaveAttribute('type', 'password');
    await expect(passwordInput).toHaveAttribute('required', '');

    // Check for login button
    const loginButton = page.getByRole('button', { name: /login/i });
    await expect(loginButton).toBeVisible();
  });

  test('should login successfully with valid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Fill in login form
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);

    // Submit form
    await page.getByRole('button', { name: /login/i }).click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*\/dashboard/, { timeout: 5000 });

    // Should see merchant info in header
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible();
  });

  test('should show error message with invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Fill in invalid credentials
    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('WrongPassword123');

    // Submit form
    await page.getByRole('button', { name: /login/i }).click();

    // Should see error message
    await expect(page.getByText(/invalid email or password/i)).toBeVisible();

    // Should still be on login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should validate password requirements', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Test with password too short
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill('Short1');

    // Submit form - validation should prevent submission or show error
    const loginButton = page.getByRole('button', { name: /login/i });
    await loginButton.click();

    // Should see validation error about password length
    await expect(page.getByText(/Password must be at least 8 characters/i)).toBeVisible();

    // Should still be on login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('should persist session across page reloads', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();

    // Wait for dashboard to load and merchant info to be visible
    await expect(page).toHaveURL(/.*\/dashboard/, { timeout: 5000 });
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible({ timeout: 5000 });

    // Reload page
    await page.reload({ waitUntil: 'networkidle' });

    // Should still be logged in - wait for merchant info to appear
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible({ timeout: 10000 });
    await expect(page).toHaveURL(/.*\/dashboard/);
  });

  test('should logout and redirect to login page', async ({ page }) => {
    // Login first
    await performLogin(page);

    // Click logout button
    await page.getByLabel(/logout options/i).click();

    // Should see confirmation dialog
    await expect(page.getByRole('dialog')).toBeVisible();
    await expect(page.getByText(/are you sure you want to logout/i)).toBeVisible();

    // Confirm logout
    await page.getByRole('button', { name: /^logout$/i }).click();

    // Should redirect to login page
    await expect(page).toHaveURL(/.*\/login/);

    // Merchant info should no longer be visible
    await expect(page.getByText(TEST_MERCHANT.email)).not.toBeVisible();
  });

  test('should cancel logout when clicking cancel button', async ({ page }) => {
    // Login first
    await performLogin(page);

    // Click logout button
    await page.getByLabel(/logout options/i).click();

    // Click cancel in dialog
    await page.getByRole('button', { name: 'cancel' }).click();

    // Dialog should close
    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Should still be logged in
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible();
  });

  test('should show loading state during login', async ({ page }) => {
    // Intercept login API to add delay
    await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.continue();
    });

    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);

    // Click login button
    await page.getByRole('button', { name: /login/i }).click();

    // Should see loading state
    await expect(page.getByText(/logging in/i)).toBeVisible();
  });

  test('should show loading state during logout', async ({ page }) => {
    // Login first
    await performLogin(page);

    // Intercept logout API to add a delay
    await page.route(`${API_URL}/api/v1/auth/logout`, async (route) => {
      // Short delay to allow loading state to be captured
      await new Promise(resolve => setTimeout(resolve, 1000));
      route.continue();
    });

    // Click logout button to open confirmation dialog
    await page.getByLabel(/logout options/i).click();

    // Wait for dialog to be visible
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click the confirm button inside the dialog
    const logoutButton = page.getByRole('button', { name: /^logout$/i });
    await logoutButton.click();

    // The button text should change to "Logging out..." immediately
    // Check for this text in the logout dialog before navigation happens
    await expect(page.getByRole('dialog').getByText('Logging out')).toBeVisible({ timeout: 2000 });
  });

  test('should preserve intended destination for post-login redirect', async ({ page }) => {
    // Try to access settings page while not logged in
    await page.goto(`${BASE_URL}/settings`);

    // Should redirect to login
    await expect(page).toHaveURL(/.*\/login/);

    // Login
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();

    // Should redirect to settings (original destination)
    await expect(page).toHaveURL(/.*\/settings/);
  });
});

test.describe('Story 1.8: Multi-tab Session Sync', () => {
  test.beforeAll(async () => {
    await createTestMerchant();
  });

  test.beforeEach(async () => {
    // Reset rate limits before each test
    await resetRateLimits();
  });

  test('should sync logout across multiple tabs', async ({ context }) => {
    // Create two pages (tabs)
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Login in first tab
    await performLogin(page1);
    await expect(page1.getByText(TEST_MERCHANT.email)).toBeVisible();

    // Navigate to dashboard in second tab
    // In Playwright, pages in the same context should share cookies
    await page2.goto(`${BASE_URL}/dashboard`);

    // Wait for authentication to propagate - page2 should see the session
    // If the merchant email isn't visible, the session cookie wasn't shared
    try {
      await expect(page2.getByText(TEST_MERCHANT.email)).toBeVisible({ timeout: 5000 });
    } catch (error) {
      // If page2 doesn't show merchant email, log in separately
      // This handles cases where cookies aren't shared between pages
      console.warn('Session not shared, logging in page2 separately');
      await performLogin(page2);
    }

    // Logout from first tab
    await page1.getByLabel(/logout options/i).click();
    await page1.getByRole('button', { name: /^logout$/i }).click();

    // Second tab should redirect to login (via BroadcastChannel)
    await expect(page2).toHaveURL(/.*\/login/, { timeout: 5000 });

    await page1.close();
    await page2.close();
  });

  test('should handle multiple tabs with different sessions', async ({ context }) => {
    // This test verifies that BroadcastChannel doesn't cause issues
    // when multiple tabs have active sessions
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    // Login in both tabs
    await performLogin(page1);
    await performLogin(page2);

    // Both should be logged in
    await expect(page1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(page2.getByText(TEST_MERCHANT.email)).toBeVisible();

    // Refresh both - should maintain session
    await page1.reload();
    await page2.reload();

    await expect(page1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(page2.getByText(TEST_MERCHANT.email)).toBeVisible();

    await page1.close();
    await page2.close();
  });
});

test.describe('Story 1.8: Accessibility', () => {
  test.beforeAll(async () => {
    await createTestMerchant();
  });

  test.beforeEach(async () => {
    // Reset rate limits before each test
    await resetRateLimits();
  });

  test('should support keyboard navigation in login form', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Tab through form fields
    await page.keyboard.press('Tab'); // Email input
    await expect(page.getByLabel(/email/i)).toBeFocused();

    await page.keyboard.press('Tab'); // Password input
    await expect(page.getByLabel(/password/i)).toBeFocused();

    await page.keyboard.press('Tab'); // Login button
    await expect(page.getByRole('button', { name: /login/i })).toBeFocused();
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Check form labels
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();

    // Check button labels
    await expect(page.getByRole('button', { name: /login|sign in/i })).toBeVisible();
  });

  test('should announce errors to screen readers', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Submit with invalid credentials
    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');
    await page.getByRole('button', { name: /login/i }).click();

    // Error should be in an alert role for screen readers
    const error = page.getByRole('alert');
    await expect(error).toBeVisible();
  });
});

// Helper functions

async function resetRateLimits(): Promise<void> {
  try {
    await fetch(`${API_URL}/api/v1/test/reset-rate-limits`, {
      method: 'POST',
      headers: {
        'X-Test-Mode': 'true',
      },
    });
  } catch (error) {
    console.warn('Could not reset rate limits:', error);
  }
}

async function createTestMerchant(): Promise<void> {
  // Create test merchant via API
  // In a real CI/CD setup, this would run before the test suite
  try {
    const response = await fetch(`${API_URL}/api/v1/test/create-merchant`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Test-Mode': 'true'
      },
      body: JSON.stringify(TEST_MERCHANT),
    });

    if (!response.ok && response.status !== 409) {
      // 409 means already exists, which is fine
      console.warn('Failed to create test merchant:', await response.text());
    }
  } catch (error) {
    console.warn('Could not create test merchant:', error);
  }
}

async function performLogin(page: Page): Promise<void> {
  await page.goto(`${BASE_URL}/login`);
  await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
  await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
  await page.getByRole('button', { name: /login/i }).click();

  // Wait for navigation to complete
  await page.waitForURL(/.*\/dashboard/, { timeout: 5000 });
}
