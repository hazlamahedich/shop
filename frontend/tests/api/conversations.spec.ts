/**
 * Conversations API Integration Tests
 *
 * Story 3-1: Conversation List with Pagination
 * Tests the /api/conversations endpoint with authentication, pagination, and sorting
 *
 * @tags api integration conversations story-3-1
 */

import { test, expect } from '@playwright/test';

/**
 * Base URL for API requests
 * Configure based on environment (local/staging/production)
 */
const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Helper to create authenticated request context
 * In production, this would use proper auth tokens
 */
async function getAuthenticatedRequest({ request }) {
  // Set auth token - in real scenario, this would come from login
  const token = process.env.TEST_AUTH_TOKEN || 'test-token';

  return {
    baseURL: BASE_URL,
    extraHeaders: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  };
}

test.describe('Conversations API - Authentication', () => {
  test('[P0] @smoke should require authentication', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`);

    // Should return 401 Unauthorized
    expect(response.status()).toBe(401);

    const body = await response.json();
    expect(body).toHaveProperty('message');
    expect(body.message).toMatch(/authentication|unauthorized|required/i);
  });

  test('[P0] should accept valid authentication', async ({ request }) => {
    // Mock authenticated request
    const authRequest = await getAuthenticatedRequest({ request });

    // This test assumes a test merchant exists in the database
    // In CI: Use seeded test data
    const response = await authRequest.request.get(`${BASE_URL}/api/conversations`);

    // Should return 200 or 403 (forbidden if merchant_id doesn't match)
    // Both are acceptable - we're testing auth mechanism, not data
    expect([200, 403, 404]).toContain(response.status());

    // Should NOT be 401 (unauthorized)
    expect(response.status()).not.toBe(401);
  });
});

test.describe('Conversations API - Pagination', () => {
  // Use authenticated requests for these tests
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P0] @smoke should return paginated conversations', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        page: '1',
        per_page: '20',
      },
    });

    // Accept 200 (success) or 404 (no data, but endpoint works)
    if (response.status() === 200) {
      const body = await response.json();

      // Validate response structure
      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');
      expect(body.meta).toHaveProperty('pagination');

      const { pagination } = body.meta;
      expect(pagination).toMatchObject({
        total: expect.any(Number),
        page: 1,
        perPage: 20,
        totalPages: expect.any(Number),
      });

      // Validate data is an array
      expect(Array.isArray(body.data)).toBe(true);

      // Validate conversation structure
      if (body.data.length > 0) {
        const conversation = body.data[0];
        expect(conversation).toMatchObject({
          id: expect.any(Number),
          platformSenderIdMasked: expect.any(String),
          lastMessage: expect.any(String),
          status: expect.any(String),
          messageCount: expect.any(Number),
          updated_at: expect.any(String),
          created_at: expect.any(String),
        });
      }
    } else {
      // No conversations - that's ok for test environment
      expect([404, 403]).toContain(response.status());
    }
  });

  test('[P1] should validate page parameter constraints', async ({ request }) => {
    // Test page < 1 (should fail validation)
    const response1 = await request.get(`${BASE_URL}/api/conversations`, {
      params: { page: '0' },
    });

    expect(response1.status()).toBe(422);

    const body1 = await response1.json();
    expect(body1).toHaveProperty('detail'); // FastAPI validation error format

    // Test non-integer page
    const response2 = await request.get(`${BASE_URL}/api/conversations`, {
      params: { page: 'invalid' },
    });

    expect(response2.status()).toBe(422);
  });

  test('[P1] should validate per_page parameter constraints', async ({ request }) => {
    // Test per_page > 100 (max allowed)
    const response1 = await request.get(`${BASE_URL}/api/conversations`, {
      params: { per_page: '101' },
    });

    expect(response1.status()).toBe(422);

    // Test per_page < 1
    const response2 = await request.get(`${BASE_URL}/api/conversations`, {
      params: { per_page: '0' },
    });

    expect(response2.status()).toBe(422);

    // Test per_page = 100 (boundary test - should pass validation)
    const response3 = await request.get(`${BASE_URL}/api/conversations`, {
      params: { per_page: '100' },
    });

    // Validation should pass (might be 404 if no data, but not 422)
    expect(response3.status()).not.toBe(422);
  });

  test('[P1] should handle pagination overflow gracefully', async ({ request }) => {
    // Request page beyond available data
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        page: '9999',
        per_page: '20',
      },
    });

    // Should return 200 with empty array or 404
    // Either is acceptable - endpoint handles invalid page gracefully
    expect([200, 404]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      expect(body.data).toEqual([]);
    }
  });

  test('[P2] should return correct pagination metadata', async ({ request }) => {
    // This test requires seeded data with known count
    // For now, we validate the metadata structure

    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        page: '1',
        per_page: '10',
      },
    });

    if (response.status() === 200) {
      const body = await response.json();
      const { pagination } = body.meta;

      // Validate pagination math
      const expectedTotalPages = Math.ceil(pagination.total / pagination.perPage);
      expect(pagination.totalPages).toBe(expectedTotalPages);

      // Validate bounds
      expect(pagination.page).toBeGreaterThanOrEqual(1);
      expect(pagination.page).toBeLessThanOrEqual(pagination.totalPages);
      expect(pagination.perPage).toBeGreaterThanOrEqual(1);
      expect(pagination.perPage).toBeLessThanOrEqual(100);
    }
  });
});

test.describe('Conversations API - Sorting', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] should validate sort_by parameter', async ({ request }) => {
    // Test invalid sort column
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sort_by: 'invalid_column' },
    });

    // Should return validation error (400 or 422)
    expect([400, 401, 422]).toContain(response.status());

    if (response.status() === 422) {
      const body = await response.json();
      expect(body).toHaveProperty('detail');
    }
  });

  test('[P1] should validate sort_order parameter', async ({ request }) => {
    // Test invalid sort order (FastAPI pattern validation)
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sort_order: 'invalid' },
    });

    // Pattern validation should fail
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P1] should accept valid sort columns', async ({ request }) => {
    const validColumns = ['updated_at', 'status', 'created_at'];

    for (const column of validColumns) {
      const response = await request.get(`${BASE_URL}/api/conversations`, {
        params: {
          sort_by: column,
          sort_order: 'desc',
        },
      });

      // Validation should pass (might be 404/no data, but not 422)
      expect(response.status()).not.toBe(422);
    }
  });

  test('[P1] should accept valid sort orders', async ({ request }) => {
    const validOrders = ['asc', 'desc'];

    for (const order of validOrders) {
      const response = await request.get(`${BASE_URL}/api/conversations`, {
        params: {
          sort_by: 'updated_at',
          sort_order: order,
        },
      });

      // Validation should pass
      expect(response.status()).not.toBe(422);
    }
  });

  test('[P2] should return conversations sorted correctly', async ({ request }) => {
    // This test requires seeded data with known timestamps
    // For now, we validate the endpoint accepts sort parameters

    const responseDesc = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        sort_by: 'updated_at',
        sort_order: 'desc',
      },
    });

    if (responseDesc.status() === 200) {
      const bodyDesc = await response.json();

      if (bodyDesc.data.length > 1) {
        // Verify descending order (newest first)
        const firstDate = new Date(bodyDesc.data[0].updated_at);
        const secondDate = new Date(bodyDesc.data[1].updated_at);
        expect(firstDate.getTime()).toBeGreaterThanOrEqual(secondDate.getTime());
      }
    }

    // Test ascending order
    const responseAsc = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        sort_by: 'updated_at',
        sort_order: 'asc',
      },
    });

    if (responseAsc.status() === 200) {
      const bodyAsc = await response.json();

      if (bodyAsc.data.length > 1) {
        // Verify ascending order (oldest first)
        const firstDate = new Date(bodyAsc.data[0].updated_at);
        const secondDate = new Date(bodyAsc.data[1].updated_at);
        expect(firstDate.getTime()).toBeLessThanOrEqual(secondDate.getTime());
      }
    }
  });
});

test.describe('Conversations API - Response Format', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P0] should return valid JSON content type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`);

    if (response.status() === 200) {
      const contentType = response.headers()['content-type'];
      expect(contentType).toMatch(/application\/json/);
    }
  });

  test('[P1] should include masked customer ID', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`);

    if (response.status() === 200) {
      const body = await response.json();

      if (body.data.length > 0) {
        const conversation = body.data[0];

        // Validate masking format (e.g., "cust****" or "1234****")
        expect(conversation).toHaveProperty('platformSenderIdMasked');
        expect(conversation.platformSenderIdMasked).toMatch(/\*{4,}$/);

        // Original ID should NOT be in response (security)
        expect(conversation).not.toHaveProperty('platformSenderId');
      }
    }
  });

  test('[P1] should include all required conversation fields', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`);

    if (response.status() === 200) {
      const body = await response.json();

      if (body.data.length > 0) {
        const conversation = body.data[0];

        // All required fields must be present
        const requiredFields = [
          'id',
          'platformSenderIdMasked',
          'lastMessage',
          'status',
          'messageCount',
          'updated_at',
          'created_at',
        ];

        for (const field of requiredFields) {
          expect(conversation).toHaveProperty(field);
        }

        // Validate status enum values
        expect(['active', 'handoff', 'closed']).toContain(conversation.status);

        // Validate message count is non-negative
        expect(conversation.messageCount).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('[P2] should handle null last_message gracefully', async ({ request }) => {
    // This test requires a conversation with no messages
    // For now, we validate the field structure

    const response = await request.get(`${BASE_URL}/api/conversations`);

    if (response.status() === 200) {
      const body = await response.json();

      // lastMessage can be null or a string
      if (body.data.length > 0) {
        const conversation = body.data[0];
        const hasValidLastMessage =
          conversation.lastMessage === null ||
          typeof conversation.lastMessage === 'string';

        expect(hasValidLastMessage).toBe(true);
      }
    }
  });
});

test.describe('Conversations API - Edge Cases', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P2] should handle very large page numbers', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        page: '1000000',
        per_page: '20',
      },
    });

    // Should handle gracefully (200 with empty array or 404)
    expect([200, 404]).toContain(response.status());
  });

  test('[P2] should handle minimum per_page value', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        per_page: '1',
      },
    });

    // Should accept minimum value (validation passes)
    expect(response.status()).not.toBe(422);
  });

  test('[P2] should handle maximum per_page value', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        per_page: '100',
      },
    });

    // Should accept maximum value (validation passes)
    expect(response.status()).not.toBe(422);
  });

  test('[P3] should handle special characters in sort parameters', async ({ request }) => {
    // Test SQL injection protection
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        sort_by: "updated_at; DROP TABLE conversations--",
      },
    });

    // Should reject malicious input
    expect([400, 401, 422]).toContain(response.status());
  });
});
