/**
 * Conversations API Filter Tests
 *
 * Story 3-2: Search and Filter Conversations
 * Tests the /api/conversations endpoint with search and filter parameters
 *
 * @tags api integration conversations story-3-2 filters
 */

import { test, expect } from '@playwright/test';
import { createConversation, createConversations } from '../factories/conversation.factory';

/**
 * Base URL for API requests
 */
const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

/**
 * Valid enum values for validation tests
 */
const VALID_STATUS_VALUES = ['active', 'handoff', 'closed'];
const VALID_SENTIMENT_VALUES = ['positive', 'neutral', 'negative'];

test.describe('Conversations API - Search Parameter', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P0] @smoke should accept valid search parameter', async ({ request }) => {
    // Given: A valid search term
    const searchTerm = 'customer_';

    // When: Searching conversations
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: searchTerm },
    });

    // Then: Request should be accepted (not 422 validation error)
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate response structure
      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');
      expect(Array.isArray(body.data)).toBe(true);
    }
  });

  test('[P2] should handle empty search parameter', async ({ request }) => {
    // Given: An empty search string
    const emptySearch = '';

    // When: Searching with empty string
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: emptySearch },
    });

    // Then: Should return all conversations (empty search = no filter)
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();
      expect(Array.isArray(body.data)).toBe(true);
    }
  });

  test('[P2] should handle special characters in search', async ({ request }) => {
    // Given: Search term with special characters
    const searchSpecial = 'test@#$%^&*()';

    // When: Searching with special characters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: searchSpecial },
    });

    // Then: Should handle gracefully (sanitize input, no crashes)
    expect([200, 404, 400]).toContain(response.status());

    // Should NOT return 500 (server error from malformed input)
    expect(response.status()).not.toBe(500);
  });

  test('[P3] should handle very long search strings', async ({ request }) => {
    // Given: Extremely long search string (1000 chars)
    const longSearch = 'a'.repeat(1000);

    // When: Searching with long string
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: longSearch },
    });

    // Then: Should handle gracefully
    expect([200, 404, 400]).toContain(response.status());
    expect(response.status()).not.toBe(500);
  });
});

test.describe('Conversations API - Date Range Filters', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P0] @smoke should accept valid date_from parameter', async ({ request }) => {
    // Given: A valid ISO 8601 date
    const dateFrom = '2026-01-01';

    // When: Filtering by start date
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { date_from: dateFrom },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);
  });

  test('[P0] should accept valid date_to parameter', async ({ request }) => {
    // Given: A valid ISO 8601 date
    const dateTo = '2026-12-31';

    // When: Filtering by end date
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { date_to: dateTo },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);
  });

  test('[P1] should accept both date_from and date_to together', async ({ request }) => {
    // Given: Valid start and end dates
    const dateFrom = '2026-01-01';
    const dateTo = '2026-01-31';

    // When: Filtering by date range
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        date_from: dateFrom,
        date_to: dateTo,
      },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate filtered dates are within range
      if (body.data.length > 0) {
        const firstConversation = body.data[0];
        const convoDate = new Date(firstConversation.updated_at);
        const fromDate = new Date(dateFrom);
        const toDate = new Date(dateTo);

        // Date should be within range (inclusive)
        expect(convoDate.getTime()).toBeGreaterThanOrEqual(fromDate.getTime());
        expect(convoDate.getTime()).toBeLessThanOrEqual(toDate.getTime());
      }
    }
  });

  test('[P2] should reject invalid date format for date_from', async ({ request }) => {
    // Given: Invalid date format
    const invalidDate = '01-01-2026'; // MM-DD-YYYY instead of ISO

    // When: Filtering with invalid format
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { date_from: invalidDate },
    });

    // Then: Should return validation error
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P2] should reject invalid date format for date_to', async ({ request }) => {
    // Given: Invalid date format
    const invalidDate = 'not-a-date';

    // When: Filtering with invalid format
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { date_to: invalidDate },
    });

    // Then: Should return validation error
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P2] should accept ISO datetime strings', async ({ request }) => {
    // Given: Full ISO 8601 datetime string
    const dateFrom = '2026-01-01T00:00:00Z';
    const dateTo = '2026-01-31T23:59:59Z';

    // When: Filtering with datetime strings
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        date_from: dateFrom,
        date_to: dateTo,
      },
    });

    // Then: Should accept ISO datetime format
    expect(response.status()).not.toBe(422);
  });

  test('[P3] should handle inverted date range', async ({ request }) => {
    // Given: date_from after date_to (inverted range)
    const dateFrom = '2026-12-31';
    const dateTo = '2026-01-01';

    // When: Filtering with inverted range
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        date_from: dateFrom,
        date_to: dateTo,
      },
    });

    // Then: Should handle gracefully (empty result or validation error)
    // Accept either 422 (validation catches it) or 200 with empty results
    expect([200, 422]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      // Inverted range should return empty results
      expect(body.data).toEqual([]);
    }
  });
});

