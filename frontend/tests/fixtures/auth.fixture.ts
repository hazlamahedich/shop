/**
 * Authentication Fixture
 *
 * Provides mock authentication context for E2E tests.
 * Since we're mocking OAuth flows, this fixture simulates
 * authenticated state without real external service calls.
 */

import { test as base } from '@playwright/test';

type AuthState = {
  isAuthenticated: boolean;
  userId: string | null;
  merchantKey: string | null;
  token: string | null;
};

type AuthFixtures = {
  authenticatedPage: typeof base['page'];
  authState: AuthState;
  mockAuth: (merchantKey?: string) => Promise<void>;
  clearAuth: () => Promise<void>;
};

export const authFixture = base.extend<AuthFixtures>({
  /**
   * Auth state fixture - initializes as unauthenticated
   */
  authState: async ({ page }, use) => {
    const state: AuthState = {
      isAuthenticated: false,
      userId: null,
      merchantKey: null,
      token: null,
    };
    await use(state);
  },

  /**
   * Mock authentication helper
   * Simulates OAuth login by setting localStorage state
   */
  mockAuth: async ({ page, authState }, use) => {
    const mockAuthentication = async (merchantKey: string = 'test-merchant-123') => {
      // Simulate authenticated state via localStorage
      await page.evaluate((key) => {
        localStorage.setItem('auth_token', 'mock-jwt-token');
        localStorage.setItem('merchant_key', key);
        localStorage.setItem('user_id', 'mock-user-123');
        localStorage.setItem('auth_timestamp', Date.now().toString());
      }, merchantKey);

      // Update auth state
      authState.isAuthenticated = true;
      authState.userId = 'mock-user-123';
      authState.merchantKey = merchantKey;
      authState.token = 'mock-jwt-token';

      // Reload page to apply auth state
      await page.reload();
    };

    await use(mockAuthentication);
  },

  /**
   * Clear authentication helper
   * Removes auth state from localStorage
   */
  clearAuth: async ({ page, authState }, use) => {
    const clearAuthentication = async () => {
      await page.evaluate(() => {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('merchant_key');
        localStorage.removeItem('user_id');
        localStorage.removeItem('auth_timestamp');
        sessionStorage.clear();
      });

      // Reset auth state
      authState.isAuthenticated = false;
      authState.userId = null;
      authState.merchantKey = null;
      authState.token = null;

      await page.reload();
    };

    await use(clearAuthentication);
  },

  /**
   * Authenticated page fixture
   * A page that starts with mock authentication
   */
  authenticatedPage: async ({ page, mockAuth }, use) => {
    await mockAuth();
    await use(page);
  },
});
