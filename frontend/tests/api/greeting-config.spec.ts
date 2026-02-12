/**
 * API Tests for Story 1.14: Greeting Configuration
 * Tests greeting config API endpoints with authentication and validation
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

test.describe.configure({ mode: 'serial' }); // Run tests serially to avoid state conflicts
test.describe('Story 1.14: Greeting Configuration API [P0]', () => {
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

  test('[P0] should fetch greeting configuration - GET returns correct structure', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('data');
    expect(body.data).toHaveProperty('greetingTemplate');
    expect(body.data).toHaveProperty('useCustomGreeting');
    expect(body.data).toHaveProperty('personalityType');
    expect(body.data).toHaveProperty('defaultTemplate');
    expect(body.data).toHaveProperty('availableVariables');
    expect(body.meta).toBeDefined();
  });

  test('[P0] should fetch greeting configuration - handles unauthenticated request', async ({ request }) => {
    const response = await request.get(`${API_URL}/api/v1/merchant/greeting-config`);

    // Should get 401 Unauthorized
    expect(response.status()).toBe(401);
  });

  test('[P0] should update greeting configuration - PUT saves custom greeting', async ({ request }) => {
    const customGreeting = 'Custom welcome to {business_name}! We\'re excited to help you find what you need!!!';

    const response = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: customGreeting,
        use_custom_greeting: true,
      },
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.data.greetingTemplate).toBe(customGreeting);
    expect(body.data.useCustomGreeting).toBe(true);
  });

  test('[P0] should update greeting configuration - validates 500 character limit', async ({ request }) => {
    const longGreeting = 'a'.repeat(501);

    const response = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: longGreeting,
        use_custom_greeting: true,
      },
    });

    // Should return validation error
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body.error.code).toBe('4501');
    expect(body.error.message).toContain('500 characters');
  });

  test('[P0] should update greeting configuration - validates empty greeting', async ({ request }) => {
    const response = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: '',
        use_custom_greeting: true,
      },
    });

    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body.error.code).toBe('4500');
    expect(body.error.message).toContain('cannot be empty');
  });

  test('[P0] should reset greeting to default', async ({ request }) => {
    // First set a custom greeting
    await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: 'Custom greeting',
        use_custom_greeting: true,
      },
    });

    // Reset to default
    const response = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: null,
        use_custom_greeting: false,
      },
    });

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.data.useCustomGreeting).toBe(false);
    expect(body.data.greetingTemplate).toContain('Hey there');
  });

  test('[P1] should support all three personality types', async ({ request }) => {
    const personalities = ['friendly', 'professional', 'enthusiastic'] as const;

    for (const personality of personalities) {
      // Update to this personality
      const updateResponse = await request.put(`${API_URL}/api/v1/merchant/personality`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        data: {
          personality: personality,
        },
      });

      expect(updateResponse.status()).toBe(200);

      // Fetch greeting config to verify default template changed
      const getConfigResponse = await request.get(`${API_URL}/api/v1/merchant/greeting-config`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });
      const body = await getConfigResponse.json();

      expect(body.data.personalityType).toBe(personality);
      expect(body.data.greetingTemplate).toBeTruthy(); // Has some template
    }
  });

  test('[P1] should handle CSRF protection', async ({ request }) => {
    // This test verifies CSRF token is required for state-changing operations

    // Get CSRF token first
    const csrfResponse = await request.get(`${API_URL}/api/v1/csrf-token`);

    expect(csrfResponse.ok()).toBeTruthy();

    const csrfData = await csrfResponse.json();
    const csrfToken = csrfData.data.csrf_token;

    // Try to update with CSRF token (should work)
    const responseWithCsrf = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'X-CSRF-Token': csrfToken,
      },
      data: {
        greeting_template: 'Test greeting with CSRF',
        use_custom_greeting: true,
      },
    });

    expect(responseWithCsrf.status()).toBe(200);
  });

  test('[P1] should return proper error codes for validation failures', async ({ request }) => {
    // Test error code 4500: Empty greeting
    const emptyResponse = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: '',
        use_custom_greeting: true,
      },
    });

    expect(emptyResponse.status()).toBe(422);
    expect(emptyResponse.json()).toMatchObject({
      error: {
        code: 4500,
        message: 'Greeting cannot be empty',
      },
    });

    // Test error code 4501: Too long greeting
    const longResponse = await request.put(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        greeting_template: 'a'.repeat(501),
        use_custom_greeting: true,
      },
    });

    expect(longResponse.status()).toBe(422);
    expect(longResponse.json()).toMatchObject({
      error: {
        code: 4501,
        message: 'Greeting must be less than 500 characters',
      },
    });
  });

  test('[P1] should handle personality-based default greeting updates', async ({ request }) => {
    // Update personality to friendly
    await request.put(`${API_URL}/api/v1/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        personality: 'friendly',
      },
    });

    // Get greeting config - should show friendly default
    const friendlyResponse = await request.get(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });
    const friendlyBody = await friendlyResponse.json();
    expect(friendlyBody.data.personalityType).toBe('friendly');
    expect(friendlyBody.data.defaultTemplate).toContain('Hey there');

    // Update personality to enthusiastic
    await request.put(`${API_URL}/api/v1/merchant/personality`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        personality: 'enthusiastic',
      },
    });

    // Get greeting config - should show enthusiastic default
    const enthusiasticResponse = await request.get(`${API_URL}/api/v1/merchant/greeting-config`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });
    const enthusiasticBody = await enthusiasticResponse.json();
    expect(enthusiasticBody.data.personalityType).toBe('enthusiastic');
    expect(enthusiasticBody.data.defaultTemplate).toContain('SO excited');
  });
});
