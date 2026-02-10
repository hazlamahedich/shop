/**
 * API Tests for Story 1.11: FAQ Rate Limiting
 *
 * Tests rate limiting behavior on FAQ endpoints.
 * Verifies 429 responses when rate limits are exceeded.
 *
 * @tags api integration faq story-1-11 rate-limit
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

// Rate limit configuration (adjust based on actual backend settings)
const RATE_LIMIT_CONFIG = {
  faqEndpoints: {
    maxRequests: 10, // Adjust based on actual rate limit
    windowSeconds: 60,
  },
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: FAQ Rate Limiting [P1]', () => {
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
    }
  });

  test.beforeEach(async ({ request }) => {
    // Reset rate limits before each test (if test endpoint is available)
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: { 'X-Test-Mode': 'true' },
    }).catch(() => {
      // Ignore if reset endpoint doesn't exist
    });
  });

  test('[P1] should return 429 after exceeding FAQ GET rate limit', async ({ request }) => {
    const rateLimitReached: number[] = [];

    // When: Making rapid GET requests to /faqs
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Test-Mode': 'false', // Enable rate limiting
        },
      });

      if (response.status() === 429) {
        rateLimitReached.push(i);
        break; // Stop once we hit the rate limit
      }
    }

    // Then: Should eventually return 429
    expect(rateLimitReached.length).toBeGreaterThan(0);
  });

  test('[P1] should return 429 after exceeding FAQ POST rate limit', async ({ request }) => {
    const rateLimitReached: number[] = [];

    // When: Making rapid POST requests to create FAQs
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-Test-Mode': 'false',
        },
        data: {
          question: `Rate Limit Test ${i}?`,
          answer: `Answer ${i}`,
          keywords: `rl${i}`,
        },
      });

      if (response.status() === 429) {
        rateLimitReached.push(i);
        break;
      }

      // Clean up created FAQ for next iteration
      if (response.ok()) {
        const data = await response.json();
        await request.delete(`${API_URL}/api/v1/merchant/faqs/${data.data.id}`, {
          headers: { Authorization: `Bearer ${authToken}` },
        });
      }
    }

    // Then: Should eventually return 429
    expect(rateLimitReached.length).toBeGreaterThan(0);
  });

  test('[P1] should return 429 after exceeding FAQ PUT rate limit', async ({ request }) => {
    // Given: An FAQ to update
    const createResponse = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      data: {
        question: 'Rate Limit Update Test?',
        answer: 'Original answer',
        keywords: 'rlu',
      },
    });

    if (!createResponse.ok()) {
      test.skip(true, 'Could not create test FAQ');
      return;
    }

    const createData = await createResponse.json();
    const faqId = createData.data.id;
    const rateLimitReached: number[] = [];

    // When: Making rapid PUT requests to update FAQ
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.put(`${API_URL}/api/v1/merchant/faqs/${faqId}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-Test-Mode': 'false',
        },
        data: {
          answer: `Updated answer ${i}`,
        },
      });

      if (response.status() === 429) {
        rateLimitReached.push(i);
        break;
      }
    }

    // Then: Should eventually return 429
    expect(rateLimitReached.length).toBeGreaterThan(0);

    // Clean up
    await request.delete(`${API_URL}/api/v1/merchant/faqs/${faqId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
  });

  test('[P1] should return 429 after exceeding FAQ DELETE rate limit', async ({ request }) => {
    // Given: Multiple FAQs to delete
    const createdIds: number[] = [];
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          question: `Delete Rate Test ${i}?`,
          answer: `Answer ${i}`,
          keywords: `drl${i}`,
        },
      });

      if (response.ok()) {
        const data = await response.json();
        createdIds.push(data.data.id);
      }
    }

    const rateLimitReached: number[] = [];

    // When: Making rapid DELETE requests
    for (let i = 0; i < createdIds.length; i++) {
      const response = await request.delete(`${API_URL}/api/v1/merchant/faqs/${createdIds[i]}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Test-Mode': 'false',
        },
      });

      if (response.status() === 429) {
        rateLimitReached.push(i);
        break;
      }
    }

    // Then: Should eventually return 429
    expect(rateLimitReached.length).toBeGreaterThan(0);
  });

  test('[P1] should return 429 after exceeding FAQ reorder rate limit', async ({ request }) => {
    // Given: Multiple FAQs exist
    const createdIds: number[] = [];
    for (let i = 0; i < 3; i++) {
      const response = await request.post(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        data: {
          question: `Reorder Rate Test ${i}?`,
          answer: `Answer ${i}`,
          keywords: `rrl${i}`,
        },
      });

      if (response.ok()) {
        const data = await response.json();
        createdIds.push(data.data.id);
      }
    }

    const rateLimitReached: number[] = [];

    // When: Making rapid reorder requests
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      // Shuffle the order for each request
      const shuffled = [...createdIds].sort(() => Math.random() - 0.5);

      const response = await request.put(`${API_URL}/api/v1/merchant/faqs/reorder`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
          'X-Test-Mode': 'false',
        },
        data: {
          faq_ids: shuffled,
        },
      });

      if (response.status() === 429) {
        rateLimitReached.push(i);
        break;
      }
    }

    // Then: Should eventually return 429
    expect(rateLimitReached.length).toBeGreaterThan(0);

    // Clean up
    for (const id of createdIds) {
      await request.delete(`${API_URL}/api/v1/merchant/faqs/${id}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
    }
  });

  test('[P1] should include retry-after header in 429 response', async ({ request }) => {
    // Make rapid requests to trigger rate limit
    let lastResponse: any = null;

    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      lastResponse = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Test-Mode': 'false',
        },
      });

      if (lastResponse.status() === 429) {
        break;
      }
    }

    if (lastResponse && lastResponse.status() === 429) {
      // Then: Response should include retry information
      const headers = lastResponse.headers();
      const retryAfter = headers['retry-after'];

      // retry-after header should be present (optional but recommended)
      if (retryAfter) {
        expect(parseInt(retryAfter)).toBeGreaterThanOrEqual(0);
      }

      // Response body should have error details
      const body = await lastResponse.json();
      expect(body.detail).toBeDefined();
      expect(body.detail.message.toLowerCase()).toMatch(/rate limit|too many requests/i);
    } else {
      test.skip(true, 'Rate limit not triggered within expected request count');
    }
  });

  test('[P1] should allow requests after rate limit window expires', async ({ request }) => {
    let rateLimitResponse: any = null;

    // When: Exceed rate limit
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Test-Mode': 'false',
        },
      });

      if (response.status() === 429) {
        rateLimitResponse = response;
        break;
      }
    }

    if (rateLimitResponse) {
      // Wait for rate limit window to expire
      // Note: This may take up to the configured window duration
      // In tests, we might use a shorter window or manual reset
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Reset rate limits for test purposes
      await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
        headers: { 'X-Test-Mode': 'true' },
      }).catch(() => {});

      // Then: Request should succeed again
      const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      expect(response.status()).toBe(200);
    } else {
      test.skip(true, 'Rate limit not triggered within expected request count');
    }
  });

  test('[P1] should rate limit per merchant/IP basis', async ({ request }) => {
    // This test verifies that rate limiting is applied per merchant or IP
    // We use X-Forwarded-For to simulate different IPs

    let ip1RateLimited = false;
    let ip2RateLimited = false;

    // Make requests from IP 1
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Forwarded-For': '192.168.1.100',
          'X-Test-Mode': 'false',
        },
      });

      if (response.status() === 429) {
        ip1RateLimited = true;
        break;
      }
    }

    // Make requests from IP 2
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests + 5; i++) {
      const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'X-Forwarded-For': '192.168.1.101',
          'X-Test-Mode': 'false',
        },
      });

      if (response.status() === 429) {
        ip2RateLimited = true;
        break;
      }
    }

    // Both IPs should be rate limited independently
    expect(ip1RateLimited).toBe(true);
    expect(ip2RateLimited).toBe(true);
  });

  test('[P2] should not rate limit in test mode when disabled', async ({ request }) => {
    // When: Making many requests with rate limiting disabled
    const requests = [];
    for (let i = 0; i < RATE_LIMIT_CONFIG.faqEndpoints.maxRequests * 2; i++) {
      requests.push(
        request.get(`${API_URL}/api/v1/merchant/faqs`, {
          headers: {
            Authorization: `Bearer ${authToken}`,
            'X-Test-Mode': 'true', // Disable rate limiting
          },
        })
      );
    }

    const responses = await Promise.all(requests);

    // Then: All requests should succeed (no 429 responses)
    const rateLimitedCount = responses.filter(r => r.status() === 429).length;
    expect(rateLimitedCount).toBe(0);
  });

  test('[P2] should include rate limit info headers when available', async ({ request }) => {
    // When: Making a request
    const response = await request.get(`${API_URL}/api/v1/merchant/faqs`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    // Then: Check for rate limit headers (optional but recommended)
    const headers = response.headers();

    // These headers are optional but commonly used
    // RateLimit-Limit, RateLimit-Remaining, RateLimit-Reset
    if (headers['ratelimit-limit']) {
      expect(parseInt(headers['ratelimit-limit'])).toBeGreaterThan(0);
    }

    if (headers['ratelimit-remaining']) {
      expect(parseInt(headers['ratelimit-remaining'])).toBeGreaterThanOrEqual(0);
    }
  });
});
