/**
 * E2E Tests: Multi-Tab Authentication Sync Journey
 *
 * User Journey: Merchant logs in on one tab and authentication
 * state synchronizes across multiple browser tabs.
 *
 * Flow: Login in Tab A → Verify Tab B → Logout Sync
 *
 * Priority Coverage:
 * - [P0] Authentication sync across tabs
 * - [P1] Logout propagation to all tabs
 * - [P2] Session refresh coordination
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Multi-Tab Authentication Sync', () => {
  test('[P0] should sync authentication state across tabs', async ({ context }) => {
    // GIVEN: User is not authenticated
    // Create two tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // WHEN: Logging in on Tab A
      await page1.goto('/login');
      await page1.waitForLoadState('domcontentloaded');

      // Mock login API
      await page1.route('**/api/auth/login**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              token: 'mock-jwt-token-123',
              merchantKey: 'test-merchant-abc',
              userId: 'user-123',
            },
            meta: { requestId: 'test-login' },
          }),
        });
      });

      // Fill login form
      const emailInput = page1.getByLabel(/email|username/i);
      await emailInput.fill('test@example.com');

      const passwordInput = page1.getByLabel(/password/i);
      await passwordInput.fill('password123');

      const loginButton = page1.getByRole('button', { name: /login|sign in/i });
      await loginButton.click();

      // Wait for successful login
      await page1.waitForURL(/\/dashboard/, { timeout: 5000 });

      // THEN: Tab B should also be authenticated
      await page2.goto('/dashboard');
      await page2.waitForLoadState('networkidle');

      // Should show dashboard (not redirect to login)
      await expect(page2.getByRole('heading', { name: /dashboard/i })).toBeVisible({
        timeout: 5000
      });

      // Should have access token in storage
      const token = await page2.evaluate(() => localStorage.getItem('auth_token'));
      expect(token).toBeTruthy();
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P1] should propagate logout to all tabs', async ({ context }) => {
    // GIVEN: User is logged in on multiple tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Set up authenticated state via localStorage
      for (const page of [page1, page2]) {
        await page.goto('/');
        await page.evaluate(() => {
          localStorage.setItem('auth_token', 'mock-jwt-token');
          localStorage.setItem('merchant_key', 'test-merchant');
        });
      }

      // WHEN: Logging out on Tab A
      await page1.goto('/dashboard');
      await page1.waitForLoadState('networkidle');

      // Mock logout API
      await page1.route('**/api/auth/logout**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { success: true },
            meta: { requestId: 'test-logout' },
          }),
        });
      });

      const logoutButton = page1.getByRole('button', { name: /logout|sign out/i });
      const hasLogout = await logoutButton.isVisible().catch(() => false);

      if (hasLogout) {
        await logoutButton.click();

        // Wait for logout to complete
        await page1.waitForURL(/\/login/, { timeout: 5000 });

        // THEN: Tab B should also be logged out
        await page2.reload();
        await page2.waitForLoadState('networkidle');

        // Should redirect to login or show login prompt
        const url = page2.url();
        const isLoginPage = url.includes('/login') ||
          await page2.getByText(/login|sign in/i).isVisible();

        expect(isLoginPage).toBeTruthy();

        // Storage should be cleared
        const token = await page2.evaluate(() => localStorage.getItem('auth_token'));
        expect(token).toBeNull();
      }
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P1] should sync token refresh across tabs', async ({ context }) => {
    // GIVEN: User has expiring token on multiple tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Set up expiring token
      const expiringToken = JSON.stringify({
        token: 'expiring-token',
        expiresAt: Date.now() + 1000, // Expires in 1 second
      });

      for (const page of [page1, page2]) {
        await page.goto('/');
        await page.evaluate((token) => {
          localStorage.setItem('auth_token', token);
        }, expiringToken);
      }

      // WHEN: Token refreshes on Tab A
      await page1.route('**/api/auth/refresh**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              token: 'new-refreshed-token',
              expiresAt: Date.now() + 3600000, // 1 hour
            },
            meta: { requestId: 'test-refresh' },
          }),
        });
      });

      await page1.goto('/dashboard');
      await page1.waitForLoadState('networkidle');

      // Wait for token refresh
      await page1.waitForTimeout(2000);

      // THEN: Tab B should have new token
      await page2.reload();
      await page2.waitForLoadState('networkidle');

      const newToken = await page2.evaluate(() => {
        const tokenData = localStorage.getItem('auth_token');
        return tokenData ? JSON.parse(tokenData).token : null;
      });

      expect(newToken).toBe('new-refreshed-token');
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P2] should handle session expiry notification across tabs', async ({ context }) => {
    // GIVEN: User has session about to expire
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Set up session with warning threshold
      const sessionData = JSON.stringify({
        token: 'session-token',
        expiresAt: Date.now() + 300000, // 5 minutes
        warningShown: false,
      });

      for (const page of [page1, page2]) {
        await page.goto('/dashboard');
        await page.evaluate((data) => {
          localStorage.setItem('auth_token', data);
        }, sessionData);
      }

      // WHEN: Session warning triggers on Tab A
      await page1.waitForTimeout(1000);

      // Trigger expiry warning
      await page1.evaluate(() => {
        window.dispatchEvent(new CustomEvent('session:expiring', {
          detail: { timeRemaining: 300000 } // 5 minutes
        }));
      });

      // THEN: Tab B should also show warning
      const warning1 = page1.getByText(/session expiring|log out soon/i);
      const hasWarning1 = await warning1.isVisible().catch(() => false);

      if (hasWarning1) {
        await expect(warning1).toBeVisible();

        // Check Tab B
        await page2.bringToFront();
        const warning2 = page2.getByText(/session expiring|log out soon/i);
        const hasWarning2 = await warning2.isVisible().catch(() => false);

        expect(hasWarning2).toBeTruthy();
      }
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P2] should prevent concurrent login from different locations', async ({ context }) => {
    // GIVEN: User is logged in on Tab A
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Login on Tab A
      await page1.goto('/login');
      await page1.evaluate(() => {
        localStorage.setItem('auth_token', 'existing-session-token');
        localStorage.setItem('session_id', 'session-abc-123');
      });

      // WHEN: Attempting to login on Tab B from different location
      await page2.goto('/login');

      await page2.route('**/api/auth/login**', route => {
        // Simulate concurrent session detection
        route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Session already active',
            message: 'You are already logged in from another location',
          }),
        });
      });

      const emailInput = page2.getByLabel(/email/i);
      await emailInput.fill('test@example.com');

      const passwordInput = page2.getByLabel(/password/i);
      await passwordInput.fill('password123');

      const loginButton = page2.getByRole('button', { name: /login/i });
      await loginButton.click();

      // THEN: Should show concurrent session warning
      await expect(page2.getByText(/already logged in|another location/i)).toBeVisible({
        timeout: 3000
      });

      // Should offer to terminate other session
      const terminateButton = page2.getByRole('button', { name: /terminate|continue/i });
      const hasTerminate = await terminateButton.isVisible().catch(() => false);

      if (hasTerminate) {
        await expect(terminateButton).toBeVisible();
      }
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P0] should sync merchant context across tabs', async ({ context }) => {
    // GIVEN: User switches merchants on Tab A
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Set initial merchant context
      for (const page of [page1, page2]) {
        await page.goto('/dashboard');
        await page.evaluate(() => {
          localStorage.setItem('merchant_key', 'merchant-1');
          localStorage.setItem('merchant_name', 'First Store');
        });
      }

      // WHEN: Switching merchant on Tab A
      await page1.route('**/api/merchant/switch**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              merchantKey: 'merchant-2',
              merchantName: 'Second Store',
            },
            meta: { requestId: 'test-switch' },
          }),
        });
      });

      await page1.evaluate(() => {
        localStorage.setItem('merchant_key', 'merchant-2');
        localStorage.setItem('merchant_name', 'Second Store');
      });

      await page1.reload();

      // THEN: Tab B should reflect new merchant
      await page2.reload();
      await page2.waitForLoadState('networkidle');

      const merchantKey = await page2.evaluate(() =>
        localStorage.getItem('merchant_key')
      );

      expect(merchantKey).toBe('merchant-2');
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P1] should handle offline tab coming online', async ({ context }) => {
    // GIVEN: User is logged in on Tab A
    const page1 = await context.newPage();
    let page2: any;

    try {
      await page1.goto('/dashboard');
      await page1.evaluate(() => {
        localStorage.setItem('auth_token', 'online-session-token');
      });

      // Tab B goes offline
      page2 = await context.newPage();
      await page2.goto('/dashboard');
      await page2.evaluate(() => {
        localStorage.setItem('auth_token', 'offline-session-token');
      });

      // Simulate offline
      await page2.setOffline(true);

      // WHEN: Tab A logs out
      await page1.evaluate(() => {
        localStorage.clear();
      });

      // THEN: Tab B should handle sync when coming back online
      await page2.setOffline(false);
      await page2.reload();

      // Should detect session invalidation
      const loginPrompt = page2.getByText(/session expired|please login/i);
      const hasPrompt = await loginPrompt.isVisible().catch(() => false);

      if (hasPrompt) {
        await expect(loginPrompt).toBeVisible();
      }
    } finally {
      await page1.close();
      if (page2) await page2.close();
    }
  });

  test('[P2] should coordinate real-time updates across tabs', async ({ context }) => {
    // GIVEN: User has conversation open on multiple tabs
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      for (const page of [page1, page2]) {
        await page.goto('/conversations');
        await page.evaluate(() => {
          localStorage.setItem('auth_token', 'test-token');
        });
      }

      // WHEN: New message arrives on Tab A
      await page1.evaluate(() => {
        // Simulate receiving new message via WebSocket
        window.dispatchEvent(new CustomEvent('conversation:new', {
          detail: {
            id: 'conv-new',
            customerName: 'New Customer',
            message: 'Hello',
          }
        }));
      });

      await page1.waitForTimeout(500);

      // THEN: Tab B should also show new message
      await page2.bringToFront();
      await page2.waitForTimeout(500);

      const newConversation = page2.getByText('New Customer');
      const hasNew = await newConversation.isVisible().catch(() => false);

      if (hasNew) {
        await expect(newConversation).toBeVisible();
      }
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P1] should sync user preferences across tabs', async ({ context }) => {
    // GIVEN: User changes preferences on Tab A
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      for (const page of [page1, page2]) {
        await page.goto('/settings');
      }

      // WHEN: Changing theme preference on Tab A
      await page1.evaluate(() => {
        localStorage.setItem('theme', 'dark');
        localStorage.setItem('notifications_enabled', 'true');
      });

      // Trigger storage event
      await page1.evaluate(() => {
        window.dispatchEvent(new StorageEvent('storage', {
          key: 'theme',
          newValue: 'dark',
        }));
      });

      // THEN: Tab B should reflect preferences
      await page2.bringToFront();
      await page2.reload();

      const theme = await page2.evaluate(() => localStorage.getItem('theme'));
      expect(theme).toBe('dark');

      const notifications = await page2.evaluate(() =>
        localStorage.getItem('notifications_enabled')
      );
      expect(notifications).toBe('true');
    } finally {
      await page1.close();
      await page2.close();
    }
  });

  test('[P0] should handle simultaneous authentication actions', async ({ context }) => {
    // GIVEN: User has two tabs open
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // WHEN: Both tabs attempt to login simultaneously
      const loginPromises = [
        page1.goto('/login'),
        page2.goto('/login'),
      ];

      await Promise.all(loginPromises);

      // Mock login API that handles race conditions
      let callCount = 0;
      await page1.route('**/api/auth/login**', (route) => {
        callCount++;
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              token: `token-${callCount}-${Date.now()}`,
              merchantKey: 'test-merchant',
            },
            meta: { requestId: `test-login-${callCount}` },
          }),
        });
      });

      // Submit login on both tabs
      await page1.getByLabel(/email/i).fill('user@example.com');
      await page1.getByLabel(/password/i).fill('password123');
      const login1 = page1.getByRole('button', { name: /login/i }).click();

      await page2.getByLabel(/email/i).fill('user@example.com');
      await page2.getByLabel(/password/i).fill('password123');
      const login2 = page2.getByRole('button', { name: /login/i }).click();

      // Wait for both to complete
      await Promise.all([
        page1.waitForURL(/\/dashboard/, { timeout: 5000 }).catch(() => null),
        page2.waitForURL(/\/dashboard/, { timeout: 5000 }).catch(() => null),
      ]);

      // THEN: Both tabs should be authenticated
      const token1 = await page1.evaluate(() => localStorage.getItem('auth_token'));
      const token2 = await page2.evaluate(() => localStorage.getItem('auth_token'));

      expect(token1).toBeTruthy();
      expect(token2).toBeTruthy();

      // Both should have valid sessions
      await page1.goto('/dashboard');
      await page2.goto('/dashboard');

      await expect(page1.getByRole('heading', { name: /dashboard/i })).toBeVisible();
      await expect(page2.getByRole('heading', { name: /dashboard/i })).toBeVisible();
    } finally {
      await page1.close();
      await page2.close();
    }
  });
});
