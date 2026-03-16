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

/**
 * Set a value in localStorage using addInitScript with proper variable interpolation.
 *
 * CRITICAL: Playwright's addInitScript runs in browser context.
 * Template literals like `${value}` won't interpolate - pass values as 2nd argument.
 *
 * @param page - Playwright Page object
 * @param key - localStorage key
 * @param value - Value to store (will be JSON.stringified)
 *
 * @example
 * // ✅ CORRECT - Pass value as 2nd argument
 * await setLocalStorageValue(page, 'onboardingMode', 'general');
 *
 * @example
 * // ❌ WRONG - Template literal won't work
 * await page.addInitScript(() => {
 *   localStorage.setItem('mode', `${mode}`); // mode is undefined in browser!
 * });
 */
export async function setLocalStorageValue(page: Page, key: string, value: unknown): Promise<void> {
  await page.addInitScript(
    ({ key, value }) => {
      localStorage.setItem(key, JSON.stringify(value));
    },
    { key, value }
  );
}

/**
 * Set multiple localStorage values using addInitScript.
 *
 * @param page - Playwright Page object
 * @param values - Object with key-value pairs to store
 *
 * @example
 * await setLocalStorageValues(page, {
 *   onboardingMode: 'general',
 *   merchantId: 123,
 *   token: 'abc123'
 * });
 */
export async function setLocalStorageValues(page: Page, values: Record<string, unknown>): Promise<void> {
  await page.addInitScript(
    (values) => {
      Object.entries(values).forEach(([key, value]) => {
        localStorage.setItem(key, JSON.stringify(value));
      });
    },
    values
  );
}

/**
 * Mock a global variable in the browser window using addInitScript.
 *
 * @param page - Playwright Page object
 * @param key - Window property name
 * @param value - Value to assign
 *
 * @example
 * await setWindowValue(page, '__TEST_MERCHANT_ID__', 123);
 */
export async function setWindowValue(page: Page, key: string, value: unknown): Promise<void> {
  await page.addInitScript(
    ({ key, value }) => {
      (window as Record<string, unknown>)[key] = value;
    },
    { key, value }
  );
}
