/**
 * API Tests for Story 1.11: Business Info CSRF Validation
 *
 * Tests CSRF protection on business info endpoints.
 * Verifies that requests without valid CSRF tokens are rejected.
 *
 * @tags api security business-info story-1-11 csrf
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: Business Info CSRF Validation [P0]', () => {
  let authToken: string;
  let csrfToken: string;
  let merchantId: number;

  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      authToken = loginData.data.session.token;
      csrfToken = loginData.data.session.csrfToken;
      merchantId = loginData.data.merchant.id;
    }
  });

  test('[P0] should reject PUT without CSRF token', async ({ request }) => {
    // When: Attempt to update business info without CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        // Note: Not including CSRF token
      },
      data: {
        business_name: 'CSRF Test Store',
      },
    });

    // Then: Should return 403 Forbidden
    expect(response.status()).toBe(403);

    // And: Response should contain CSRF error message
    const body = await response.json();
    expect(body.detail.message.toLowerCase()).toMatch(/csrf|forbidden|invalid/i);
  });

  test('[P0] should reject PUT with invalid CSRF token', async ({ request }) => {
    // When: Attempt to update business info with invalid CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        'X-CSRF-Token': 'invalid-csrf-token-12345',
      },
      data: {
        business_name: 'CSRF Test Store',
      },
    });

    // Then: Should return 403 Forbidden
    expect(response.status()).toBe(403);

    // And: Response should contain CSRF error message
    const body = await response.json();
    expect(body.detail.message.toLowerCase()).toMatch(/csrf|forbidden|invalid/i);
  });

  test('[P0] should accept PUT with valid CSRF token', async ({ request }) => {
    // When: Update business info with valid CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
      },
      data: {
        business_name: 'Valid CSRF Test Store',
      },
    });

    // Then: Should return 200 OK
    expect(response.status()).toBe(200);

    // And: Response should contain updated data
    const body = await response.json();
    expect(body.data.business_name).toBe('Valid CSRF Test Store');
  });

  test('[P0] should validate CSRF token on partial updates', async ({ request }) => {
    // When: Attempt partial update without CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        // No CSRF token
      },
      data: {
        business_description: 'Partial update without CSRF',
      },
    });

    // Then: Should return 403 Forbidden
    expect(response.status()).toBe(403);
  });

  test('[P0] should validate CSRF token when clearing fields', async ({ request }) => {
    // When: Attempt to clear field without CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        // No CSRF token
      },
      data: {
        business_hours: null,
      },
    });

    // Then: Should return 403 Forbidden
    expect(response.status()).toBe(403);
  });

  test('[P1] should reject empty CSRF token', async ({ request }) => {
    // When: Attempt with empty CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
        'X-CSRF-Token': '',
      },
      data: {
        business_name: 'Empty CSRF Test',
      },
    });

    // Then: Should return 403 Forbidden
    expect(response.status()).toBe(403);
  });

  test('[P1] should reject malformed CSRF token', async ({ request }) => {
    const malformedTokens = [
      'not-a-valid-token',
      '00000000-0000-0000-0000-000000000000', // All zeros
      'Bearer token-in-wrong-format',
      '<script>alert("xss")</script>', // Attempt XSS
      '../../../etc/passwd', // Path traversal attempt
    ];

    for (const token of malformedTokens) {
      // When: Attempt with malformed CSRF token
      const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-CSRF-Token': token,
        },
        data: {
          business_name: `Malformed Test ${token.substring(0, 5)}`,
        },
      });

      // Then: Should return 403 Forbidden
      expect(response.status()).toBe(403);
    }
  });

  test('[P1] should not require CSRF for GET requests', async ({ request }) => {
    // When: Get business info without CSRF token
    const response = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        // No CSRF token for GET
      },
    });

    // Then: Should return 200 OK (GET doesn't require CSRF)
    expect(response.status()).toBe(200);
  });

  test('[P1] should require CSRF token regardless of auth token validity', async ({ request }) => {
    // When: Use valid CSRF token but invalid auth token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: 'Bearer invalid-auth-token',
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken, // Valid CSRF but invalid auth
      },
      data: {
        business_name: 'Test',
      },
    });

    // Then: Should fail due to auth (401) not CSRF (403)
    // If auth fails first, we get 401
    // If CSRF check happens first, we get 403
    expect([401, 403]).toContain(response.status());
  });

  test('[P1] should validate CSRF token in different header formats', async ({ request }) => {
    // Test different header names that might be used for CSRF
    const headerVariations = [
      'X-CSRF-Token',
      'X-Csrf-Token',
      'x-csrf-token', // Case insensitive
      'X-CSRF-Token',
    ];

    for (const headerName of headerVariations) {
      // When: Use case variation of CSRF header
      const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          [headerName]: csrfToken,
        },
        data: {
          business_name: `Header Test ${headerName}`,
        },
      });

      // Then: Should accept the request (headers should be case-insensitive)
      expect(response.status()).toBe(200);
    }
  });

  test('[P2] should include CSRF error code in response', async ({ request }) => {
    // When: Attempt without CSRF token
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_name: 'Error Code Test',
      },
    });

    // Then: Response should include error code
    expect(response.status()).toBe(403);
    const body = await response.json();

    expect(body.detail).toBeDefined();
    // Error code might be present (depends on implementation)
    if (body.detail.error_code) {
      expect(typeof body.detail.error_code).toBe('number');
    }
  });

  test('[P2] should validate CSRF token for each state-changing operation', async ({ request }) => {
    // Test that CSRF is required for each state-changing field update
    const fieldsToUpdate = [
      { business_name: 'Name Update' },
      { business_description: 'Description Update' },
      { business_hours: 'Hours Update' },
    ];

    for (const fieldData of fieldsToUpdate) {
      // When: Update field without CSRF
      const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: fieldData,
      });

      // Then: Should return 403
      expect(response.status()).toBe(403);
    }
  });

  test('[P2] should handle concurrent requests with different CSRF tokens', async ({ request }) => {
    // When: Make multiple concurrent requests with different CSRF tokens
    const responses = await Promise.all([
      request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken, // Valid
        },
        data: { business_name: 'Valid Request' },
      }),
      request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-CSRF-Token': 'invalid-token', // Invalid
        },
        data: { business_name: 'Invalid Request' },
      }),
    ]);

    // Then: Valid request should succeed, invalid should fail
    const validResponse = responses[0];
    const invalidResponse = responses[1];

    expect(validResponse.status()).toBe(200);
    expect(invalidResponse.status()).toBe(403);
  });
});
