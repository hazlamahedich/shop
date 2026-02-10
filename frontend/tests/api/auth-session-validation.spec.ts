/**
 * API Tests for Story 1.8: Authentication - Session Validation
 *
 * Tests GET /api/v1/auth/me endpoint for session validation
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
test.describe('Story 1.8: GET /api/v1/auth/me - Session Validation [P1]', () => {
  test.beforeAll(async ({ request }) => {
    // Create test merchant account
    await createTestMerchant();
  });

  // Helper function to create a session (used by most tests)
  async function createSession(request: any): Promise<string> {
    // Reset rate limits before each test
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });

    // Login to get fresh session cookie
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    return cookies?.split(';')[0] || '';
  }

  test('[P1] should return merchant data with valid session', async ({ request }) => {
    // Given: A valid session cookie
    const sessionCookie = await createSession(request);
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: GET /api/v1/auth/me with valid session
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Response should be 200 OK
    expect(response.status()).toBe(200);

    // And: Response should contain merchant data
    const body = await response.json();
    expect(body.data).toHaveProperty('merchant');

    // And: Merchant should have required fields
    expect(body.data.merchant).toHaveProperty('id');
    expect(body.data.merchant).toHaveProperty('email');
    expect(body.data.merchant).toHaveProperty('merchant_key');

    // And: Email should match test merchant
    expect(body.data.merchant.email).toBe(TEST_MERCHANT.email);
  });

  test('[P1] should return 401 with missing session cookie', async ({ request }) => {
    // Given: No session cookie

    // When: GET /api/v1/auth/me without cookie
    const response = await request.get(`${API_URL}/api/v1/auth/me`);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate authentication required
    const body = await response.json();
    expect(body).toHaveProperty('message');
    expect(body.message.toLowerCase()).toContain('authentication');
  });

  test('[P1] should return 401 with invalid session token', async ({ request }) => {
    // Given: An invalid session token
    const context = {
      headers: {
        Cookie: 'session_token=invalid_token_here',
      },
    };

    // When: GET /api/v1/auth/me with invalid token
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate invalid token
    const body = await response.json();
    expect(body).toHaveProperty('message');
  });

  test('[P1] should return 401 with expired session token', async ({ request }) => {
    // Given: An expired session token (simulated with malformed JWT)
    const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJtZXJjaGFudF9pZCI6MSwiZXhwIjoxNjMwMDAwMDAwfQ.expired';
    const context = {
      headers: {
        Cookie: `session_token=${expiredToken}`,
      },
    };

    // When: GET /api/v1/auth/me with expired token
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate token expired or invalid
    const body = await response.json();
    expect(body).toHaveProperty('message');
  });

  test('[P1] should return 401 with revoked session', async ({ request }) => {
    // Given: A session that has been revoked via logout
    // First, login to get a session
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: TEST_MERCHANT.email,
        password: TEST_MERCHANT.password,
      },
    });

    const cookies = loginResponse.headers()['set-cookie'];
    const sessionCookie = cookies?.split(';')[0] || '';

    // Then, logout to revoke the session
    await request.post(`${API_URL}/api/v1/auth/logout`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // When: GET /api/v1/auth/me with revoked session
    const response = await request.get(`${API_URL}/api/v1/auth/me`, {
      headers: {
        Cookie: sessionCookie,
      },
    });

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Error should indicate session is revoked
    const body = await response.json();
    expect(body).toHaveProperty('message');
    expect(body.message.toLowerCase()).toMatch(/revoked|invalid/);
  });

  test('[P1] should return 401 when session cookie format is invalid', async ({ request }) => {
    // Given: A malformed session cookie
    const context = {
      headers: {
        Cookie: 'session_token=not-a-valid-jwt',
      },
    };

    // When: GET /api/v1/auth/me with malformed cookie
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);
  });

  test('[P1] should return merchant data with correct types', async ({ request }) => {
    // Given: A valid session cookie
    const sessionCookie = await createSession(request);
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: GET /api/v1/auth/me
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Merchant data should have correct types
    const body = await response.json();
    expect(typeof body.data.merchant.id).toBe('number');
    expect(typeof body.data.merchant.email).toBe('string');
    expect(typeof body.data.merchant.merchant_key).toBe('string');
  });

  test('[P2] should validate email format', async ({ request }) => {
    // Given: A valid session cookie
    const sessionCookie = await createSession(request);
    const context = {
      headers: {
        Cookie: sessionCookie,
      },
    };

    // When: GET /api/v1/auth/me
    const response = await request.get(`${API_URL}/api/v1/auth/me`, context);

    // Then: Email should be valid format
    const body = await response.json();
    expect(body.data.merchant.email).toMatch(/^[^\s@]+@[^\s@]+\.[^\s@]+$/);
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
