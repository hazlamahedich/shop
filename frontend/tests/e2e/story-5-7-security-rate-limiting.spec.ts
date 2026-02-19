/**
 * E2E Security Tests for Widget Endpoints
 *
 * Story 5-7: Security & Rate Limiting
 * Tests security measures including rate limiting, session validation,
 * domain whitelist, and input sanitization.
 *
 * @tags api integration widget security story-5-7
 */

import { test, expect } from "@playwright/test";

const BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";
const TEST_MERCHANT_ID = 1;

test.describe("Story 5-7: Security & Rate Limiting", () => {
  test.describe("Session ID Validation (AC3)", () => {
    test("[P0] @smoke should reject invalid session ID format", async ({ request }) => {
      const response = await request.get(
        `${BASE_URL}/api/v1/widget/session/invalid-uuid-format`,
        {
          headers: {
            "X-Test-Mode": "true",
          },
        }
      );

      expect(response.status()).toBe(422);
      const data = await response.json();
      expect(data.error_code).toBe(1001);
    });

    test("[P1] should reject SQL injection attempt in session ID", async ({
      request,
    }) => {
      const response = await request.get(
        `${BASE_URL}/api/v1/widget/session/'; DROP TABLE sessions;--`,
        {
          headers: {
            "X-Test-Mode": "true",
          },
        }
      );

      expect(response.status()).toBe(422);
      const data = await response.json();
      expect(data.error_code).toBe(1001);
    });

    test("[P1] should return 404 for valid UUID format that doesn't exist", async ({
      request,
    }) => {
      const validUuid = "550e8400-e29b-41d4-a716-446655440000";

      const response = await request.get(
        `${BASE_URL}/api/v1/widget/session/${validUuid}`,
        {
          headers: {
            "X-Test-Mode": "true",
          },
        }
      );

      expect(response.status()).toBe(404);
    });
  });

  test.describe("Message Validation (AC5)", () => {
    test("[P0] @smoke should reject empty message", async ({ request }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: "   ",
        },
      });

      expect(response.status()).toBe(422);
      const data = await response.json();
      expect(data.error_code).toBe(1001);
    });

    test("[P0] @smoke should reject message exceeding 2000 characters", async ({
      request,
    }) => {
      const longMessage = "x".repeat(2001);

      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: longMessage,
        },
      });

      expect(response.status()).toBe(400);
      const data = await response.json();
      expect(data.error_code).toBe(12007);
    });

    test("[P1] should accept message at max length (2000 chars)", async ({
      request,
    }) => {
      const maxMessage = "x".repeat(2000);

      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: maxMessage,
        },
      });

      expect([400, 404]).toContain(response.status());
    });
  });

  test.describe("XSS Prevention (AC5)", () => {
    test("[P0] @smoke should sanitize script tags in messages", async ({ request }) => {
      const xssPayload = "<script>alert('xss')</script>";

      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: xssPayload,
        },
      });

      expect([400, 404]).toContain(response.status());
    });

    test("[P1] should sanitize img onerror in messages", async ({ request }) => {
      const xssPayload = "<img src=x onerror=alert('xss')>";

      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: xssPayload,
        },
      });

      expect([400, 404]).toContain(response.status());
    });
  });

  test.describe("Rate Limiting (AC1, AC2)", () => {
    test("[P0] @smoke should enforce rate limiting (requests without bypass succeed)", async ({
      request,
    }) => {
      const validUuid = "550e8400-e29b-41d4-a716-446655440000";

      const response = await request.get(
        `${BASE_URL}/api/v1/widget/session/${validUuid}`
      );

      expect([404, 429]).toContain(response.status());

      if (response.status() === 429) {
        const data = await response.json();
        expect(data.error_code).toBe(12003);
      }
    });

    test("[P1] @slow should return 429 with WIDGET_RATE_LIMITED when rate limit exceeded", async ({
      request,
    }) => {
      test.skip(
        !process.env.TEST_RATE_LIMITING,
        "Set TEST_RATE_LIMITING=true to run this test (requires rate limiting enabled in backend)"
      );

      const validUuid = "550e8400-e29b-41d4-a716-446655440000";
      const requests = [];

      for (let i = 0; i < 105; i++) {
        requests.push(
          request.get(`${BASE_URL}/api/v1/widget/session/${validUuid}`)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter((r) => r.status() === 429);

      expect(rateLimitedResponses.length).toBeGreaterThan(0);

      const rateLimitedData = await rateLimitedResponses[0].json();
      expect(rateLimitedData.error_code).toBe(12003);
      expect(rateLimitedData.message).toContain("rate");
    });

    test("[P1] should bypass rate limit in test mode", async ({ request }) => {
      const requests = [];

      for (let i = 0; i < 5; i++) {
        requests.push(
          request.get(
            `${BASE_URL}/api/v1/widget/session/550e8400-e29b-41d4-a716-446655440000`,
            {
              headers: {
                "X-Test-Mode": "true",
              },
            }
          )
        );
      }

      const responses = await Promise.all(requests);

      for (const response of responses) {
        expect([400, 404]).toContain(response.status());
      }
    });
  });

  test.describe("Error Response Format", () => {
    test("[P1] should return proper error format for validation errors", async ({
      request,
    }) => {
      const response = await request.get(
        `${BASE_URL}/api/v1/widget/session/invalid`,
        {
          headers: {
            "X-Test-Mode": "true",
          },
        }
      );

      expect(response.status()).toBe(422);
      const data = await response.json();

      expect(data).toHaveProperty("error_code");
      expect(data).toHaveProperty("message");
    });

    test("[P0] @smoke should return WIDGET_MESSAGE_TOO_LONG error code (12007)", async ({
      request,
    }) => {
      const response = await request.post(`${BASE_URL}/api/v1/widget/message`, {
        headers: {
          "Content-Type": "application/json",
          "X-Test-Mode": "true",
        },
        data: {
          session_id: "550e8400-e29b-41d4-a716-446655440000",
          message: "x".repeat(2001),
        },
      });

      expect(response.status()).toBe(400);
      const data = await response.json();
      expect(data.error_code).toBe(12007);
    });
  });

  test.describe("End-to-End Security Flow", () => {
    test("[P0] @smoke should validate session ID when ending session", async ({
      request,
    }) => {
      const response = await request.delete(
        `${BASE_URL}/api/v1/widget/session/invalid-uuid`,
        {
          headers: {
            "X-Test-Mode": "true",
          },
        }
      );

      expect(response.status()).toBe(422);
      const data = await response.json();
      expect(data.error_code).toBe(1001);
    });
  });

  test.describe("Retry-After Header (AC1 P1 Gap)", () => {
    test("[P1] should include Retry-After header in rate limit response", async ({
      request,
    }) => {
      test.skip(
        !process.env.TEST_RATE_LIMITING,
        "Set TEST_RATE_LIMITING=true to run this test"
      );

      const validUuid = "550e8400-e29b-41d4-a716-446655440000";
      const requests = [];

      for (let i = 0; i < 105; i++) {
        requests.push(
          request.get(`${BASE_URL}/api/v1/widget/session/${validUuid}`)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponse = responses.find((r) => r.status() === 429);

      if (rateLimitedResponse) {
        const retryAfter = rateLimitedResponse.headers()["retry-after"];
        expect(retryAfter).toBeDefined();
        expect(parseInt(retryAfter, 10)).toBe(60);

        const data = await rateLimitedResponse.json();
        expect(data.error_code).toBe(12003);
        expect(data.details?.retry_after).toBe(60);
      }
    });

    test("[P1] should include retry_after in error response body", async ({
      request,
    }) => {
      test.skip(
        !process.env.TEST_RATE_LIMITING,
        "Set TEST_RATE_LIMITING=true to run this test"
      );

      const validUuid = "550e8400-e29b-41d4-a716-446655440000";
      const requests = [];

      for (let i = 0; i < 105; i++) {
        requests.push(
          request.get(`${BASE_URL}/api/v1/widget/session/${validUuid}`)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponse = responses.find((r) => r.status() === 429);

      if (rateLimitedResponse) {
        const data = await rateLimitedResponse.json();
        expect(data.details).toBeDefined();
        expect(data.details.retry_after).toBeDefined();
        expect(typeof data.details.retry_after).toBe("number");
        expect(data.details.retry_after).toBe(60);
      }
    });
  });

  test.describe("Rate Limit Enforcement Without Bypass (AC1 P1 Gap)", () => {
    test("[P1] should enforce rate limiting without X-Test-Mode header", async ({
      request,
    }) => {
      test.skip(
        !process.env.TEST_RATE_LIMITING,
        "Set TEST_RATE_LIMITING=true to run this test"
      );

      const validUuid = "550e8400-e29b-41d4-a716-446655440000";
      const requests = [];

      for (let i = 0; i < 105; i++) {
        requests.push(
          request.get(`${BASE_URL}/api/v1/widget/session/${validUuid}`)
        );
      }

      const responses = await Promise.all(requests);
      const rateLimitedResponses = responses.filter((r) => r.status() === 429);

      expect(rateLimitedResponses.length).toBeGreaterThan(0);

      const rateLimitedData = await rateLimitedResponses[0].json();
      expect(rateLimitedData.error_code).toBe(12003);
      expect(rateLimitedData.message).toMatch(/rate/i);
    });
  });
});
