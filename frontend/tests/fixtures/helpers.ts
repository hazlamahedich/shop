/**
 * Test Helper Utilities
 *
 * Provides reusable helper functions for common testing patterns
 * including network-first waiting, retry logic, and assertions.
 *
 * Usage:
 *   import { waitForApiResponse, waitForElementState } from '../fixtures/helpers';
 *
 * @tags helpers test-utilities
 */

import { Page, expect, APIResponse } from '@playwright/test';

// ============================================================
// Network-First Helpers
// ============================================================

/**
 * Wait for an API response with URL pattern matching
 * @param page - Playwright Page object
 * @param urlPattern - URL pattern to match (partial or regex string)
 * @param timeout - Optional timeout in milliseconds (default: 5000)
 * @returns Promise that resolves when matching API response completes
 */
export const waitForApiResponse = async (
  page: Page,
  urlPattern: string,
  timeout: number = 5000
): Promise<APIResponse> => {
  return page.waitForResponse(
    (response) => {
      const url = response.url();
      return url.includes(urlPattern) && response.ok();
    },
    { timeout }
  );
};

/**
 * Wait for API response with specific status code
 * @param page - Playwright Page object
 * @param urlPattern - URL pattern to match
 * @param status - Expected HTTP status code
 * @returns Promise that resolves when response with status is received
 */
export const waitForApiResponseWithStatus = async (
  page: Page,
  urlPattern: string,
  status: number
): Promise<APIResponse> => {
  return page.waitForResponse(
    (response) =>
      response.url().includes(urlPattern) && response.status() === status,
    { timeout: 5000 }
  );
};

/**
 * Setup API request interception for mocking
 * @param page - Playwright Page object
 * @param urlPattern - URL pattern to intercept
 * @param mockResponse - Mock response function
 * @returns Route object for cleanup
 */
export const mockApiResponse = async (
  page: Page,
  urlPattern: string | RegExp,
  mockResponse: (request: any) => void
): Promise<void> => {
  await page.route(urlPattern, (route) => {
    mockResponse(route);
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ success: true }),
    });
  });
};

/**
 * Setup API error mock
 * @param page - Playwright Page object
 * @param urlPattern - URL pattern to intercept
 * @param errorCode - Error code to return
 * @param errorMessage - Error message
 * @returns Route object for cleanup
 */
export const mockApiError = async (
  page: Page,
  urlPattern: string | RegExp,
  errorCode: number,
  errorMessage: string
): Promise<void> => {
  await page.route(urlPattern, (route) => {
    route.fulfill({
      status: 400,
      contentType: 'application/json',
      body: JSON.stringify({
        error: errorMessage,
        error_code: errorCode,
      }),
    });
  });
};

// ============================================================
// Element State Helpers
// ============================================================

/**
 * Wait for element to be visible and stable
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @param timeout - Optional timeout in milliseconds
 * @returns Promise resolving to element handle
 */
export const waitForElementVisible = async (
  page: Page,
  selector: string,
  timeout: number = 5000
 Promise<any> => {
  return page.waitForSelector(selector, { state: 'visible', timeout });
};

/**
 * Wait for element to be hidden
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @param timeout - Optional timeout in milliseconds
 * @returns Promise resolving when hidden
 */
export const waitForElementHidden = async (
  page: Page,
  selector: string,
  timeout: number = 5000
): Promise<void> => {
  await page.waitForSelector(selector, { state: 'hidden', timeout });
};

/**
 * Wait for element to reach stable state (not animating)
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @returns Promise resolving when stable
 */
export const waitForElementStable = async (
  page: Page,
  selector: string
): Promise<void> => {
  const element = page.locator(selector);
  await element.waitFor({ state: 'stable' });
};

/**
 * Check if element exists in DOM
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @returns true if element exists
 */
export const elementExists = async (
  page: Page,
  selector: string
): Promise<boolean> => {
  const count = await page.locator(selector).count();
  return count > 0;
};

// ============================================================
// Retry Helpers
// ============================================================

/**
 * Retry a function with exponential backoff
 * @param fn - Function to retry
 * @param maxRetries - Maximum number of retries
 * @param delay - Initial delay in milliseconds
 * @returns Promise resolving to function result
 */
export const retryWithBackoff = async <T>(
  fn: () => Promise,
  maxRetries: number = 3,
  delay: number = 100
): Promise<T> => {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
    }
  }

  throw lastError;
};

/**
 * Retry until condition is met
 * @param condition - Function returning boolean
 * @param timeout - Maximum time to wait in milliseconds
 * @param interval - Check interval in milliseconds
 * @returns Promise resolving when condition is true
 */
