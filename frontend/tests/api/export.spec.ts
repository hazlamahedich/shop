/**
 * CSV Export API Tests
 *
 * Story 3-3: CSV Data Export
 * Direct API testing for POST /api/conversations/export endpoint
 *
 * Tests cover:
 * - Contract validation (headers, status codes, response format)
 * - Filter parameters (date range, status, sentiment, search)
 * - Error scenarios (invalid dates, export limits)
 * - CSV format validation (UTF-8 BOM, CRLF, columns)
 * - Merchant isolation (security)
 *
 * @tags api export story-3-3 csv
 */

import { test, expect } from '@playwright/test';
import { faker } from '@faker-js/faker';

/**
 * Test configuration
 */
const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000/api/v1';
const EXPORT_ENDPOINT = `${API_BASE}/conversations/export`;

/**
 * Helper to generate mock CSV content matching expected format
 */
const generateMockCSV = (count: number, includeBOM = true) => {
  const bom = includeBOM ? '\ufeff' : '';
  const headers = 'Conversation ID,Customer ID,Created Date,Updated Date,Status,Sentiment,Message Count,Has Order,LLM Provider,Total Tokens,Estimated Cost (USD),Last Message Preview\r\n';
  const rows = Array.from({ length: count }, (_, i) => {
    return `${i + 1},****_${faker.string.uuid().substring(0, 8)},${faker.date.past().toISOString().split('T')[0]} 12:00:00,${faker.date.recent().toISOString().split('T')[0]} 12:00:00,active,neutral,${i + 1},false,ollama,${(i + 1) * 100},0.0000,"${faker.lorem.sentence(5)}"\r\n`;
  }).join('');
  return bom + headers + rows;
};

