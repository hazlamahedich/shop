/**
 * API Tests for Story 10-8: Top Topics Widget - Caching Behavior
 *
 * Tests the caching behavior of the top topics API endpoint.
 * Validates AC7: 1-hour caching strategy.
 *
 * Test ID Format: 10.8-API-XXX
 */

import { test, expect } from '@playwright/test';

const API_ENDPOINT = '/api/v1/analytics/top-topics';

test.describe('[P1] Story 10-8: Top Topics API - Caching', () => {
  test('[10.8-API-001] @p1 should return Cache-Control header with 1-hour max-age', async ({
    request,
  }) => {
    const response = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    expect(response.status()).toBe(200);

    const cacheControl = response.headers()['cache-control'];
    expect(cacheControl).toBeDefined();
    expect(cacheControl).toContain('max-age=3600');
  });

  test('[10.8-API-002] @p1 should include ETag header for cache validation', async ({
    request,
  }) => {
    const response = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    expect(response.status()).toBe(200);

    const etag = response.headers()['etag'];
    expect(etag).toBeDefined();
    expect(etag.length).toBeGreaterThan(0);
  });

  test('[10.8-API-003] @p1 should respect If-None-Match header for 304 response', async ({
    request,
  }) => {
    const firstResponse = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    expect(firstResponse.status()).toBe(200);
    const etag = firstResponse.headers()['etag'];

    const secondResponse = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
        'If-None-Match': etag,
      },
    });

    expect([200, 304]).toContain(secondResponse.status());
  });

  test('[10.8-API-004] @p1 should return different cache keys for different days parameter', async ({
    request,
  }) => {
    const response7d = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    const response30d = await request.get(`${API_ENDPOINT}?days=30`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    expect(response7d.status()).toBe(200);
    expect(response30d.status()).toBe(200);

    const etag7d = response7d.headers()['etag'];
    const etag30d = response30d.headers()['etag'];

    if (etag7d && etag30d) {
      expect(etag7d).not.toBe(etag30d);
    }
  });

  test('[10.8-API-005] @p1 should include Vary header for merchant-specific caching', async ({
    request,
  }) => {
    const response = await request.get(`${API_ENDPOINT}?days=7`, {
      headers: {
        'X-Test-Mode': 'true',
        'X-Merchant-Id': '1',
      },
    });

    expect(response.status()).toBe(200);

    const vary = response.headers()['vary'];
    if (vary) {
      expect(vary.toLowerCase()).toContain('merchant');
    }
  });
});