export const waitForCondition = async (
  condition: () => boolean | Promise<boolean>,
  timeout: number = 5000,
  interval: number = 100
): Promise<void> => {
  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    if (await condition()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`Condition not met within ${timeout}ms`);
};

// ============================================================
// Form Interaction Helpers
// ============================================================

/**
 * Fill a form field with clear and type
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @param value - Value to fill
 */
export const fillField = async (
  page: Page,
  selector: string,
  value: string
): Promise<void> => {
  const element = page.locator(selector);
  await element.clear();
  await element.fill(value);
};

/**
 * Clear a form field
 * @param page - Playwright Page object
 * @param selector - Element selector
 */
export const clearField = async (
  page: Page,
  selector: string
): Promise<void> => {
  await page.locator(selector).clear();
};

/**
 * Click a button and wait for navigation/response
 * @param page - Playwright Page object
 * @param selector - Button selector
 * @param waitForNav - Whether to wait for navigation (default: false)
 */
export const clickButton = async (
  page: Page,
  selector: string,
  waitForNav: boolean = false
): Promise<void> => {
  const button = page.locator(selector);
  await button.click();

  if (waitForNav) {
    await page.waitForLoadState('networkidle');
  }
};

/**
 * Select an option from a dropdown
 * @param page - Playwright Page object
 * @param selector - Select element selector
 * @param optionText - Option text to select
 */
export const selectOption = async (
  page: Page,
  selector: string,
  optionText: string
): Promise<void> => {
  const select = page.locator(selector);
  await select.selectOption({ label: optionText });
};

// ============================================================
// Assertion Helpers
// ============================================================

/**
 * Assert element has specific text content
 * @param selector - Element selector or locator
 * @param text - Expected text content
 * @param options - Optional assertion options
 */
export const assertTextContent = async (
  selector: any,
  text: string,
  options: { useExact?: boolean; timeout?: number } = {}
): Promise<void> => {
  const timeout = options.timeout || 5000;
  await expect(selector, { timeout }).toHaveText(text, {
    useExact: options.useExact ?? false,
  });
};

/**
 * Assert element has specific attribute value
 * @param page - Playwright Page object
 * @param selector - Element selector
 * @param attribute - Attribute name
 * @param value - Expected attribute value
 */
export const assertAttribute = async (
  page: Page,
  selector: string,
  attribute: string,
  value: string
): Promise<void> => {
  const element = page.locator(selector);
  await expect(element).toHaveAttribute(attribute, value);
};

/**
 * Assert element is visible
 * @param selector - Element selector or locator
 * @param options - Optional assertion options
 */
export const assertVisible = async (
  selector: any,
  options: { timeout?: number } = {}
): Promise<void> => {
  const timeout = options.timeout || 5000;
  await expect(selector, { timeout }).toBeVisible();
};

/**
 * Assert element is hidden or not present
 * @param selector - Element selector or locator
 */
export const assertNotVisible = async (
  selector: any,
  options: { timeout?: number } = {}
): Promise<void> => {
  const timeout = options.timeout || 5000;
  await expect(selector, { timeout }).not.toBeVisible();
};

// ============================================================
// Authentication Helpers
// ============================================================

/**
 * Login as test merchant and get auth token
 * @param page - Playwright Page object
 * @param credentials - Test merchant credentials
 * @returns Auth token string
 */
export const loginAsTestMerchant = async (
  page: Page,
  credentials: { email: string; password: string } = {
    email: 'e2e-product-pins@test.com',
    password: 'TestPass123',
  }
): Promise<void> => {
  await page.goto('/login');

  await page.fill('input[name="email"]', credentials.email);
  await page.fill('input[name="password"]', credentials.password);
  await page.click('button[type="submit"]');

  // Wait for navigation to dashboard
  await page.waitForURL('/dashboard');
};

/**
 * Setup authenticated state for API tests
 * @param page - Playwright Page object
 */
export const setupAuthState = async (
  page: Page
): Promise<void> => {
  await loginAsTestMerchant(page);
  // No need to intercept and add Authorization header as cookies are sent automatically (Story 1.8)
};

// ============================================================
// Test Data Cleanup Helpers
// ============================================================

/**
 * Clear all test data after test suite
 * @param page - Playwright Page object
 */
export const clearTestData = async (page: Page): Promise<void> => {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
};

/**
 * Setup auto-cleanup fixture that runs after each test
 * @param page - Playwright Page object
 * @returns Cleanup function to call after test
 */
export const setupAutoCleanup = (page: Page): (() => Promise<void>) => {
  return async () => {
    await clearTestData(page);
  };
};
