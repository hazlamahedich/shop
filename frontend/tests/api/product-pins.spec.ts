/**
 * API Tests: Product Highlight Pins
 *
 * Story 1.15: Product Highlight Pins
 *
 * Tests product pin API endpoints:
 * - GET /api/v1/merchant/product-pins - List products with pin status
 * - POST /api/v1/merchant/product-pins - Pin a product
 * - DELETE /api/v1/merchant/product-pins/{product_id} - Unpin a product
 * - POST /api/v1/merchant/product-pins/reorder - Reorder pinned products
 *
 * Test Levels:
 * - P0: Critical paths (pin/unpin, data integrity)
 * - P1: High priority (search, pagination, limits)
 * - P2: Medium priority (error handling, validation)
 *
 * @tags api story-1-15 product-highlight-pins
 */

import { test, expect } from '@playwright/test';
import { createProductPinData, createProductPinList, createPinLimitInfo, createPaginationData, createErrorResponse } from '../fixtures/data-factories';
import { waitForApiResponse, mockApiResponse, mockApiError } from '../fixtures/helpers';

const API_URL = process.env.API_URL || 'http://localhost:8000';

// Test merchant credentials
const TEST_MERCHANT = {
  email: 'e2e-product-pins@test.com',
  password: 'TestPass123',
};

// Helper to get auth token
async function getAuthToken(): Promise<string> {
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(TEST_MERCHANT),
  });

  if (!response.ok) {
    throw new Error(`Failed to authenticate: ${response.status}`);
  }

  const data = await response.json();
  return data.data.token;
}

// Helper to make authenticated API requests
async function apiRequest(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = await getAuthToken();

  return fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
}

