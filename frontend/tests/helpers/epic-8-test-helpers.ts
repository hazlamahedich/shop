/**
 * Shared test utilities for Epic 8: General Chatbot Mode.
 * 
 * Story 8-9: Testing & Quality Assurance
 * Task 9.2: Create frontend/tests/helpers/epic-8-test-helpers.ts
 */

import { Page, expect } from '@playwright/test';

/**
 * Setup a merchant with General mode and mock requirements.
 */
export async function setupGeneralModeMerchant(page: Page): Promise<void> {
  // Assuming we use a common login/onboarding flow
  // In E2E tests, we often use mocks for the initial state
  
  // 1. Mock the initial merchant profile to be in General mode
  await page.route('**/api/merchant/profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: {
          id: 1,
          merchant_key: 'test-merchant',
          onboarding_mode: 'general',
          business_name: 'Test Business',
          bot_name: 'General Assistant'
        }
      })
    });
  });
}

/**
 * Mock Knowledge Base document list.
 */
export async function mockDocumentList(page: Page, documents: any[]): Promise<void> {
  await page.route('**/api/knowledge-base/list', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        data: documents
      })
    });
  });
}

/**
 * Wait for a document to reach a specific status in the UI.
 */
export async function waitForDocumentStatus(
  page: Page,
  filename: string,
  status: string
): Promise<void> {
  const row = page.locator('tr', { hasText: filename });
  await expect(row.locator(`text=${status}`)).toBeVisible({ timeout: 10000 });
}

/**
 * Navigate to Knowledge Base page and verify visibility.
 */
export async function navigateToKnowledgeBase(page: Page): Promise<void> {
  await page.click('nav >> text=Knowledge Base');
  await expect(page).toHaveURL(/.*knowledge-base/);
  await expect(page.locator('h1')).toContainText('Knowledge Base');
}
