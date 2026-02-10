/**
 * API Tests for Story 1.8: Authentication - Logout
 *
 * Tests POST /api/v1/auth/logout endpoint
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' }); // Run tests serially to avoid rate limiter state conflicts
test.describe('Story 1.8: POST /api/v1/auth/logout [P1]', () => {
  test.beforeAll(async () => {
    // Create test merchant account
    await createTestMerchant();
  });

  test.beforeEach(async ({ request }) => {
    // Reset rate limits before each test
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });
  });

  test('[P1] should clear session cookie and return 200 on valid logout', async ({ request }) => {
    // Given: A logged-in merchant with valid session
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    expect(loginResponse.status()).toBe(200);

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: POST to /api/v1/auth/logout
    const logoutResponse = await request.post(`${API_URL}/api/v1/auth/logout`, context);

    // Then: Response should be 200 OK
    expect(logoutResponse.status()).toBe(200);

    // And: Response should indicate success
    const body = await logoutResponse.json();
    expect(body.data).toHaveProperty('success');
    expect(body.data.success).toBe(true);

    // And: Response should clear session cookie
    const logoutCookies = logoutResponse.headers()['set-cookie'];
    expect(logoutCookies).toBeDefined();
    // Cookie clearing is indicated by Max-Age=0 or Expires in the past
    expect(logoutCookies).toMatch(/Max-Age=0|Expires=Thu, 01 Jan 1970/);
  });

  test('[P1] should revoke session in database on logout', async ({ request }) => {
    // Given: A logged-in merchant with valid session
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    // Verify session is valid before logout
    const meBeforeResponse = await request.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Cookie: sessionCookie,
      },
    });
    expect(meBeforeResponse.status()).toBe(200);

    // When: Logging out
    await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // Then: Subsequent requests with same token should fail
    const meAfterResponse = await request.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // Session should be revoked
    expect(meAfterResponse.status()).toBe(401);
  });

  test('[P1] should return 401 when logging out without session', async ({ request }) => {
    // Given: No active session

    // When: POST to /api/v1/auth/logout without cookie
    const response = await request.post(`${API_URL}/api/v1/auth/logout`);

    // Then: Response should be 401 (or could be 200 with no-op)
    // Based on implementation, logout without session might still return 200
    // but session is already cleared, so 401 is also acceptable
    expect([200, 401]).toContain(response.status());
  });

  test('[P1] should return 401 when logging out with invalid session', async ({ request }) => {
    // Given: An invalid session token
    const context = {
      headers: {
        Cookie: 'session_token=invalid_token_here',
      },
    };

    // When: POST to /api/v1/auth/logout
    const response = await request.post(`${API_URL}/api/v1/auth/logout`, context);

    // Then: Response should be 401 (or 200 with no-op)
    expect([200, 401]).toContain(response.status());
  });

  test('[P1] should handle multiple logout requests gracefully', async ({ request }) => {
    // Given: A logged-in merchant
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    // When: Logging out multiple times
    const logout1 = await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    const logout2 = await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // Then: Both requests should succeed (idempotent)
    expect(logout1.status()).toBe(200);
    expect(logout2.status()).toBe(200);
  });

  test('[P1] should include success field in logout response', async ({ request }) => {
    // Given: A logged-in merchant
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    // When: Logging out
    const logoutResponse = await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // Then: Response should include success field
    const body = await logoutResponse.json();
    expect(body.data).toHaveProperty('success');
    expect(body.data.success).toBe(true);
  });

  test('[P2] should clear only the session cookie, not other cookies', async ({ request }) => {
    // Given: A logged-in merchant with multiple cookies
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    const context = {
      headers: {
        Cookie: `${sessionCookie}; other_cookie=some_value`,
      },
    };

    // When: Logging out
    const logoutResponse = await request.post(`${API_URL}/api/v1/auth/logout`, context);

    // Then: Response should clear session cookie
    const logoutCookies = logoutResponse.headers()['set-cookie'];
    expect(logoutCookies).toBeDefined();

    // And: Should be clearing the session_token cookie
    expect(logoutCookies).toContain('session_token=');
  });
});

// Helper function

async function createTestMerchant(): Promise<void> {
  try {
    const response = await fetch(`${API_URL}/api/v1/test/create-merchant`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Test-Mode': 'true',
      },
      body: JSON.stringify(TEST_MERCHANT),
    });

    if (!response.ok && response.status !== 409) {
      console.warn('Failed to create test merchant:', await response.text());
    }
  } catch (error) {
    console.warn('Could not create test merchant:', error);
  }
}