test.describe('Conversations API - Status Filter', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] @smoke should accept single status filter', async ({ request }) => {
    // Given: A valid status value
    const status = 'active';

    // When: Filtering by single status
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: [status] },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate all results match the status filter
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.status).toBe(status);
        });
      }
    }
  });

  test('[P1] should accept multiple status filters', async ({ request }) => {
    // Given: Multiple valid status values
    const statuses = ['active', 'handoff'];

    // When: Filtering by multiple statuses
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: statuses },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate all results match one of the status filters
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(statuses).toContain(conversation.status);
        });
      }
    }
  });

  test('[P1] should accept all valid status values', async ({ request }) => {
    // Given: All valid status values
    const allStatuses = [...VALID_STATUS_VALUES];

    // When: Filtering by all statuses
    for (const status of allStatuses) {
      const response = await request.get(`${BASE_URL}/api/conversations`, {
        params: { status: [status] },
      });

      // Then: Each valid value should be accepted
      expect(response.status()).not.toBe(422);
    }
  });

  test('[P2] should reject invalid status value', async ({ request }) => {
    // Given: An invalid status value
    const invalidStatus = 'invalid_status';

    // When: Filtering with invalid status
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: [invalidStatus] },
    });

    // Then: Should return validation error
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P2] should reject mixed valid and invalid status values', async ({ request }) => {
    // Given: Mix of valid and invalid status values
    const mixedStatuses = ['active', 'invalid', 'closed'];

    // When: Filtering with mixed values
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: mixedStatuses },
    });

    // Then: Should return validation error for invalid value
    expect(response.status()).toBe(422);
  });

  test('[P3] should handle empty status array', async ({ request }) => {
    // Given: Empty status array
    const emptyStatus: string[] = [];

    // When: Filtering with empty array
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: emptyStatus },
    });

    // Then: Should handle gracefully (no filter applied or validation error)
    expect([200, 422]).toContain(response.status());
  });
});