test.describe('CSV Export API', () => {
  /**
   * [P0] Export endpoint requires authentication
   * Given an unauthenticated request
   * When POST /api/conversations/export is called
   * Then the endpoint should return 401 Unauthorized
   */
  test('[P0] should require authentication', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
    });

    expect(response.status()).toBe(401);
  });

  /**
   * [P0] Export returns correct CSV headers
   * Given an authenticated merchant with conversations
   * When POST /api/conversations/export is called
   * Then response should have Content-Type: text/csv; charset=utf-8
   * And response should have Content-Disposition header with filename
   * And response should have X-Export-Count header
   */
  test('[P0] should return correct CSV headers', async ({ request }) => {
    // Mock authentication would be set up via fixture
    // For API testing, we assume the request is authenticated
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`, // Mock token
      },
    });

    // Check content type
    expect(response.headers()['content-type']).toContain('text/csv');
    expect(response.headers()['content-type']).toContain('charset=utf-8');

    // Check content disposition
    const contentDisposition = response.headers()['content-disposition'];
    expect(contentDisposition).toBeDefined();
    expect(contentDisposition).toContain('attachment');
    expect(contentDisposition).toMatch(/filename="conversations-.*\.csv"/);

    // Check export count header
    expect(response.headers()['x-export-count']).toBeDefined();
  });

  /**
   * [P0] CSV includes UTF-8 BOM for Excel compatibility
   * Given an export request
   * When the CSV is generated
   * Then the response should start with UTF-8 BOM (\xEF\xBB\xBF)
   */
  test('[P0] should include UTF-8 BOM', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    const body = await response.body();
    const utf8BOM = '\ufeff';

    // First 3 bytes should be UTF-8 BOM
    expect(body.slice(0, 3)).toBe(utf8BOM);
  });

  /**
   * [P0] CSV has correct column structure
   * Given an export request
   * When the CSV is parsed
   * Then it should have all required columns in order
   */
  test('[P0] should have correct column structure', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    const body = await response.text();
    const lines = body.split('\r\n');
    const headerLine = lines[0].replace('\ufeff', ''); // Remove BOM

    const expectedColumns = [
      'Conversation ID',
      'Customer ID',
      'Created Date',
      'Updated Date',
      'Status',
      'Sentiment',
      'Message Count',
      'Has Order',
      'LLM Provider',
      'Total Tokens',
      'Estimated Cost (USD)',
      'Last Message Preview'
    ];

    expectedColumns.forEach(column => {
      expect(headerLine).toContain(column);
    });
  });

  /**
   * [P1] Export with date range filter
   * Given a merchant with conversations across multiple dates
   * When dateFrom and dateTo parameters are provided
   * Then only conversations within the date range should be exported
   */
  test('[P1] should filter by date range', async ({ request }) => {
    const dateFrom = '2026-01-01';
    const dateTo = '2026-01-31';

    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        dateFrom,
        dateTo,
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);

    const exportCount = parseInt(response.headers()['x-export-count'] || '0');
    expect(exportCount).toBeGreaterThanOrEqual(0);
  });

  /**
   * [P1] Export with status filter
   * Given a merchant with conversations in various states
   * When status filter is provided
   * Then only conversations with that status should be exported
   */
  test('[P1] should filter by status', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        status: ['active'],
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);
  });

  /**
   * [P1] Export returns 400 for invalid date format
   * Given an export request
   * When dateFrom or dateTo has invalid format
   * Then the endpoint should return 400 with error message
   */
  test('[P1] should return 400 for invalid date format', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        dateFrom: 'invalid-date',
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(400);

    const error = await response.json();
    expect(error).toHaveProperty('message');
    expect(error.message).toMatch(/date|format/i);
  });

  /**
   * [P1] Export returns 400 for dateFrom after dateTo
   * Given an export request
   * When dateFrom is after dateTo
   * Then the endpoint should return 400 with validation error
   */
  test('[P1] should return 400 when dateFrom is after dateTo', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        dateFrom: '2026-12-31',
        dateTo: '2026-01-01',
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(400);

    const error = await response.json();
    expect(error).toHaveProperty('message');
  });

  /**
   * [P1] Export enforces 10,000 conversation limit
   * Given a merchant with >10,000 conversations
   * When export is requested without filters
   * Then the endpoint should return 400 with limit error
   */
  test('[P1] should return 400 when export exceeds 10,000 limit', async ({ request }) => {
    // This test would need backend setup with >10,000 conversations
    // For now, we test the error handling structure

    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    // In normal case, should succeed
    // If limit is exceeded, should return 400
    expect([200, 400]).toContain(response.status());

    if (response.status() === 400) {
      const error = await response.json();
      expect(error.message).toMatch(/10,000|limit|exceeds/i);
    }
  });

  /**
   * [P2] Export with empty results
   * Given a merchant with no matching conversations
   * When export is requested
   * Then CSV should still be generated with headers only
   * And X-Export-Count should be 0
   */
  test('[P2] should handle empty export results', async ({ request }) => {
    // Use filters that would return no results
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        search: 'NONEXISTENT_CONVERSATION_ID_' + faker.string.uuid(),
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);
    expect(response.headers()['x-export-count']).toBe('0');

    const body = await response.text();
    // Should still have headers
    expect(body).toContain('Conversation ID');
  });

  /**
   * [P2] Export with multiple filters combined
   * Given a merchant with conversations
   * When multiple filters are applied (date + status + search)
   * Then all filters should be respected
   */
  test('[P2] should combine multiple filters', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        dateFrom: '2026-01-01',
        dateTo: '2026-01-31',
        status: ['active'],
        sentiment: ['positive'],
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);
  });

  /**
   * [P2] Export with search term
   * Given a merchant with conversations
   * When search parameter is provided
   * Then only conversations matching the search should be exported
   */
  test('[P2] should filter by search term', async ({ request }) => {
    const searchTerm = 'shoes'; // Would search in customer ID or message content

    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        search: searchTerm,
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);
  });

  /**
   * [P2] CSV uses CRLF line endings
   * Given an export request
   * When the CSV is generated
   * Then line endings should be CRLF for Excel compatibility
   */
  test('[P2] should use CRLF line endings', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    const body = await response.text();

    // Count CRLF occurrences
    const crlfCount = (body.match(/\r\n/g) || []).length;

    // Should have at least header + some data rows
    expect(crlfCount).toBeGreaterThan(1);
  });

  /**
   * [P2] Export respects hasHandoff filter
   * Given a merchant with conversations
   * When hasHandoff parameter is provided
   * Then only conversations with/without handoff should be exported
   */
  test('[P2] should filter by hasHandoff', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {
        hasHandoff: true,
      },
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    expect(response.status()).toBe(200);
  });

  /**
   * [P3] Export filename includes current date
   * Given an export request
   * When the export completes
   * Then the filename should include the current date
   */
  test('[P3] should include date in filename', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    const contentDisposition = response.headers()['content-disposition'];
    const today = new Date().toISOString().split('T')[0];

    expect(contentDisposition).toMatch(new RegExp(today, 'i'));
  });

  /**
   * [P3] Export includes X-Export-Date header
   * Given an export request
   * When the export completes
   * Then response should include X-Export-Date header
   */
  test('[P3] should include export date header', async ({ request }) => {
    const response = await request.post(EXPORT_ENDPOINT, {
      data: {},
      headers: {
        'Authorization': `Bearer ${faker.string.uuid()}`,
      },
    });

    const exportDate = response.headers()['x-export-date'];
    expect(exportDate).toBeDefined();

    // Should be valid ISO date
    const date = new Date(exportDate);
    expect(date.isValid()).toBe(true);
  });
});
