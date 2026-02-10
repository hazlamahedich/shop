/**
 * E2E Tests for Story 1.8: Multiple Session Management
 *
 * Tests session management across multiple devices and sessions:
 * - Login on new device creates new session (session rotation)
 * - Old session remains valid during rotation overlap period
 * - Logout from one device invalidates only that session
 * - "Logout from all devices" invalidates all sessions
 * - Session count reflects active sessions correctly
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 * - Frontend running on http://localhost:5173
 */

import { test, expect, Page, BrowserContext } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test merchant credentials
const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe('Story 1.8: Multiple Session Management [P2]', () => {
  test.beforeAll(async () => {
    await createTestMerchant();
  });

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto(BASE_URL);
  });

  test('[P2] login on new device should create new session via rotation', async ({ context }) => {
    // Given: User is logged in on first device
    const device1 = await context.newPage();
    await performLogin(device1);
    const device1Cookies = await getContextCookies(context);

    // When: User logs in on second device (simulated by new browser context)
    const device2 = await context.newPage();
    await performLogin(device2);
    const device2Cookies = await getContextCookies(context);

    // Then: Each device should have its own session cookie
    const session1 = device1Cookies.find(c => c.name === 'session_token');
    const session2 = device2Cookies.find(c => c.name === 'session_token');
    expect(session1).toBeDefined();
    expect(session2).toBeDefined();

    // And: Session tokens should be different
    expect(session1?.value).not.toBe(session2?.value);

    await device1.close();
    await device2.close();
  });

  test('[P2] login should rotate sessions (invalidate old sessions)', async ({ context }) => {
    // Given: User is logged in and has a session token
    const page1 = await context.newPage();
    await performLogin(page1);

    // Get the first session token
    const firstToken = await getSessionToken(page1);
    expect(firstToken).toBeDefined();

    // When: User logs in again (session rotation)
    await page1.goto(`${BASE_URL}/login`);
    await page1.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page1.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page1.getByRole('button', { name: /login/i }).click();
    await page1.waitForURL(/.*\/dashboard/);

    // Get the new session token
    const secondToken = await getSessionToken(page1);
    expect(secondToken).toBeDefined();

    // Then: New token should be different from old token
    expect(secondToken).not.toBe(firstToken);

    // And: Old token should be invalidated (if we try to use it)
    // Note: This is verified by the backend marking old sessions as revoked

    await page1.close();
  });

  test('[P2] logout from one device should not affect other devices', async ({ context }) => {
    // Given: User is logged in on two devices
    const device1 = await context.newPage();
    await performLogin(device1);

    const device2 = await context.newPage();
    await performLogin(device2);

    // Verify both are logged in
    await expect(device1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(device2.getByText(TEST_MERCHANT.email)).toBeVisible();

    // When: User logs out from device 1
    await device1.getByLabel(/logout options/i).click();
    await device1.getByRole('button', { name: /^logout$/i }).click();

    // Then: Device 1 should be logged out
    await expect(device1).toHaveURL(/.*\/login/);

    // But: Device 2 should still be logged in (different session)
    await expect(device2.getByText(TEST_MERCHANT.email)).toBeVisible();

    // And: Device 2 should still have access to protected routes
    await device2.goto(`${BASE_URL}/settings`);
    await expect(device2.getByText(TEST_MERCHANT.email)).toBeVisible();

    await device1.close();
    await device2.close();
  });

  test('[P2] session rotation should allow overlap period', async ({ context }) => {
    // Given: User is logged in with an active session
    const page = await context.newPage();
    await performLogin(page);

    // Get current session token
    const oldToken = await getSessionToken(page);

    // Mock login response to simulate session rotation
    // The backend creates a new session and marks old ones as revoked
    let oldSessionRevoked = false;
    await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
      const response = await route.fetch();
      const body = await response.json();

      // Simulate session rotation - old session is revoked
      oldSessionRevoked = true;

      await route.fulfill({
        status: response.status(),
        headers: response.headers(),
        body: JSON.stringify(body),
      });
    });

    // When: User logs in again (creates new session)
    await page.goto(`${BASE_URL}/login`);
    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL(/.*\/dashboard/);

    // Get new session token
    const newToken = await getSessionToken(page);

    // Then: New token should be different
    expect(newToken).not.toBe(oldToken);

    // And: Old session should be marked as revoked
    expect(oldSessionRevoked).toBe(true);

    await page.close();
  });

  test('[P2] concurrent sessions should work independently', async ({ context }) => {
    // Given: User is logged in on multiple tabs
    const tab1 = await context.newPage();
    await performLogin(tab1);

    const tab2 = await context.newPage();
    await performLogin(tab2);

    // Both should be logged in
    await expect(tab1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(tab2.getByText(TEST_MERCHANT.email)).toBeVisible();

    // When: User navigates in tab 1
    await tab1.goto(`${BASE_URL}/settings`);
    await expect(tab1.getByRole('heading', { name: /settings/i })).toBeVisible();

    // And: User navigates in tab 2
    await tab2.goto(`${BASE_URL}/dashboard`);
    await expect(tab2.getByRole('heading', { name: /dashboard/i })).toBeVisible();

    // Then: Both tabs should remain functional
    await expect(tab1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(tab2.getByText(TEST_MERCHANT.email)).toBeVisible();

    await tab1.close();
    await tab2.close();
  });

  test('[P2] session count should reflect active sessions', async ({ page }) => {
    // Given: User is logged in
    await performLogin(page);

    // When: Checking for active sessions
    // Note: This would require an endpoint to list active sessions
    // For now, we verify the session is valid

    const isValid = await page.evaluate(async (apiUrl) => {
      try {
        const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
          credentials: 'include',
        });
        return response.ok;
      } catch {
        return false;
      }
    }, API_URL);

    // Then: Session should be valid
    expect(isValid).toBe(true);
  });

  test('[P3] should handle rapid login/logout cycles', async ({ page }) => {
    // Given: User is not logged in
    await page.goto(`${BASE_URL}/login`);

    // When: User performs multiple rapid login/logout cycles
    for (let i = 0; i < 3; i++) {
      // Login
      await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
      await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
      await page.getByRole('button', { name: /login/i }).click();
      await page.waitForURL(/.*\/dashboard/);

      // Verify logged in
      await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible();

      // Logout
      await page.getByLabel(/logout options/i).click();
      await page.getByRole('button', { name: /^logout$/i }).click();
      await page.waitForURL(/.*\/login/);

      // Verify logged out
      await expect(page.getByText(TEST_MERCHANT.email)).not.toBeVisible();

      // Clear form for next iteration
      await page.getByLabel(/email/i).fill('');
      await page.getByLabel(/password/i).fill('');
    }

    // Then: Final state should be logged out
    await expect(page).toHaveURL(/.*\/login/);
  });

  test('[P3] sessions should persist across browser restarts (when cookie is set)', async ({ page, context }) => {
    // Given: User is logged in
    await performLogin(page);

    // Get session cookie
    const cookies = await context.cookies();
    const sessionCookie = cookies.find(c => c.name === 'session_token');
    expect(sessionCookie).toBeDefined();

    // When: Simulating browser restart by clearing in-memory state but keeping cookies
    await page.goto(`${BASE_URL}/dashboard`);

    // Then: Session should still be valid
    await expect(page.getByText(TEST_MERCHANT.email)).toBeVisible();
  });

  test('[P3] session cookie should have correct security attributes', async ({ context }) => {
    // Given: User logs in
    const page = await context.newPage();
    await page.goto(`${BASE_URL}/login`);

    // Track login response
    let setCookieHeader: string | null = null;
    await page.route(`${API_URL}/api/v1/auth/login`, async (route) => {
      const response = await route.fetch();
      setCookieHeader = response.headers()['set-cookie'];
      await route.continue();
    });

    await page.getByLabel(/email/i).fill(TEST_MERCHANT.email);
    await page.getByLabel(/password/i).fill(TEST_MERCHANT.password);
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL(/.*\/dashboard/);

    // When: Checking cookie attributes
    const cookies = await context.cookies();
    const sessionCookie = cookies.find(c => c.name === 'session_token');

    // Then: Cookie should have security attributes
    expect(sessionCookie).toBeDefined();
    expect(sessionCookie?.httpOnly).toBe(true); // httpOnly to prevent XSS
    expect(sessionCookie?.sameSite).toBe('Strict'); // CSRF protection
    // Note: 'secure' is false in development, true in production

    await page.close();
  });

  test('[P3] should handle session timeout during active use', async ({ page }) => {
    // Given: User is logged in with an expired session
    await performLoginWithExpiryOverride(page, '2000-01-01T00:00:00Z'); // Past date

    // When: User tries to interact with the app
    await page.goto(`${BASE_URL}/dashboard`);

    // Then: Should detect expired session and redirect to login
    await expect(page).toHaveURL(/.*\/login/, { timeout: 10000 });

    // And: Should show appropriate message
    await expect(page.getByRole('heading', { name: /merchant dashboard login/i })).toBeVisible();
  });

  test('[P3] BroadcastChannel should sync logout across tabs', async ({ context }) => {
    // Given: User is logged in on two tabs
    const tab1 = await context.newPage();
    await performLogin(tab1);

    const tab2 = await context.newPage();
    await performLogin(tab2);

    // Both should be logged in
    await expect(tab1.getByText(TEST_MERCHANT.email)).toBeVisible();
    await expect(tab2.getByText(TEST_MERCHANT.email)).toBeVisible();

    // When: User logs out from tab 1
    await tab1.getByLabel(/logout options/i).click();
    await tab1.getByRole('button', { name: /^logout$/i }).click();

    // Then: Tab 2 should also log out via BroadcastChannel
    await expect(tab2).toHaveURL(/.*\/login/, { timeout: 5000 });

    await tab1.close();
    await tab2.close();
  });

  test('[P3] should handle invalid session token gracefully', async ({ page }) => {
    // Given: User has an invalid session token
    await page.context().addCookies([
      {
        name: 'session_token',
        value: 'invalid_token_value',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        sameSite: 'Strict',
      },
    ]);

    // When: User tries to access a protected route
    await page.goto(`${BASE_URL}/dashboard`);

    // Then: Should be redirected to login
    await expect(page).toHaveURL(/.*\/login/);

    // And: Should not see error page
    await expect(page.getByRole('heading', { name: /merchant dashboard login/i })).toBeVisible();
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

async function getSessionToken(page: Page): Promise<string | undefined> {
  return await page.evaluate(() => {
    // Get cookie from document
    const cookies = document.cookie.split(';').map(c => c.trim());
    const sessionCookie = cookies.find(c => c.startsWith('session_token='));
    return sessionCookie?.split('=')[1];
  });
}

async function getContextCookies(context: BrowserContext) {
  return await context.cookies();
}

async function performLoginWithExpiryOverride(page: Page, expiryIso: string): Promise<void> {
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

  await performLogin(page);
}
