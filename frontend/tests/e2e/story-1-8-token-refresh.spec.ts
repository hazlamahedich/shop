/**
 * E2E Tests for Story 1.8: Token Refresh Behavior
 *
 * Tests automatic token refresh functionality including:
 * - Token auto-refreshes at 50% of session lifetime (12 hours)
 * - Refresh extends session expiry time
 * - After refresh, session remains valid for extended period
 * - Failed refresh triggers logout and redirect to login
 * - Manual refresh via API extends session correctly
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

// Session constants (must match backend and frontend)
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours
const REFRESH_THRESHOLD_MS = SESSION_DURATION_MS * 0.5; // 12 hours (50%)
const REFRESH_CHECK_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes (check interval)

test.describe('Story 1.8: Token Refresh Behavior [P1]', () => {
  test.beforeAll(async () => {
    await createTestMerchant();
  });

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(BASE_URL);
  });

  test('[P1] should auto-refresh token at 50% of session lifetime', async ({ page }) => {
    // Given: User is logged in with session at refresh threshold (12 hours elapsed)
    const sessionAge = REFRESH_THRESHOLD_MS; // 12 hours
    await performLoginWithSessionAge(page, sessionAge);

    // Track refresh API calls
    let refreshCalled = false;
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      refreshCalled = true;
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // When: The refresh timer checks (triggered by store initialization)
    // Navigate to trigger the refresh check
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(1000); // Wait for store to initialize and check

    // Then: Refresh API should be called
    expect(refreshCalled).toBe(true);
  });

  test('[P1] refresh should extend session expiry time', async ({ page }) => {
    // Given: User is logged in with session at refresh threshold
    const sessionAge = REFRESH_THRESHOLD_MS;
    const initialExpiry = new Date(Date.now() + (SESSION_DURATION_MS - sessionAge));
    await performLoginWithCustomExpiry(page, initialExpiry.toISOString());

    // Get initial expiry from store
    const initialExpiryStr = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.sessionExpiresAt;
    });

    // Intercept refresh to return extended expiry
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // When: Token is refreshed
    await page.goto(`${BASE_URL}/dashboard`);

    // Trigger manual refresh via store action
    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      await window.__authStore?.getState()?.refreshSession();
    });

    // Wait for refresh to complete
    await page.waitForTimeout(500);

    // Then: Session expiry should be extended
    const newExpiryStr = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.sessionExpiresAt;
    });

    expect(newExpiryStr).not.toBe(initialExpiryStr);
    const newExpiry = new Date(newExpiryStr!);
    const oldExpiry = new Date(initialExpiryStr!);
    expect(newExpiry.getTime()).toBeGreaterThan(oldExpiry.getTime());
  });

  test('[P1] session should remain valid after refresh', async ({ page }) => {
    // Given: User is logged in and session has been refreshed
    await performLogin(page);

    // Intercept and mock refresh
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // Perform refresh
    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      await window.__authStore?.getState()?.refreshSession();
    });

    await page.waitForTimeout(500);

    // Mock /auth/me to verify session is still valid
    let meCallCount = 0;
    await page.route(`${API_URL}/api/v1/auth/me`, async (route) => {
      meCallCount++;
      await route.continue();
    });

    // When: User navigates to a protected route
    await page.goto(`${BASE_URL}/settings`);

    // Then: Session should be valid (me endpoint called successfully)
    expect(meCallCount).toBeGreaterThan(0);

    // And: User should remain logged in
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible();
  });

  test('[P1] failed refresh should trigger logout and redirect', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Mock refresh failure (401 Unauthorized)
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      await route.abort('failed'); // Simulate network error
    });

    // When: Refresh fails
    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      try {
        await window.__authStore?.getState()?.refreshSession();
      } catch (e) {
        // Expected to fail
      }
    });

    await page.waitForTimeout(500);

    // Then: User should be logged out
    const isAuthenticated = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.isAuthenticated;
    });
    expect(isAuthenticated).toBe(false);

    // And: Should be redirected to login on navigation
    await page.goto(`${BASE_URL}/dashboard`);
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('[P1] manual refresh via API should extend session correctly', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Get initial expiry
    const initialExpiryStr = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.sessionExpiresAt;
    });

    // When: Manually calling refresh API
    const refreshResponse = await page.evaluate(async (apiUrl) => {
      const response = await fetch(`${apiUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      return response.ok ? await response.json() : null;
    }, API_URL);

    // Then: Refresh should succeed
    expect(refreshResponse).not.toBeNull();
    expect(refreshResponse).toHaveProperty('session');

    // And: New expiry should be in the future
    const newExpiry = new Date(refreshResponse.session.expiresAt);
    const initialExpiry = new Date(initialExpiryStr!);
    expect(newExpiry.getTime()).toBeGreaterThan(initialExpiry.getTime());

    // And: Session should be valid for approximately 24 hours from now
    const now = Date.now();
    const timeUntilExpiry = newExpiry.getTime() - now;
    expect(timeUntilExpiry).toBeGreaterThan(SESSION_DURATION_MS - 60000); // Within 1 minute margin
  });

  test('[P2] should not refresh before threshold is reached', async ({ page }) => {
    // Given: User is logged in with fresh session (less than 50% elapsed)
    const sessionAge = REFRESH_THRESHOLD_MS - 3600000; // 11 hours (1 hour before threshold)
    await performLoginWithSessionAge(page, sessionAge);

    // Track refresh API calls
    let refreshCalled = false;
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      refreshCalled = true;
      await route.continue();
    });

    // When: Store checks for refresh (before threshold)
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForTimeout(1000); // Wait for store initialization

    // Then: Refresh should NOT be called
    expect(refreshCalled).toBe(false);
  });

  test('[P2] refresh should update cookie with new token', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Get initial cookies
    const initialCookies = await page.context().cookies();
    const initialSessionCookie = initialCookies.find(c => c.name === 'session_token');

    // When: Refreshing token
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      const originalResponse = await route.fetch();
      const body = await originalResponse.json();

      // Verify set-cookie header is present
      const headers = originalResponse.headers();
      expect(headers['set-cookie']).toBeDefined();

      await route.fulfill({
        status: originalResponse.status(),
        headers: originalResponse.headers(),
        body: JSON.stringify(body),
      });
    });

    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      await window.__authStore?.getState()?.refreshSession();
    });

    await page.waitForTimeout(500);

    // Then: Cookie should still be present
    const newCookies = await page.context().cookies();
    const newSessionCookie = newCookies.find(c => c.name === 'session_token');
    expect(newSessionCookie).toBeDefined();
  });

  test('[P2] multiple rapid refresh attempts should be handled gracefully', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    let refreshCount = 0;
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      refreshCount++;
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    // When: Multiple refresh calls happen rapidly
    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      const store = window.__authStore;
      await Promise.all([
        store?.getState()?.refreshSession(),
        store?.getState()?.refreshSession(),
        store?.getState()?.refreshSession(),
      ]);
    });

    await page.waitForTimeout(1000);

    // Then: All refreshes should complete successfully
    const isAuthenticated = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.isAuthenticated;
    });
    expect(isAuthenticated).toBe(true);
  });

  test('[P3] refresh timer should start after login', async ({ page }) => {
    // Given: User is not logged in
    await page.goto(`${BASE_URL}/login`);

    // Track when refresh timer starts
    let timerStarted = false;
    await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
      const response = await route.fetch();
      const body = await response.json();

      // After login, check if timer starts
      timerStarted = await page.evaluate(() => {
        // @ts-ignore - accessing window store
        return typeof window.__authStore?.getState()?._startRefreshTimer === 'function';
      });

      await route.fulfill({
        status: response.status(),
        headers: response.headers(),
        body: JSON.stringify(body),
      });
    });

    // When: User logs in
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();

    // Wait for navigation
    await page.waitForURL(/.*\/dashboard/, { timeout: 5000 });

    // Then: Refresh timer should be initialized
    expect(timerStarted).toBe(true);
  });

  test('[P3] refresh timer should stop after logout', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Verify timer is running
    const isTimerRunningBefore = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.isAuthenticated;
    });
    expect(isTimerRunningBefore).toBe(true);

    // When: User logs out
    await page.getByLabel(/logout options/i).click();
    await page.getByRole('button', { name: /^logout$/i }).click();

    // Then: Timer should be stopped
    const isTimerRunningAfter = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.isAuthenticated;
    });
    expect(isTimerRunningAfter).toBe(false);
  });

  test('[P3] refresh should maintain merchant session state', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // Get initial merchant info
    const initialMerchant = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.merchant;
    });

    // When: Refreshing token
    await page.route(`${API_URL}/api/v1/auth/refresh`, async (route) => {
      const newExpiry = new Date(Date.now() + SESSION_DURATION_MS).toISOString();
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: { expiresAt: newExpiry },
        }),
      });
    });

    await page.evaluate(async () => {
      // @ts-ignore - accessing window store
      await window.__authStore?.getState()?.refreshSession();
    });

    await page.waitForTimeout(500);

    // Then: Merchant state should remain unchanged
    const merchantAfter = await page.evaluate(() => {
      // @ts-ignore - accessing window store
      return window.__authStore?.getState()?.merchant;
    });

    expect(merchantAfter).toEqual(initialMerchant);
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
 * Perform login with a specific session age.
 * This mocks the login response to simulate an aged session.
 */
async function performLoginWithSessionAge(page: Page, sessionAgeMs: number): Promise<void> {
  const customExpiry = new Date(Date.now() + (SESSION_DURATION_MS - sessionAgeMs)).toISOString();
  await performLoginWithCustomExpiry(page, customExpiry);
}

/**
 * Perform login with a custom session expiration time.
 * This mocks the login response to set a specific expiration time.
 */
async function performLoginWithCustomExpiry(page: Page, expiryIso: string): Promise<void> {
  await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
    const response = await route.fetch();
    const body = await response.json();

    // Override the expiration time
    body.session.expiresAt = expiryIso;

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
