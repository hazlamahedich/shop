/**
 * E2E Tests for Story 1.8: Session Expiry and Warning
 *
 * Tests session expiry behavior including:
 * - Session expiry warning appears at 19 hours (5 minutes before expiry)
 * - Warning banner offers "Extend Session" button
 * - Clicking "Extend Session" calls refresh API and dismisses warning
 * - Warning auto-dismisses if session is extended elsewhere
 * - Auto-logout occurs when session fully expires
 * - After logout, redirect to login page occurs
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
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

// Session constants (must match backend)
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours
const WARNING_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes
const TIME_AT_WARNING = SESSION_DURATION_MS - WARNING_THRESHOLD_MS; // 23h 55m

test.describe('Story 1.8: Session Expiry Warning [P1]', () => {
  test.beforeAll(async () => {
    await createTestMerchant();
  });

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(BASE_URL);
  });

  test('[P1] should show session expiry warning at 19 hours remaining', async ({ page }) => {
    // Given: User is logged in with a session expiring soon
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);

    // When: Session is within warning threshold (5 minutes remaining)
    // Navigate to dashboard where warning component is rendered
    await page.goto(`${BASE_URL}/dashboard`);

    // Then: Warning banner should be visible
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // And: Warning should show time remaining
    await expect(page.getByText(/Your session will expire in/i)).toBeVisible();
  });

  test('[P1] warning banner should offer Extend Session button', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: Looking at the warning banner
    // Then: Should see "Extend Session" or "Refresh Session" button
    const refreshButton = page.getByRole('button', { name: /refresh session|extend session/i });
    await expect(refreshButton).toBeVisible();
  });

  test('[P1] clicking Extend Session should call refresh API and dismiss warning', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // Track refresh API calls
    let refreshCalled = false;
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      refreshCalled = true;
      // Mock successful refresh with extended session
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // When: User clicks "Refresh Session" button
    const refreshButton = page.getByRole('button', { name: /refresh session/i });
    await refreshButton.click();

    // Then: Refresh API should be called
    expect(refreshCalled).toBe(true);

    // And: Warning should be dismissed after successful refresh
    await expect(warningBanner).not.toBeVisible({ timeout: 5000 });
  });

  test('[P1] warning should auto-dismiss if session is extended elsewhere', async ({ page, context }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // Create second tab (simulates session extended elsewhere)
    const page2 = await context.newPage();
    await page2.goto(`${BASE_URL}/dashboard`);

    // Extend session from second tab
    await page2.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // Trigger refresh from second tab via BroadcastChannel
    await page2.evaluate(() => {
      const channel = new BroadcastChannel('auth-channel');
      channel.postMessage({ type: 'SESSION_REFRESHED' });
      channel.close();
    });

    // When: Session is refreshed elsewhere
    // Then: Warning should auto-dismiss in first tab
    await expect(warningBanner).not.toBeVisible({ timeout: 10000 });

    await page2.close();
  });

  test('[P1] should auto-logout when session fully expires', async ({ page }) => {
    // Given: User is logged in with session that has already expired
    await performLoginWithCustomExpiry(page, 0); // Already expired

    // When: User tries to navigate or interact
    await page.goto(`${BASE_URL}/dashboard`);

    // Then: Should be redirected to login page
    await expect(page).toHaveURL(/.*\/login/, { timeout: 10000 });

    // And: Should see login form
    await expect(page.getByRole('heading', { name: /merchant dashboard login/i })).toBeVisible();
  });

  test('[P1] should redirect to login page after auto-logout', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Mock expired session on next API call
    await page.route(`${API_URL}/api/v1/auth/me`, async (route) => {
      await route.abort();
    });

    // When: Session expires and user tries to access protected route
    await page.goto(`${BASE_URL}/settings`);

    // Then: Should be redirected to login page
    await expect(page).toHaveURL(/.*\/login/);

    // And: Should not see authenticated content
    await expect(page.getByText(TEST_MERCHANT.email)).not.toBeVisible();
  });

  test('[P2] warning should show logout button for immediate logout', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: Looking at warning banner
    // Then: Should see "Logout" button
    const logoutButton = page.getByRole('button', { name: /^logout$/i });
    await expect(logoutButton).toBeVisible();

    // When: User clicks logout button
    await logoutButton.click();

    // Then: Should be redirected to login page
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('[P2] warning should have close button to dismiss temporarily', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: User clicks close button
    const closeButton = page.getByRole('button', { name: /close warning/i });
    await closeButton.click();

    // Then: Warning should be dismissed
    await expect(warningBanner).not.toBeVisible();

    // And: Warning should reappear on next check interval (30 seconds)
    // Note: We skip waiting for this as it would make test too slow
  });

  test('[P2] should display countdown timer in warning', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: Looking at the warning message
    // Then: Should see time remaining displayed
    const timeText = await page.getByText(/Your session will expire in \d+:\d{2}/).textContent();
    expect(timeText).toMatch(/\d+:\d{2}/); // Format: "minutes:seconds"
  });

  test('[P2] should show loading state while refreshing session', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // Delay the refresh response to see loading state
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      await new Promise(resolve => setTimeout(resolve, 500));
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // When: User clicks refresh button
    const refreshButton = page.getByRole('button', { name: /refresh session/i });
    await refreshButton.click();

    // Then: Should see loading state
    await expect(page.getByText(/refreshing...|loading/i)).toBeVisible();

    // And: Button should be disabled during refresh
    await expect(refreshButton).toBeDisabled();
  });

  test('[P3] should not show warning when session is not expiring soon', async ({ page }) => {
    // Given: User is logged in with fresh session (24 hours remaining)
    await performLoginWithCustomExpiry(page, SESSION_DURATION_MS);
    await page.goto(`${BASE_URL}/dashboard`);

    // When: Session is not within warning threshold
    // Then: Warning banner should not be visible
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).not.toBeVisible();
  });

  test('[P3] warning should be accessible with keyboard navigation', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert').filter({ hasText: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: User tabs through the warning
    await page.keyboard.press('Tab');

    // Then: Focus should move to refresh button
    const refreshButton = page.getByRole('button', { name: /refresh session/i });
    await expect(refreshButton).toBeFocused();

    // Tab again to logout button
    await page.keyboard.press('Tab');
    const logoutButton = page.getByRole('button', { name: /^logout$/i });
    await expect(logoutButton).toBeFocused();
  });

  test('[P3] warning should have proper ARIA attributes', async ({ page }) => {
    // Given: User is logged in with expiring session
    await performLoginWithCustomExpiry(page, TIME_AT_WARNING);
    await page.goto(`${BASE_URL}/dashboard`);

    // Wait for warning to appear
    const warningBanner = page.getByRole('alert', { name: /session will expire/i });
    await expect(warningBanner).toBeVisible();

    // When: Checking ARIA attributes
    // Then: Should have alert role
    await expect(warningBanner).toHaveAttribute('role', 'alert');

    // And: Should have aria-live for screen readers
    await expect(warningBanner).toHaveAttribute('aria-live', 'polite');

    // And: Buttons should have proper aria-labels
    const refreshButton = page.getByRole('button', { name: /refresh session/i });
    await expect(refreshButton).toHaveAttribute('aria-label', /refresh session/i);
  });
});

// Helper functions

async function createTestMerchant(): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/api/v1/test/create-merchant`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(TEST_MERCHANT),
    });

    if (!response.ok && response.status !== 409) {
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
  await page.waitForURL(/.*\/dashboard/, { timeout: 5000 });
}

/**
 * Perform login with a custom session expiration time.
 * This mocks the login response to set a specific expiration time.
 */
async function performLoginWithCustomExpiry(page: Page, sessionDurationMs: number): Promise<void> {
  // Intercept login request to return custom expiry
  await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
    const customExpiry = new Date(Date.now() + sessionDurationMs).toISOString();

    // Continue with original request but modify response
    const response = await route.fetch();
    const body = await response.json();

    // Override the expiration time
    body.session.expiresAt = customExpiry;

    await route.fulfill({
      status: response.status(),
      headers: response.headers(),
      body: JSON.stringify(body),
    });
  });

  await page.goto(`${BASE_URL}/login`);
  await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
  await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL(/.*\/dashboard/, { timeout: 5000 });
}