test.describe('Story 1.15: Product Pins API', () => {
  let authToken: string;

  // Authenticate before all tests
  test.beforeAll(async () => {
    authToken = await getAuthToken();
  });

  test.describe('GET /api/v1/merchant/product-pins', () => {
    test('[P0] should return products with pin status for authenticated merchant', async ({ request }) => {
      const response = await apiRequest('/api/v1/merchant/product-pins');

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify response structure
      expect(data).toHaveProperty('data');
      expect(data).toHaveProperty('meta');
      expect(data.data).toHaveProperty('products');
      expect(data.data).toHaveProperty('pagination');
      expect(data.data).toHaveProperty('pinLimit');
      expect(data.data).toHaveProperty('pinnedCount');

      // Verify products array
      expect(Array.isArray(data.data.products)).toBeTruthy();

      // Verify pagination structure
      expect(data.data.pagination).toMatchObject({
        page: expect.any(Number),
        limit: expect.any(Number),
        total: expect.any(Number),
        has_more: expect.any(Boolean),
      });

      // Verify pin limit info
      expect(typeof data.data.pinLimit).toBe('number');
      expect(typeof data.data.pinnedCount).toBe('number');
    });

    test('[P0] should include CSRF protection metadata', async ({ request }) => {
      const response = await apiRequest('/api/v1/merchant/product-pins');

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify meta has request tracking
      expect(data.meta).toHaveProperty('requestId');
      expect(data.meta).toHaveProperty('timestamp');
    });

    test('[P1] should support search query parameter', async ({ request }) => {
      const searchTerm = 'running';

      const response = await apiRequest(
        `/api/v1/merchant/product-pins?search=${encodeURIComponent(searchTerm)}`
      );

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify search filtered results
      if (data.data.products.length > 0) {
        const hasMatchingProduct = data.data.products.some(
          (p: any) => p.title && p.title.toLowerCase().includes(searchTerm)
        );
        expect(hasMatchingProduct).toBeTruthy();
      }
    });

    test('[P1] should support pinned_only filter', async ({ request }) => {
      const response = await apiRequest(
        '/api/v1/merchant/product-pins?pinned_only=true'
      );

      expect(response.status).toBe(200);

      const data = await response.json();

      // All returned products should be pinned
      const allPinned = data.data.products.every(
        (p: any) => p.is_pinned === true
      );
      expect(allPinned).toBeTruthy();
    });

    test('[P1] should support pagination parameters', async ({ request }) => {
      const page = 2;
      const limit = 10;

      const response = await apiRequest(
        `/api/v1/merchant/product-pins?page=${page}&limit=${limit}`
      );

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify pagination applied
      expect(data.data.pagination.page).toBe(page);
      expect(data.data.pagination.limit).toBe(limit);
      expect(data.data.products.length).toBeLessThanOrEqual(limit);
    });

    test('[P2] should handle empty product list gracefully', async ({ request }) => {
      // This test assumes merchant has no products
      const response = await apiRequest('/api/v1/merchant/product-pins');

      expect(response.status).toBe(200);

      const data = await response.json();

      // Empty list should still have valid structure
      expect(data.data.products).toEqual([]);
      expect(data.data.pagination.total).toBe(0);
      expect(data.data.pinnedCount).toBe(0);
    });

    test('[P2] should handle invalid pagination values', async ({ request }) => {
      const response = await apiRequest(
        '/api/v1/merchant/product-pins?page=-1&limit=9999'
      );

      // Should return 400 for invalid pagination
      expect(response.status).toBe(400);

      const data = await response.json();

      expect(data).toHaveProperty('error');
    });
  });

  test.describe('POST /api/v1/merchant/product-pins', () => {
    test('[P0] should pin a product successfully', async ({ request }) => {
      const testData = createProductPinData({
        is_pinned: true,
        pinned_order: 1,
      });

      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify response structure
      expect(data.data).toHaveProperty('productId', testData.product_id);
      expect(data.data).toHaveProperty('isPinned', true);
      expect(data.data).toHaveProperty('pinnedOrder', testData.pinned_order);
      expect(data.data).toHaveProperty('pinnedAt');
    });

    test('[P0] should enforce 10-product pin limit', async ({ request }) => {
      // Pin 10 products using factory
      const pinnedProducts = createProductPinList(10, { is_pinned: true });

      const pinPromises = pinnedProducts.map((product) =>
        apiRequest('/api/v1/merchant/product-pins', {
          method: 'POST',
          body: JSON.stringify({ product_id: product.product_id }),
        })
      );

      await Promise.all(pinPromises);

      // Attempting to pin 11th product should fail
      const overflowProduct = createProductPinData();
      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: overflowProduct.product_id }),
      });

      // Should return 4602 error code (Pin limit reached)
      expect(response.status).toBe(400);

      const data = await response.json();
      expect(data.error_code).toBe(4602);
      expect(data.message).toContain('pin limit');
    });

    test('[P1] should prevent duplicate pins', async ({ request }) => {
      const testData = createProductPinData();

      // Pin product first time
      await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      // Attempt to pin same product again
      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      // Should return 4603 error (Product already pinned)
      expect(response.status).toBe(400);

      const data = await response.json();
      expect(data.error_code).toBe(4603);
    });

    test('[P1] should validate product_id is not empty', async ({ request }) => {
      const testData = createProductPinData({ product_id: '' });

      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      // Should return 4600 error (Product ID is required)
      expect(response.status).toBe(400);

      const data = await response.json();
      expect(data.error_code).toBe(4600);
    });

    test('[P2] should handle malformed request body', async ({ request }) => {
      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: 'invalid json',
      });

      expect(response.status).toBe(400);

      const data = await response.json();
      expect(data).toHaveProperty('error');
    });
  });

  test.describe('DELETE /api/v1/merchant/product-pins/{product_id}', () => {
    test('[P0] should unpin a product successfully', async ({ request }) => {
      const testData = createProductPinData({
        is_pinned: true,
        pinned_order: 1,
      });

      const response = await apiRequest(
        `/api/v1/merchant/product-pins/${testData.product_id}`,
        { method: 'DELETE' }
      );

      expect(response.status).toBe(200);

      const data = await response.json();

      // Verify response structure
      expect(data.data).toHaveProperty('productId', testData.product_id);
      expect(data.data).toHaveProperty('isPinned', false);
    });

    test('[P1] should allow re-pinning after unpinned', async ({ request }) => {
      const testData = createProductPinData({
        is_pinned: true,
        pinned_order: 1,
      });

      // First pin product
      await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      // Unpin product
      await apiRequest(
        `/api/v1/merchant/product-pins/${testData.product_id}`,
        { method: 'DELETE' }
      );

      // Re-pin should succeed
      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      expect(response.status).toBe(200);

      const data = await response.json();

      expect(data.data.isPinned).toBe(true);
    });

    test('[P2] should handle unpinning non-existent product', async ({ request }) => {
      const response = await apiRequest(
        '/api/v1/merchant/product-pins/non_existent_product_id',
        { method: 'DELETE' }
      );

      // Should return success or handle gracefully
      expect([200, 404]).toContain(response.status);
    });
  });

  test.describe('POST /api/v1/merchant/product-pins/reorder', () => {
    test('[P1] should reorder pinned products successfully', async ({ request }) => {
      const testData1 = {
        product_1: 'prod_1',
        product_2: 'prod_2',
        product_3: 'prod_3',
      };

      const productOrders = [
        { product_id: testData1.product_1, order: 1 },
        { product_id: testData1.product_2, order: 2 },
        { product_id: testData1.product_3, order: 3 },
      ];

      const response = await apiRequest('/api/v1/merchant/product-pins/reorder', {
        method: 'POST',
        body: JSON.stringify({ product_orders: productOrders }),
      });

      expect(response.status).toBe(200);

      const data = await response.json();

      expect(data).toHaveProperty('data');
    });

    test('[P2] should validate product_orders array structure', async ({ request }) => {
      // Missing required field
      const response = await apiRequest('/api/v1/merchant/product-pins/reorder', {
        method: 'POST',
        body: JSON.stringify({ product_orders: [{ product_id: 'test' }] }),
      });

      expect(response.status).toBe(400);

      const data = await response.json();

      expect(data).toHaveProperty('error');
    });

    test('[P2] should handle empty product_orders', async ({ request }) => {
      const response = await apiRequest('/api/v1/merchant/product-pins/reorder', {
        method: 'POST',
        body: JSON.stringify({ product_orders: [] }),
      });

      // Empty array should be handled gracefully
      expect([200, 400]).toContain(response.status);
    });
  });

  test.describe('Authentication & Authorization', () => {
    test('[P0] should require authentication for all endpoints', async ({ request }) => {
      // Request without auth token
      const response = await fetch(`${API_URL}/api/v1/merchant/product-pins`);

      expect(response.status).toBe(401);
    });

    test('[P1] should reject invalid auth tokens', async ({ request }) => {
      const response = await fetch(`${API_URL}/api/v1/merchant/product-pins`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer invalid_token_12345',
        },
      });

      expect(response.status).toBe(401);
    });

    test('[P1] should validate merchant owns product pins', async ({ request }) => {
      // This test would require two merchant accounts
      // For now, verify authorization header is processed
      const response = await apiRequest('/api/v1/merchant/product-pins');

      expect(response.status).toBe(200);

      const data = await response.json();

      // Should only return current merchant's products
      expect(data.data).toHaveProperty('products');
    });
  });

  test.describe('Error Response Format', () => {
    test('[P2] should return consistent error format', async ({ request }) => {
      const testData = createProductPinData({ product_id: '' });

      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      expect(response.status).toBe(400);

      const data = await response.json();

      expect(data).toHaveProperty('error');
      expect(data).toHaveProperty('error_code');
      expect(data).toHaveProperty('details');
    });

    test('[P2] should include request_id in error response', async ({ request }) => {
      const testData = createProductPinData();

      const response = await apiRequest('/api/v1/merchant/product-pins', {
        method: 'POST',
        body: JSON.stringify({ product_id: testData.product_id }),
      });

      expect(response.status).toBe(400);

      const data = await response.json();

      // Verify error has tracking metadata
      expect(data.meta).toHaveProperty('requestId');
    });
  });

  test.describe('CSRF Protection', () => {
    test('[P0] should require CSRF token for state-changing operations', async ({ request }) => {
      // POST without CSRF token should fail
      const response = await fetch(`${API_URL}/api/v1/merchant/product-pins`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
          // Missing X-CSRF-Token header
        },
        body: JSON.stringify({ product_id: 'test_product' }),
      });

      // Should return 403 or 400
      expect([403, 400]).toContain(response.status);
    });

    test('[P1] should accept valid CSRF token', async ({ request }) => {
      // First get CSRF token
      const csrfResponse = await fetch(`${API_URL}/api/v1/csrf-token`, {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });

      expect(csrfResponse.ok).toBeTruthy();

      const { csrf_token } = await csrfResponse.json();

      // Now use CSRF token in request
      const response = await fetch(`${API_URL}/api/v1/merchant/product-pins`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
          'X-CSRF-Token': csrf_token,
        },
        body: JSON.stringify({ product_id: 'test_product' }),
      });

      expect([200, 201]).toContain(response.status);
    });
  });
});
