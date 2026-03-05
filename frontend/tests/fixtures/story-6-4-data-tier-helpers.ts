/**
 * Story 6-4 Test Fixtures and Helpers
 * Shared utilities for data tier separation tests
 */

import { Page, APIRequestContext } from '@playwright/test';
import { faker } from '@faker-js/faker';

/**
 * Data Tier Types
 */
export type DataTier = 'voluntary' | 'operational' | 'anonymized';

/**
 * Create test conversation via API
 */
export async function createTestConversation(
  request: APIRequestContext,
  merchantId: number,
  tier: DataTier,
  overrides: Record<string, any> = {}
) {
  const response = await request.post('/api/v1/test/conversations', {
    data: {
      merchantId,
      platformSenderId: faker.string.uuid(),
      dataTier: tier,
      status: 'active',
      ...overrides,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to create test conversation: ${response.status()}`);
  }

  return response.json();
}

/**
 * Create test order via API
 */
export async function createTestOrder(
  request: APIRequestContext,
  merchantId: number,
  tier: DataTier,
  overrides: Record<string, any> = {}
) {
  const response = await request.post('/api/v1/test/orders', {
    data: {
      merchantId,
      orderNumber: `ORD-TEST-${Date.now()}`,
      platformSenderId: faker.string.uuid(),
      total: faker.number.float({ min: 10, max: 500 }),
      isTest: true,
      dataTier: tier,
      ...overrides,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to create test order: ${response.status()}`);
  }

  return response.json();
}

/**
 * Create test consent record via API
 */
export async function createTestConsent(
  request: APIRequestContext,
  merchantId: number,
  sessionId: string,
  granted: boolean = true,
  overrides: Record<string, any> = {}
) {
  const response = await request.post('/api/v1/test/consent', {
    data: {
      merchantId,
      sessionId,
      consentType: 'conversation',
      granted,
      ...overrides,
    },
  });

  if (!response.ok()) {
    throw new Error(`Failed to create test consent: ${response.status()}`);
  }

  return response.json();
}

/**
 * Helper: Login as merchant
 */
export async function loginAsMerchant(page: Page, merchantId: number = 1) {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', `merchant${merchantId}@example.com`);
  await page.fill('[data-testid="password"]', 'testpassword123');
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}

/**
 * Helper: Wait for analytics summary API response
 */
export async function waitForAnalyticsSummary(page: Page) {
  const response = await page.waitForResponse('**/api/v1/analytics/summary');
  return response.json();
}

/**
 * Helper: Verify tier distribution widget visible
 */
export async function verifyTierWidgetVisible(page: Page) {
  const tierWidget = page.getByTestId('tier-distribution-widget');
  await tierWidget.waitFor({ state: 'visible' });
  return tierWidget;
}

/**
 * Helper: Get tier count from widget
 */
export async function getTierCount(page: Page, tier: DataTier): Promise<number> {
  const tierWidget = await verifyTierWidgetVisible(page);
  const countElement = tierWidget.getByTestId(`${tier}-count`);
  const countText = await countElement.textContent();
  return parseInt(countText || '0', 10);
}

/**
 * Helper: Trigger consent opt-out
 */
export async function triggerConsentOptOut(page: Page, sessionId: string) {
  const consentCard = page.getByTestId(`consent-${sessionId}`);
  await consentCard.waitFor({ state: 'visible' });

  const optOutButton = consentCard.getByTestId('opt-out-button');
  await optOutButton.click();

  // Confirm opt-out dialog
  await page.getByText(/Are you sure/).waitFor({ state: 'visible' });
  await page.click('[data-testid="confirm-opt-out"]');

  // Wait for API response
  await page.waitForResponse('**/api/v1/consent/opt-out');
}

/**
 * Helper: Verify tier changed in UI
 */
export async function verifyTierChanged(
  page: Page,
  sessionId: string,
  expectedTier: DataTier,
  timeout: number = 5000
) {
  const consentCard = page.getByTestId(`consent-${sessionId}`);
  const tierText = expectedTier.charAt(0).toUpperCase() + expectedTier.slice(1);

  await consentCard.getByText(new RegExp(tierText, 'i')).waitFor({
    state: 'visible',
    timeout,
  });
}

/**
 * Helper: Create conversation with PII (for anonymization tests)
 */
export async function createConversationWithPII(
  request: APIRequestContext,
  merchantId: number
) {
  const piiEmail = `user-${Date.now()}@example.com`;
  const conversation = await createTestConversation(request, merchantId, 'voluntary', {
    platformSenderId: piiEmail, // PII field
  });

  return { conversation, piiEmail };
}

/**
 * Helper: Verify no PII in response
 */
export function verifyNoPII(data: any, piiFields: string[]): void {
  const dataString = JSON.stringify(data);
  for (const field of piiFields) {
    if (dataString.includes(field)) {
      throw new Error(`PII found in response: ${field}`);
    }
  }
}

/**
 * Helper: Mock analytics API failure
 */
export async function mockAnalyticsFailure(page: Page) {
  await page.route('**/api/v1/analytics/summary', (route) => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Internal Server Error' }),
    });
  });
}

/**
 * Helper: Create multi-merchant test data
 */
export async function createMultiMerchantData(
  request: APIRequestContext,
  merchantIds: number[]
) {
  const conversations = [];

  for (const merchantId of merchantIds) {
    const conv = await createTestConversation(request, merchantId, 'voluntary');
    conversations.push(conv);
  }

  return conversations;
}
