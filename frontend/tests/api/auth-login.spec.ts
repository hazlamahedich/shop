/**
 * API Tests for Story 1.8: Authentication - Login Endpoint
 *
 * Tests POST /api/v1/auth/login endpoint contract validation
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test merchant credentials
const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' }); // Run tests serially to avoid rate limiter state conflicts
test.describe('Story 1.8: POST /api/v1/auth/login - Contract Validation [P1]', () => {
  test.beforeAll(async () => {
    // Create test merchant account via API
    await createTestMerchant();
  });

  test.beforeEach(async ({ request }) => {
    // Reset rate limits before each test to ensure clean state
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });
  });

  test('[P1] should return 200 with merchant data and session info on valid credentials', async ({ request }) => {
    // Given: Valid merchant credentials
    const loginData = {
      email: TEST_MERCHANT.email,
      password: TEST_MERCHANT.password,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should be 200 OK
    expect(response.status()).toBe(200);

    // And: Response body should contain MinimalEnvelope wrapper
    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body).toHaveProperty('meta');

    // And: Data should contain merchant and session
    expect(body.data).toHaveProperty('merchant');
    expect(body.data).toHaveProperty('session');

    // And: Merchant data should include required fields
    expect(body.data.merchant).toHaveProperty('id');
    expect(body.data.merchant).toHaveProperty('email');
    expect(body.data.merchant).toHaveProperty('merchant_key');

    // And: Session data should include expiry time
    expect(body.data.session).toHaveProperty('expiresAt');
    expect(body.data.session).toHaveProperty('expiresAt');
  });

  test('[P1] should return 401 with error message on invalid email', async ({ request }) => {
    // Given: Invalid email (wrong email)
    const loginData = {
      email: 'wrong@example.com',
      password: TEST_MERCHANT.password,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Response should contain error details
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(body.detail).toHaveProperty('message');
    expect(body.detail.message.toLowerCase()).toContain('invalid');
  });

  test('[P1] should return 401 with error message on invalid password', async ({ request }) => {
    // Given: Invalid password (wrong password)
    const loginData = {
      email: TEST_MERCHANT.email,
      password: 'WrongPassword123',
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should be 401 Unauthorized
    expect(response.status()).toBe(401);

    // And: Response should contain error details
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(body.detail).toHaveProperty('message');
    expect(body.detail.message.toLowerCase()).toContain('invalid');
  });

  test('[P1] should return 422 validation error when email field is missing', async ({ request }) => {
    // Given: Login data missing email field
    const loginData = {
      password: TEST_MERCHANT.password,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should be 422 Unprocessable Entity (FastAPI validation)
    expect(response.status()).toBe(422);

    // And: Response should contain validation error
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(Array.isArray(body.detail)).toBe(true);
  });

  test('[P1] should return 422 validation error when password field is missing', async ({ request }) => {
    // Given: Login data missing password field
    const loginData = {
      email: TEST_MERCHANT.email,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should be 422 Unprocessable Entity (FastAPI validation)
    expect(response.status()).toBe(422);

    // And: Response should contain validation error
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(Array.isArray(body.detail)).toBe(true);
  });

  test('[P1] should set session cookie with correct flags on successful login', async ({ request }) => {
    // Given: Valid merchant credentials
    const loginData = {
      email: TEST_MERCHANT.email,
      password: TEST_MERCHANT.password,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should include session cookie
    const cookies = response.headers()['set-cookie'];
    expect(cookies).toBeDefined();

    // And: Cookie should have httpOnly flag
    expect(cookies).toContain('HttpOnly');

    // And: Cookie should have Secure flag (in production)
    // And: Cookie should have SameSite=strict (or SameSite=Strict)
    expect(cookies.toLowerCase()).toContain('samesite=strict');
  });

  test('[P1] should return 429 after 5 failed login attempts from same IP', async ({ request }) => {
    // Reset rate limits at start of test to ensure clean state
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });

    // Given: An IP address with 5 failed login attempts
    const testIp = '192.168.1.200'; // Use explicit IP for consistent tracking (different from rate-limiting tests)
    for (let i = 0; i < 5; i++) {
      await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: `wrong-${i}@example.com`,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false', // Enable rate limiting
          'X-Forwarded-For': testIp, // Explicit IP for consistent tracking
        },
      });
    }

    // When: Making 6th login attempt from same IP
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'another-wrong@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false', // Enable rate limiting
        'X-Forwarded-For': testIp, // Same IP
      },
    });

    // Then: Response should be 429 Too Many Requests
    expect(response.status()).toBe(429);

    // And: Response should contain rate limit error details
    const body = await response.json();
    expect(body).toHaveProperty('detail');
    expect(body.detail.message.toLowerCase()).toContain('too many');

    // Clean up: Reset rate limits for subsequent tests
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    });
  });

  test('[P1] should return ISO-8601 formatted expiresAt timestamp', async ({ request }) => {
    // Given: Valid merchant credentials
    const loginData = {
      email: TEST_MERCHANT.email,
      password: TEST_MERCHANT.password,
    };

    // When: POST to login endpoint
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: loginData,
    });

    // Then: Response should include valid ISO-8601 timestamp
    const body = await response.json();
    expect(body.data.session).toHaveProperty('expiresAt');

    // And: Timestamp should be valid ISO 8601 format
    const expiresAt = new Date(body.data.session.expiresAt);
    expect(expiresAt.toISOString()).toBeTruthy();
    expect(expiresAt.getTime()).toBeGreaterThan(Date.now());
  });
});

// Helper function

async function createTestMerchant(): Promise<void> {
  // Create test merchant via API
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
      // 409 means already exists, which is fine
      console.warn('Failed to create test merchant:', await response.text());
    }
  } catch (error) {
    console.warn('Could not create test merchant:', error);
  }
}
