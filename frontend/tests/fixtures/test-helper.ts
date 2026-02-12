/**
 * E2E Test Helpers
 *
 * Common utilities for Playwright E2E tests
 */

import { Page, Locator } from '@playwright/test';

export const mockSelectors = {
  // Prerequisite Checklist
  prerequisiteChecklist: '[data-testid="prerequisite-checklist"]',
  cloudAccountCheckbox: '[data-testid="checkbox-cloudAccount"]',
  facebookAccountCheckbox: '[data-testid="checkbox-facebookAccount"]',
  shopifyAccessCheckbox: '[data-testid="checkbox-shopifyAccess"]',
  llmProviderCheckbox: '[data-testid="checkbox-llmProviderChoice"]',
  deployButton: '[data-testid="deploy-button"]',

  // Deployment Wizard
  deploymentWizard: '[data-testid="deployment-wizard"]',
  deploymentStatus: '[data-testid="deployment-status"]',

  // Facebook Connection
  facebookConnection: '[data-testid="facebook-connection"]',
  facebookStatus: '[data-testid="facebook-connection-status"]',

  // Shopify Connection
  shopifyConnection: '[data-testid="shopify-connection"]',
  shopifyStatus: '[data-testid="shopify-connection-status"]',

  // LLM Configuration
  llmConfiguration: '[data-testid="llm-configuration"]',
  ollamaOption: '[data-testid="ollama-option"]',
  cloudOption: '[data-testid="cloud-option"]',
  testConnectionButton: '[data-testid="test-connection-button"]',
};

/**
 * Wait for API response to avoid race conditions
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp) {
  return await page.waitForResponse(
    (response) =>
      response.url().match(urlPattern) && response.status() === 200
  );
}

/**
 * Clear localStorage between tests
 *
 * Uses page.context().clearCookies() and addInitScript for more reliable clearing.
 */
export async function clearStorage(page: Page) {
  // Clear all cookies (more reliable than localStorage access)
  await page.context().clearCookies();

  // Also clear localStorage using addInitScript which runs before page load
  await page.addInitScript(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Mock external service responses
 */
export const mockResponses = {
  facebook: {
    verifyToken: 'verified',
    pageId: 'mock-page-123',
    pageName: 'Mock Test Page',
  },
  shopify: {
    storeUrl: 'test-store.myshopify.com',
    accessToken: 'mock-access-token',
  },
  ollama: {
    status: 'connected',
    models: ['llama3', 'mistral'],
  },
};

/**
 * Complete prerequisite checklist
 */
export async function completePrerequisites(page: Page) {
  await page.click(mockSelectors.cloudAccountCheckbox);
  await page.click(mockSelectors.facebookAccountCheckbox);
  await page.click(mockSelectors.shopifyAccessCheckbox);
  await page.click(mockSelectors.llmProviderCheckbox);

  // Verify deploy button is enabled
  const deployButton = page.locator(mockSelectors.deployButton);
  // Note: expect is available in test context, not here
  // Tests should verify the button state separately
}