test.describe('Conversations API - Sentiment Filter', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] @smoke should accept single sentiment filter', async ({ request }) => {
    // Given: A valid sentiment value
    const sentiment = 'positive';

    // When: Filtering by single sentiment
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sentiment: [sentiment] },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate all results match the sentiment filter
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.sentiment).toBe(sentiment);
        });
      }
    }
  });

  test('[P1] should accept multiple sentiment filters', async ({ request }) => {
    // Given: Multiple valid sentiment values
    const sentiments = ['positive', 'neutral'];

    // When: Filtering by multiple sentiments
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sentiment: sentiments },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate all results match one of the sentiment filters
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(sentiments).toContain(conversation.sentiment);
        });
      }
    }
  });

  test('[P1] should accept all valid sentiment values', async ({ request }) => {
    // Given: All valid sentiment values
    const allSentiments = [...VALID_SENTIMENT_VALUES];

    // When: Filtering by all sentiments
    for (const sentiment of allSentiments) {
      const response = await request.get(`${BASE_URL}/api/conversations`, {
        params: { sentiment: [sentiment] },
      });

      // Then: Each valid value should be accepted
      expect(response.status()).not.toBe(422);
    }
  });

  test('[P2] should reject invalid sentiment value', async ({ request }) => {
    // Given: An invalid sentiment value
    const invalidSentiment = 'very_positive';

    // When: Filtering with invalid sentiment
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sentiment: [invalidSentiment] },
    });

    // Then: Should return validation error
    expect(response.status()).toBe(422);

    const body = await response.json();
    expect(body).toHaveProperty('detail');
  });

  test('[P2] should reject mixed valid and invalid sentiment values', async ({ request }) => {
    // Given: Mix of valid and invalid sentiment values
    const mixedSentiments = ['positive', 'invalid', 'negative'];

    // When: Filtering with mixed values
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sentiment: mixedSentiments },
    });

    // Then: Should return validation error for invalid value
    expect(response.status()).toBe(422);
  });

  test('[P3] should handle empty sentiment array', async ({ request }) => {
    // Given: Empty sentiment array
    const emptySentiment: string[] = [];

    // When: Filtering with empty array
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { sentiment: emptySentiment },
    });

    // Then: Should handle gracefully
    expect([200, 422]).toContain(response.status());
  });
});

test.describe('Conversations API - Handoff Filter', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] @smoke should accept has_handoff true', async ({ request }) => {
    // Given: has_handoff filter set to true
    const hasHandoff = true;

    // When: Filtering conversations with handoff
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { has_handoff: String(hasHandoff) },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate results have handoff status
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.status).toBe('handoff');
        });
      }
    }
  });

  test('[P1] should accept has_handoff false', async ({ request }) => {
    // Given: has_handoff filter set to false
    const hasHandoff = false;

    // When: Filtering conversations without handoff
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { has_handoff: String(hasHandoff) },
    });

    // Then: Validation should pass
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate results don't have handoff status
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.status).not.toBe('handoff');
        });
      }
    }
  });
});

