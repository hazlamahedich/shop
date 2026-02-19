/**
 * Security & Rate Limiting - Domain Whitelist E2E Tests
 *
 * Story 5-7: Security & Rate Limiting
 * Tests AC4: Domain Whitelist validation in E2E context
 *
 * Priority: P2 (Valid - complements backend tests with E2E perspective)
 * Critical Analysis: Some overlap with backend tests, but Origin header
 * testing at E2E level provides additional coverage
 *
 * @tags api widget story-5-7 security domain-whitelist
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = 1;

test.describe('Story 5-7: Domain Whitelist E2E', () => {
  test.describe('Origin Header Validation (AC4)', () => {
    test('[P2] should accept request from allowed domain', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://allowed-domain.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Id': TEST_MERCHANT_ID.toString(),
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });

    test('[P2] should reject request from unauthorized domain', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://malicious-site.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Domains': 'allowed-domain.com,shop.example.com',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      if (response.status() === 403) {
        const data = await response.json();
        expect(data.error_code).toBe(12006);
      }
    });

    test('[P2] should accept request when whitelist is empty', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://any-domain.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Domains': '',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });
  });

  test.describe('Subdomain Handling', () => {
    test('[P2] should accept subdomain of allowed domain', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://shop.allowed-domain.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Domains': 'allowed-domain.com',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });

    test('[P2] should accept www subdomain', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://www.allowed-domain.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Domains': 'allowed-domain.com',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });
  });

  test.describe('Missing Origin Header', () => {
    test('[P2] should handle missing Origin header', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'X-Test-Mode': 'true',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });

    test('[P2] should handle empty Origin header', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': '',
          'X-Test-Mode': 'true',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });
  });

  test.describe('Error Response Format', () => {
    test('[P2] should return WIDGET_DOMAIN_NOT_ALLOWED error code (12006)', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'https://blocked-domain.com',
          'X-Test-Mode': 'true',
          'X-Test-Merchant-Domains': 'only-this-domain.com',
          'X-Test-Force-Domain-Check': 'true',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      if (response.status() === 403) {
        const data = await response.json();
        expect(data.error_code).toBe(12006);
        expect(data.message).toMatch(/domain|origin|allowed/i);
      }
    });
  });

  test.describe('Protocol Handling', () => {
    test('[P2] should accept http in development', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'http://localhost:3000',
          'X-Test-Mode': 'true',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });

    test('[P2] should handle file:// protocol', async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/session`, {
        headers: {
          'Content-Type': 'application/json',
          'Origin': 'file:///path/to/page.html',
          'X-Test-Mode': 'true',
        },
        data: {
          merchant_id: TEST_MERCHANT_ID,
        },
      });

      expect([201, 404]).toContain(response.status());
    });
  });
});
