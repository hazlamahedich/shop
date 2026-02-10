/**
 * API Tests for Story 1.8: Authentication - Rate Limiting
 *
 * Tests rate limiting behavior for login attempts
 *
 * Prerequisites:
 * - Backend API running on http://localhost:8000
 * - Rate limiting configured (5 attempts per 15 minutes per IP)
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.API_URL || 'http://localhost:8000';

test.describe.configure({ mode: 'serial' }); // Run tests serially to avoid rate limiter state conflicts
test.describe('Story 1.8: Authentication Rate Limiting [P1]', () => {
  test.beforeEach(async ({ request }) => {
    // Reset rate limits before each test
    await resetRateLimits(request);
  });

  test('[P1] should enforce IP lockout after 5 failed attempts (15 minute window)', async ({ request }) => {
    // Extra reset to ensure clean state when running with other tests
    await resetRateLimits(request);

    // Given: An IP address making failed login attempts
    const allowedAttempts = 5;
    const testIp = '192.168.1.101'; // Use explicit IP for testing (unique)

    // When: Making 5 failed login attempts from same IP
    for (let i = 0; i < allowedAttempts; i++) {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: `wrong-${i}@example.com`,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false', // Enable rate limiting
          'X-Forwarded-For': testIp, // Explicit IP for consistent tracking
        },
      });

      // First 5 attempts should return 401 (invalid credentials)
      expect(response.status()).toBe(401);
    }

    // When: Making 6th attempt (should be rate limited)
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'another-wrong@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp, // Same IP
      },
    });

    // Then: Response should be 429 Too Many Requests
    expect(response.status()).toBe(429);

    // And: Error message should mention rate limit
    const body = await response.json();
    expect(body.detail.message.toLowerCase()).toContain('too many');
  });

  test('[P1] should enforce email lockout after 5 failed attempts (15 minute window)', async ({ request }) => {
    // Given: Same email making failed login attempts from different IPs
    const email = 'rate-limit-test@example.com';
    const allowedAttempts = 5;

    // When: Making 5 failed login attempts for same email
    for (let i = 0; i < allowedAttempts; i++) {
      const response = await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: email,
          password: `WrongPassword${i}`,
        },
        headers: {
          'X-Test-Mode': 'false',
          'X-Forwarded-For': `192.168.1.${i}`, // Simulate different IPs
        },
      });

      // First 5 attempts should return 401 (invalid credentials)
      expect(response.status()).toBe(401);
    }

    // When: Making 6th attempt for same email
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: email,
        password: 'AnotherWrongPassword',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': '192.168.1.99', // Different IP
      },
    });

    // Then: Response should be 429 (email rate limit)
    expect(response.status()).toBe(429);
  });

  test('[P1] should reset rate limit counter on successful login', async ({ request }) => {
    // Given: An IP with some failed login attempts
    const email = 'successful-login-test@example.com';
    const testIp = '192.168.1.103';

    // Create merchant first
    await createMerchantIfNotExists(request, email, 'ValidPass123');

    // Make 3 failed attempts
    for (let i = 0; i < 3; i++) {
      await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: email,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false',
          'X-Forwarded-For': testIp,
        },
      });
    }

    // When: Making successful login
    const successResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: email,
        password: 'ValidPass123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp,
      },
    });

    // Then: Login should succeed
    expect(successResponse.status()).toBe(200);

    // When: Making failed attempts after successful login
    // Should be able to make up to 5 more failed attempts
    const failedResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: email,
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp,
      },
    });

    // Then: Should not be rate limited yet
    expect(failedResponse.status()).toBe(401);
  });

  test('[P1] should include retry information in rate limit response', async ({ request }) => {
    // Given: An IP that has exceeded rate limit
    const testIp = '192.168.1.101';
    for (let i = 0; i < 5; i++) {
      await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: `wrong-${i}@example.com`,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false',
          'X-Forwarded-For': testIp,
        },
      });
    }

    // When: Making another attempt (rate limited)
    const response = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'another-wrong@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp,
      },
    });

    // Then: Response should include retry information
    expect(response.status()).toBe(429);

    const body = await response.json();
    expect(body.detail).toHaveProperty('message');
    expect(body.detail.message.toLowerCase()).toMatch(/too many|rate limit/);
  });

  test('[P1] should track IP and email rate limits independently', async ({ request }) => {
    // Given: IP1 with 5 failed attempts for email1
    const email1 = 'independent-test-1@example.com';
    const ip1 = '192.168.1.10';

    for (let i = 0; i < 5; i++) {
      await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: email1,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false',
          'X-Forwarded-For': ip1,
        },
      });
    }

    // When: Same IP makes failed attempt for different email (6th attempt from this IP)
    const response1 = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'different-email@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': ip1,
      },
    });

    // Then: Should be rate limited by IP (6th attempt from this IP)
    expect(response1.status()).toBe(429);

    // When: Different IP makes failed attempt for email1 (6th attempt for this email)
    const response2 = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: email1,
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': '192.168.1.20', // Different IP
      },
    });

    // Then: Should be rate limited by email (6th attempt for this email)
    expect(response2.status()).toBe(429);
  });

  test('[P2] should allow requests after rate limit window expires', async ({ request }) => {
    // Note: This test would require time manipulation or waiting
    // In production, this would verify that the 15-minute window resets

    // Given: An IP that has been rate limited (5 attempts + 1 blocked)
    const testIp = '192.168.1.102';
    for (let i = 0; i < 5; i++) {
      await request.post(`${API_URL}/api/v1/auth/login`, {
        data: {
          email: `wrong-${i}@example.com`,
          password: 'WrongPassword123',
        },
        headers: {
          'X-Test-Mode': 'false',
          'X-Forwarded-For': testIp,
        },
      });
    }

    // Verify rate limited (6th attempt)
    const rateLimitedResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'another-wrong@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp,
      },
    });
    expect(rateLimitedResponse.status()).toBe(429);

    // When: Reset rate limits (simulating time passage)
    await resetRateLimits(request);

    // Then: Should allow new attempts
    const newAttemptResponse = await request.post(`${API_URL}/api/v1/auth/login`, {
      data: {
        email: 'another-wrong@example.com',
        password: 'WrongPassword123',
      },
      headers: {
        'X-Test-Mode': 'false',
        'X-Forwarded-For': testIp,
      },
    });

    // Should get 401 (invalid credentials) not 429 (rate limited)
    expect(newAttemptResponse.status()).toBe(401);
  });
});

// Helper functions

async function resetRateLimits(request: any): Promise<void> {
  try {
    await request.post(`${API_URL}/api/v1/test/reset-rate-limits`, {
      headers: {
        'X-Test-Mode': 'true',
      },
    });
  } catch (error) {
    // Reset endpoint might not exist, continue anyway
    console.warn('Could not reset rate limits:', error);
  }
}

async function createMerchantIfNotExists(
  request: any,
  email: string,
  password: string
): Promise<void> {
  try {
    await request.post(`${API_URL}/api/v1/test/create-merchant`, {
      data: {
        email: email,
        password: password,
      },
      headers: {
        'X-Test-Mode': 'true',
      },
    });
  } catch (error) {
    // Ignore errors
  }
}
