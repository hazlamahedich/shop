/**
 * API Tests for Story 1.10: Bot Personality Configuration
 *
 * Tests personality configuration API endpoints contract validation
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

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.10: Bot Personality Configuration API [P0]', () => {
  let authToken: string;

  test.beforeAll(async () => {
    // Create test merchant account via API
    await createTestMerchant();

    // Login to get auth token
    const loginResponse = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(TEST_MERCHANT),
    });

    if (loginResponse.ok) {
      const loginData = await loginResponse.json();
      authToken = loginData.data.session.token;
    }
  });

  test('[P0] should retrieve current personality config', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
      },
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('personality');
    expect(body.data).toHaveProperty('custom_greeting');
  });

  test('[P0] should update personality to Friendly', async ({ request }) => {
    // Get CSRF Token first
    const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`);
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.csrf_token;

    const updateResponse = await request.patch(`${API_URL}/api/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      data: {
        personality: 'friendly',
        custom_greeting: 'Hello from friendly bot!',
      },
    });

    expect(updateResponse.status()).toBe(200);

    const body = await updateResponse.json();
    expect(body.data.personality).toBe('friendly');
  });

  test('[P1] should validate invalid personality type', async ({ request }) => {
    // Get CSRF Token first
    const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`);
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.csrf_token;

    const response = await request.patch(`${API_URL}/api/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      data: {
        personality: 'invalid_type',
      },
    });

    expect(response.status()).toBe(422);
  });

  test('[P1] should enforce character limit on greeting', async ({ request }) => {
    // Get CSRF Token first
    const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`);
    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.csrf_token;

    const longGreeting = 'a'.repeat(501);
    const response = await request.patch(`${API_URL}/api/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-Merchant-Id': '1',
        'X-CSRF-Token': csrfToken,
      },
      data: {
        personality: 'friendly',
        custom_greeting: longGreeting,
      },
    });

    expect(response.status()).toBe(422);
  });

  test('[P1] should support all three personality types', async ({ request }) => {
    const personalities = ['friendly', 'professional', 'enthusiastic'] as const;

    for (const personality of personalities) {
      // Get CSRF Token for each request
      const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`);
      const csrfData = await csrfResponse.json();
      const csrfToken = csrfData.csrf_token;

      const response = await request.patch(`${API_URL}/api/merchant/personality`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Merchant-Id': '1',
          'X-CSRF-Token': csrfToken,
        },
        data: {
          personality,
        },
      });

      expect(response.status()).toBe(200);

      const body = await response.json();
      expect(body.data.personality).toBe(personality);
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