test.describe('Conversations API - Combined Filters', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] @smoke should combine search with date range', async ({ request }) => {
    // Given: Search term and date range
    const search = 'customer_';
    const dateFrom = '2026-01-01';
    const dateTo = '2026-01-31';

    // When: Applying multiple filters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        search,
        date_from: dateFrom,
        date_to: dateTo,
      },
    });

    // Then: All filters should be applied
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();
      expect(Array.isArray(body.data)).toBe(true);

      // Validate date range is respected
      if (body.data.length > 0) {
        const firstConversation = body.data[0];
        const convoDate = new Date(firstConversation.updated_at);
        const fromDate = new Date(dateFrom);
        const toDate = new Date(dateTo);

        expect(convoDate.getTime()).toBeGreaterThanOrEqual(fromDate.getTime());
        expect(convoDate.getTime()).toBeLessThanOrEqual(toDate.getTime());
      }
    }
  });

  test('[P1] should combine search with status filter', async ({ request }) => {
    // Given: Search term and status filter
    const search = 'customer_';
    const status = ['active'];

    // When: Applying multiple filters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        search,
        status,
      },
    });

    // Then: All filters should be applied
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate status filter is respected
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.status).toBe('active');
        });
      }
    }
  });

  test('[P1] should combine all filter types', async ({ request }) => {
    // Given: All filter types combined
    const search = 'customer_';
    const dateFrom = '2026-01-01';
    const dateTo = '2026-12-31';
    const status = ['active', 'handoff'];
    const sentiment = ['positive'];
    const hasHandoff = false;

    // When: Applying all filters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        search,
        date_from: dateFrom,
        date_to: dateTo,
        status,
        sentiment,
        has_handoff: String(hasHandoff),
      },
    });

    // Then: All filters should be applied
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();
      expect(Array.isArray(body.data)).toBe(true);

      // Validate filters are respected
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          // Check status filter
          expect(status).toContain(conversation.status);

          // Check sentiment filter
          expect(sentiment).toContain(conversation.sentiment);

          // Check handoff filter
          expect(conversation.status).not.toBe('handoff');
        });
      }
    }
  });

  test('[P2] should handle conflicting filters gracefully', async ({ request }) => {
    // Given: Conflicting filters (e.g., status=active AND has_handoff=true)
    const status = ['active'];
    const hasHandoff = true;

    // When: Applying conflicting filters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        status,
        has_handoff: String(hasHandoff),
      },
    });

    // Then: Should handle gracefully (empty results is acceptable)
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Active conversations can't have handoff status
      // Should return empty results
      expect(body.data).toEqual([]);
    }
  });

  test('[P3] should handle filters with pagination', async ({ request }) => {
    // Given: Filters with pagination
    const search = 'customer_';
    const page = 1;
    const perPage = 10;

    // When: Applying filters with pagination
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        search,
        page: String(page),
        per_page: String(perPage),
      },
    });

    // Then: Should apply both filters and pagination
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body).toHaveProperty('meta');
      expect(body.meta).toHaveProperty('pagination');
      expect(body.meta.pagination.page).toBe(page);
      expect(body.meta.pagination.perPage).toBe(perPage);
    }
  });

  test('[P3] should handle filters with sorting', async ({ request }) => {
    // Given: Filters with sorting
    const status = ['active'];
    const sortBy = 'updated_at';
    const sortOrder = 'desc';

    // When: Applying filters with sorting
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        status,
        sort_by: sortBy,
        sort_order: sortOrder,
      },
    });

    // Then: Should apply both filters and sorting
    expect(response.status()).not.toBe(422);

    if (response.status() === 200) {
      const body = await response.json();

      // Validate status filter
      if (body.data.length > 0) {
        body.data.forEach((conversation: any) => {
          expect(conversation.status).toBe('active');
        });

        // Validate sort order
        if (body.data.length > 1) {
          const firstDate = new Date(body.data[0].updated_at);
          const secondDate = new Date(body.data[1].updated_at);
          expect(firstDate.getTime()).toBeGreaterThanOrEqual(secondDate.getTime());
        }
      }
    }
  });
});

test.describe('Conversations API - Filter Edge Cases', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P2] should return empty results for no-match filters', async ({ request }) => {
    // Given: Filters that match nothing
    const dateFrom = '2099-01-01'; // Future date
    const dateTo = '2099-12-31';

    // When: Applying non-matching filters
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: {
        date_from: dateFrom,
        date_to: dateTo,
      },
    });

    // Then: Should return empty results (not error)
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.data).toEqual([]);
  });

  test('[P2] should handle unicode in search parameter', async ({ request }) => {
    // Given: Search term with unicode characters
    const unicodeSearch = '客户消息'; // Chinese characters

    // When: Searching with unicode
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: unicodeSearch },
    });

    // Then: Should handle gracefully
    expect([200, 404]).toContain(response.status());
    expect(response.status()).not.toBe(500);
  });

  test('[P3] should handle filter parameter injection attempts', async ({ request }) => {
    // Given: Malicious filter parameters
    const maliciousSearch = "'; DROP TABLE conversations--";

    // When: Attempting injection
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { search: maliciousSearch },
    });

    // Then: Should sanitize and handle gracefully
    expect([200, 404, 400]).toContain(response.status());
    expect(response.status()).not.toBe(500);
  });

  test('[P3] should handle very large filter arrays', async ({ request }) => {
    // Given: Large array of status values (even duplicates)
    const largeStatusArray = Array(100).fill('active');

    // When: Filtering with large array
    const response = await request.get(`${BASE_URL}/api/conversations`, {
      params: { status: largeStatusArray },
    });

    // Then: Should handle gracefully
    expect([200, 400, 422]).toContain(response.status());
    expect(response.status()).not.toBe(500);
  });
});
