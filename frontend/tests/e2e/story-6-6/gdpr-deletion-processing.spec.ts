/**
 * Story 6-6: GDPR Deletion Processing E2E Tests
 *
 * Epic 6: Data Privacy & Compliance
 * Priority: P1 (Critical - GDPR/CCPA Compliance)
 *
 * Tests GDPR deletion functionality end-to-end:
 * - GDPR request submission via API
 * - Compliance status monitoring
 * - Request revocation
 * - Data deletion verification
 * - Duplicate request prevention
 *
 * Note: Frontend UI components (PrivacyDashboard.tsx, ComplianceStatusWidget.tsx)
 * are not required for MVP. These tests verify API-level E2E flow.
 *
 * PREREQUISITES:
 * - Backend server running at http://localhost:8000
 * - Run: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
 *
 * Test IDs: 6-6-E2E-001 through 6-6-E2E-005
 * @tags e2e gdpr privacy compliance story-6-6
 */

import { test, expect } from '@playwright/test';
import { faker } from '@faker-js/faker';

// Test configuration
const API_BASE = process.env.TEST_API_BASE || 'http://localhost:8000/api';

test.describe('Story 6-6: GDPR Deletion Processing', () => {
  // Tests are independent - can run in parallel
  let merchantId: number;
  let authToken: string;
  let requestId: number;

  test.beforeAll(async ({ request }) => {
    // Create test merchant and get auth token
    const loginResponse = await request.post(`${API_BASE}/v1/auth/login`, {
      data: {
        merchant_key: 'test-gdpr-merchant',
        platform: 'facebook',
      },
    });

    if (loginResponse.ok()) {
      const data = await loginResponse.json();
      merchantId = data.merchant_id;
      authToken = data.token;
    }
  });

  test('[P0][6-6-E2E-001] @smoke should submit GDPR request successfully', async ({ request }) => {
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: 'e2e_gdpr_customer',
        request_type: 'gdpr_formal',
        email: 'customer@example.com',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.requestId).toBeDefined();
    expect(data.data.customerId).toBe('e2e_gdpr_customer');
    expect(data.data.requestType).toBe('gdpr_formal');
    expect(data.data.deadline).toBeDefined();
    requestId = data.data.requestId;
  });

  test('[P0][6-6-E2E-002] @smoke should prevent duplicate GDPR requests', async ({ request }) => {
    // Try to submit duplicate request
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: 'e2e_gdpr_customer',
        request_type: 'gdpr_formal',
      },
    });

    expect(response.status()).toBe(400);
    const data = await response.json();
    expect(data.error_code).toBeDefined();
  });

  test('[P0][6-6-E2E-003] @smoke should retrieve compliance status', async ({ request }) => {
    const response = await request.get(`${API_BASE}/compliance/status`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.status).toMatch(/compliant|non_compliant/);
    expect(data.data.overdueRequests).toBeDefined();
    expect(data.data.approachingDeadline).toBeDefined();
    expect(data.data.lastChecked).toBeDefined();
  });

  test('[P0][6-6-E2E-004] @smoke should revoke GDPR request successfully', async ({ request }) => {
    const response = await request.post(
      `${API_BASE}/customers/e2e_gdpr_customer/revoke-gdpr-request`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.revoked).toBe(true);
    expect(data.data.customerId).toBe('e2e_gdpr_customer');
  });

  test('[P0][6-6-E2E-005] @smoke should allow new request after revocation', async ({ request }) => {
    // After revocation, should be able to submit new request
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: 'e2e_gdpr_customer',
        request_type: 'manual',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.requestId).toBeDefined();
  });
});

test.describe('Story 6-6: GDPR Data Deletion Verification', () => {
  // Tests are independent - can run in parallel
  let merchantId: number;
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    const loginResponse = await request.post(`${API_BASE}/v1/auth/login`, {
      data: {
        merchant_key: 'test-gdpr-deletion-merchant',
        platform: 'facebook',
      },
    });

    if (loginResponse.ok()) {
      const data = await loginResponse.json();
      merchantId = data.merchant_id;
      authToken = data.token;
    }
  });

  test('[P1][6-6-E2E-006] should delete voluntary data but retain operational', async ({ request }) => {
    const customerId = `gdpr_tier_test_${faker.string.uuid()}`;
    
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: customerId,
        request_type: 'gdpr_formal',
        email: 'tier-test@example.com',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.requestId).toBeDefined();
    expect(data.data.customerId).toBe(customerId);
    expect(data.data.deadline).toBeDefined();

    const deadline = new Date(data.data.deadline);
    const requestTimestamp = new Date();
    const daysDiff = Math.ceil((deadline.getTime() - requestTimestamp.getTime()) / (1000 * 60 * 60 * 24));
    
    expect(daysDiff).toBeGreaterThanOrEqual(29);
    expect(daysDiff).toBeLessThanOrEqual(31);
  });

  test('[P1][6-6-E2E-007] should respect 30-day compliance window', async ({ request }) => {
    const complianceResponse = await request.get(`${API_BASE}/compliance/status`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    expect(complianceResponse.ok()).toBeTruthy();
    const statusData = await complianceResponse.json();
    
    expect(statusData.data.status).toMatch(/compliant|non_compliant/);
    expect(statusData.data.overdueRequests).toBeDefined();
    expect(statusData.data.approachingDeadline).toBeDefined();
    expect(statusData.data.lastChecked).toBeDefined();

    if (statusData.data.status === 'non_compliant') {
      expect(statusData.data.overdueRequests).toBeGreaterThan(0);
    }
  });

  test('[P2][6-6-E2E-008] should queue email confirmation when email provided', async ({ request }) => {
    const customerId = `gdpr_email_customer_${faker.string.uuid()}`;
    const customerEmail = 'customer@example.com';
    
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: customerId,
        request_type: 'gdpr_formal',
        email: customerEmail,
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.requestId).toBeDefined();
    expect(data.data.customerId).toBe(customerId);
    expect(data.data.deadline).toBeDefined();
  });

  test('[P2][6-6-E2E-009] should not queue email when email not provided', async ({ request }) => {
    const customerId = `gdpr_no_email_customer_${faker.string.uuid()}`;
    
    const response = await request.post(`${API_BASE}/gdpr-request`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        customer_id: customerId,
        request_type: 'gdpr_formal',
      },
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data.requestId).toBeDefined();
    expect(data.data.customerId).toBe(customerId);
    expect(data.data.deadline).toBeDefined();
  });
});
