/**
 * API Tests for Story 1.11: Business Info Partial Updates
 *
 * Tests partial update behavior for business information endpoints.
 * Verifies that only provided fields are updated while others remain unchanged.
 *
 * @tags api integration business-info story-1-11 partial-update
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

// Test data
const INITIAL_BUSINESS_INFO = {
  business_name: 'Initial Test Store',
  business_description: 'Initial test description for partial updates',
  business_hours: '9 AM - 5 PM PST',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: Business Info Partial Updates [P0]', () => {
  let authToken: string;
  let merchantId: number;

  test.beforeAll(async ({ request }) => {
    // Login to get auth token
    const loginResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      authToken = loginData.data.session.token;
      merchantId = loginData.data.merchant.id;

      // Set initial business info state
      await request.put(`${API_URL}/api/v1/merchant/business-info`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: INITIAL_BUSINESS_INFO,
      });
    }
  });

  test.beforeEach(async ({ request }) => {
    // Reset to initial state before each test
    await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: INITIAL_BUSINESS_INFO,
    });
  });

  test('[P0] should update only business_name field, leaving other fields unchanged', async ({ request }) => {
    // Given: Initial business info with all fields set
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);
    const beforeData = await getBefore.json();

    // When: Update only business_name
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_name: 'Updated Store Name Only',
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: business_name should be updated
    expect(body.data.business_name).toBe('Updated Store Name Only');

    // And: Other fields should remain unchanged
    expect(body.data.business_description).toBe(INITIAL_BUSINESS_INFO.business_description);
    expect(body.data.business_hours).toBe(INITIAL_BUSINESS_INFO.business_hours);

    // Verify with GET request
    const verifyResponse = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const verifyData = await verifyResponse.json();

    expect(verifyData.data.business_name).toBe('Updated Store Name Only');
    expect(verifyData.data.business_description).toBe(INITIAL_BUSINESS_INFO.business_description);
    expect(verifyData.data.business_hours).toBe(INITIAL_BUSINESS_INFO.business_hours);
  });

  test('[P0] should update only business_description field, leaving other fields unchanged', async ({ request }) => {
    // Given: Initial business info with all fields set
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);

    // When: Update only business_description
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_description: 'Updated description only - partial update test',
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: business_description should be updated
    expect(body.data.business_description).toBe('Updated description only - partial update test');

    // And: Other fields should remain unchanged
    expect(body.data.business_name).toBe(INITIAL_BUSINESS_INFO.business_name);
    expect(body.data.business_hours).toBe(INITIAL_BUSINESS_INFO.business_hours);

    // Verify with GET request
    const verifyResponse = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const verifyData = await verifyResponse.json();

    expect(verifyData.data.business_name).toBe(INITIAL_BUSINESS_INFO.business_name);
    expect(verifyData.data.business_description).toBe('Updated description only - partial update test');
    expect(verifyData.data.business_hours).toBe(INITIAL_BUSINESS_INFO.business_hours);
  });

  test('[P0] should update only business_hours field, leaving other fields unchanged', async ({ request }) => {
    // Given: Initial business info with all fields set
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);

    // When: Update only business_hours
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_hours: '24/7 Open - Updated hours only',
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: business_hours should be updated
    expect(body.data.business_hours).toBe('24/7 Open - Updated hours only');

    // And: Other fields should remain unchanged
    expect(body.data.business_name).toBe(INITIAL_BUSINESS_INFO.business_name);
    expect(body.data.business_description).toBe(INITIAL_BUSINESS_INFO.business_description);

    // Verify with GET request
    const verifyResponse = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const verifyData = await verifyResponse.json();

    expect(verifyData.data.business_name).toBe(INITIAL_BUSINESS_INFO.business_name);
    expect(verifyData.data.business_description).toBe(INITIAL_BUSINESS_INFO.business_description);
    expect(verifyData.data.business_hours).toBe('24/7 Open - Updated hours only');
  });

  test('[P0] should support clearing a field with null value', async ({ request }) => {
    // Given: Business info with all fields set
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);
    const beforeData = await getBefore.json();
    expect(beforeData.data.business_description).not.toBeNull();

    // When: Clear business_description with null
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_description: null,
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: business_description should be null
    expect(body.data.business_description).toBeNull();

    // And: Other fields should remain unchanged
    expect(body.data.business_name).toBe(INITIAL_BUSINESS_INFO.business_name);
    expect(body.data.business_hours).toBe(INITIAL_BUSINESS_INFO.business_hours);
  });

  test('[P0] should support updating multiple fields simultaneously', async ({ request }) => {
    // Given: Initial business info
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);

    // When: Update multiple fields at once
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_name: 'Multi-field Update Store',
        business_hours: '8 AM - 8 PM EST',
      },
    });

    // Then: Response should be successful
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: Updated fields should have new values
    expect(body.data.business_name).toBe('Multi-field Update Store');
    expect(body.data.business_hours).toBe('8 AM - 8 PM EST');

    // And: Non-updated field should remain unchanged
    expect(body.data.business_description).toBe(INITIAL_BUSINESS_INFO.business_description);
  });

  test('[P1] should handle empty update body gracefully', async ({ request }) => {
    // Given: Initial business info
    const getBefore = await request.get(`${API_URL}/api/v1/merchant/business-info`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    expect(getBefore.ok()).toBe(true);
    const beforeData = await getBefore.json();

    // When: Send empty update body
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {},
    });

    // Then: Response should be successful (no-op)
    expect(response.status()).toBe(200);
    const body = await response.json();

    // And: All fields should remain unchanged
    expect(body.data.business_name).toBe(beforeData.data.business_name);
    expect(body.data.business_description).toBe(beforeData.data.business_description);
    expect(body.data.business_hours).toBe(beforeData.data.business_hours);
  });

  test('[P1] should preserve data types during partial updates', async ({ request }) => {
    // Given: Business info with specific values
    await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_name: 'Type Test Store',
        business_description: null,
        business_hours: null,
      },
    });

    // When: Update null field to string value
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_description: 'Now has a value',
      },
    });

    // Then: Response should contain correct types
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(typeof body.data.business_name).toBe('string');
    expect(typeof body.data.business_description).toBe('string');
    expect(body.data.business_hours).toBeNull();
  });

  test('[P1] should include metadata in partial update response', async ({ request }) => {
    // When: Perform partial update
    const response = await request.put(`${API_URL}/api/v1/merchant/business-info`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        business_name: 'Metadata Test Store',
      },
    });

    // Then: Response should include metadata
    expect(response.status()).toBe(200);
    const body = await response.json();

    expect(body).toHaveProperty('meta');
    expect(body.meta).toHaveProperty('request_id');
    expect(body.meta).toHaveProperty('timestamp');
    expect(typeof body.meta.request_id).toBe('string');
    expect(typeof body.meta.timestamp).toBe('string');
  });
});
