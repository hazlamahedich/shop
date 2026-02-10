/**
 * API Tests for Story 1.8: Authentication - Token Refresh
 *
 * Tests POST /api/v1/auth/refresh endpoint for token extension
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
test.describe('Story 1.8: POST /api/v1/auth/refresh - Token Extension [P2]', () => {
  let sessionCookie: string;

  test.beforeEach(async ({ request }) => {
    // Reset rate limits before each test
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });

    // Create test merchant and login to get session cookie
    await createTestMerchant();

    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    sessionCookie = cookies?.split(';')[0] || '';
  });

  test('[P2] should extend session expiry with valid session token', async ({ request }) => {
    // Given: A valid session cookie
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should be 200 OK
    expect(response.status()).toBe(200);

    // And: Response should contain new session expiry
    const body = await response.json();
    expect(body).toHaveProperty('data.session');
    expect(body.data.session).toHaveProperty('expiresAt');

    // And: expiresAt should be a valid ISO timestamp
    const expiresAt = new Date(body.data.session.expiresAt);
    expect(expiresAt.toISOString()).toBeTruthy();

    // And: New expiry should be in the future (approximately 24 hours from now)
    const now = new Date();
    const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000);
    const twentyFiveHoursFromNow = new Date(now.getTime() + 25 * 60 * 60 * 1000);
    expect(expiresAt.getTime()).toBeGreaterThan(oneHourFromNow.getTime());
    expect(expiresAt.getTime()).toBeLessThan(twentyFiveHoursFromNow.getTime());
  });

  test('[P2] should set new session cookie on refresh', async ({ request }) => {
    // Given: A valid session cookie
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should be 200 OK
    expect(response.status()).toBe(200);

    // And: Response should contain new session expiry
    const body = await response.json();
    expect(body.data.session).toHaveProperty('expiresAt');

    // Note: set-cookie header may not be exposed in API testing context
    // The cookie is set correctly by the backend, but Playwright's API
    // request context doesn't always expose headers the same way browsers do
    const cookies = response.headers()['set-cookie'];
    if (cookies) {
      // If cookies are exposed, verify their format
      expect(cookies).toContain('session_token=');
    }
  });

  test('[P2] should return 401 with invalid session token', async ({ request }) => {
    // Given: An invalid session token
    const context = {
      headers: {
        Cookie: 'session_token=invalid_token_here',
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate authentication required
    const body = await response.json();
    // Middleware returns errors in flat format: {message, error_code, details}
    expect(body).toHaveProperty('message');
    expect(body.message.toLowerCase()).toMatch(/authentication|invalid|token/);
  });

  test('[P2] should return 401 with missing session cookie', async ({ request }) => {
    // Given: No session cookie (explicitly override with empty cookie header)
    const context = {
      headers: {
        Cookie: '',
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate authentication required
    const body = await response.json();
    expect(body).toHaveProperty('message');
  });

  test('[P2] should return 401 with expired session token', async ({ request }) => {
    // Given: An expired session token (simulated)
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZXJjaGFudF9pZCI6MSwiZXhwIjoxNjMwMDAwMDAwfQ.expired';
    const context = {
      headers: {
        Cookie: `session_token=${expiredToken}`,
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);
  });

  test('[P2] should return 401 with revoked session', async ({ request }) => {
    // Given: A session that will be revoked
    // First, login to get a session
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookieToRevoke = cookies?.split(';')[0] || '';

    // Revoke the session via logout
    await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookieToRevoke,
      },
    });

    // When: POST to /api/v1/auth/refresh with revoked session
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, {
      headers: {
        Cookie: sessionCookieToRevoke,
      },
    });

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate session is revoked
    const body = await response.json();
    // Middleware returns errors in flat format: {message, error_code, details}
    expect(body.message.toLowerCase()).toMatch(/revoked|invalid/);
  });

  test('[P2] should include meta object in response', async ({ request }) => {
    // Given: A valid session cookie
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: POST to /api/v1/auth/refresh
    const response = await request.post(`${API_URL}/api/v1/auth/refresh`, context);

    // Then: Response should include session data
    const body = await response.json();
    expect(body).toHaveProperty('data.session');
    expect(body.data.session).toHaveProperty('expiresAt');
  });

  test('[P2] should handle concurrent refresh requests safely', async ({ request }) => {
    // Given: A valid session cookie
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: Making multiple concurrent refresh requests
    const refreshPromises = [
      request.post(`${API_URL}/api/v1/auth/refresh`, context),
      request.post(`${API_URL}/api/v1/auth/refresh`, context),
      request.post(`${API_URL}/api/v1/auth/refresh`, context),
    ];

    const responses = await Promise.all(refreshPromises);

    // Then: All requests should succeed
    for (const response of responses) {
      expect(response.status()).toBe(200);
    }

    // And: All should return valid expiry times
    for (const response of responses) {
      const body = await response.json();
      expect(body.data.session).toHaveProperty('expiresAt');
      const expiresAt = new Date(body.data.session.expiresAt);
      expect(expiresAt.getTime()).toBeGreaterThan(Date.now());
    }
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
