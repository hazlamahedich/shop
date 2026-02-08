/**
 * Test Helper Utilities
 *
 * Common helper functions for testing.
 * Provides utilities for waiting, assertions, and test setup.
 */

import { expect, type Page } from '@playwright/test';

/**
 * Wait for a specific condition with polling
 * @param condition - Function that returns true when condition is met
 * @param options - Wait options
 * @returns Promise that resolves when condition is met
 */
export async function waitFor<T>(
  condition: () => T | Promise<T>,
  options: { timeout?: number; interval?: number; message?: string } = {}
): Promise<T> {
  const { timeout = 5000, interval = 100, message = 'Condition not met' } = options;

  const startTime = Date.now();

  while (Date.now() - startTime < timeout) {
    try {
      const result = await condition();
      if (result) {
        return result;
      }
    } catch {
      // Ignore errors, continue polling
    }

    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error(`${message} (timeout: ${timeout}ms)`);
}

/**
 * Retry a function with exponential backoff
 * @param fn - Function to retry
 * @param options - Retry options
 * @returns Promise that resolves with the function result
 */
export async function retry<T>(
  fn: () => T | Promise<T>,
  options: { maxAttempts?: number; delay?: number; backoff?: number } = {}
): Promise<T> {
  const { maxAttempts = 3, delay = 100, backoff = 2 } = options;
  let lastError: Error | undefined;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxAttempts - 1) {
        const waitTime = delay * Math.pow(backoff, attempt);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }

  throw lastError;
}

/**
 * Custom assertion helpers
 */
export const assertions = {
  /**
   * Assert that an element is visible and enabled
   */
  async isVisibleAndEnabled(page: Page, selector: string) {
    const element = page.locator(selector);
    await expect(element).toBeVisible();
    await expect(element).toBeEnabled();
  },

  /**
   * Assert that an element contains specific text
   */
  async hasText(page: Page, selector: string, text: string | RegExp) {
    await expect(page.locator(selector)).toContainText(text);
  },

  /**
   * Assert that an element has a specific attribute value
   */
  async hasAttribute(page: Page, selector: string, attribute: string, value: string | RegExp) {
    await expect(page.locator(selector)).toHaveAttribute(attribute, value);
  },

  /**
   * Assert that an element has a specific class
   */
  async hasClass(page: Page, selector: string, className: string | RegExp) {
    await expect(page.locator(selector)).toHaveClass(className);
  },

  /**
   * Assert that the page URL matches a pattern
   */
  async hasUrl(page: Page, urlPattern: string | RegExp) {
    await expect(page).toHaveURL(urlPattern);
  },

  /**
   * Assert that an API call was made with specific parameters
   */
  async apiCalledWith(page: Page, url: string, method: string = 'GET') {
    const requests = [];
    page.on('request', request => {
      if (request.url().includes(url) && request.method() === method) {
        requests.push(request);
      }
    });
    return requests.length > 0;
  },
};

/**
 * Test data cleanup helpers
 */
export const cleanup = {
  /**
   * Clear all timers and intervals
   */
  clearAllTimers() {
    if (typeof window !== 'undefined') {
      const highestId = window.setTimeout(() => {}, 0);
      for (let i = 0; i < highestId; i++) {
        window.clearTimeout(i);
        window.clearInterval(i);
      }
    }
  },

  /**
   * Clear localStorage
   */
  clearLocalStorage() {
    if (typeof window !== 'undefined') {
      localStorage.clear();
    }
  },

  /**
   * Clear sessionStorage
   */
  clearSessionStorage() {
    if (typeof window !== 'undefined') {
      sessionStorage.clear();
    }
  },

  /**
   * Clear all storage
   */
  clearAllStorage() {
    this.clearLocalStorage();
    this.clearSessionStorage();
  },
};

/**
 * Mock setup helpers
 */
export const mocks = {
  /**
   * Setup mock fetch with response
   */
  setupFetch(response: any) {
    if (typeof global.fetch !== 'undefined') {
      global.fetch = jest.fn().mockResolvedValue(response);
    }
  },

  /**
   * Restore original fetch
   */
  restoreFetch() {
    if (typeof global.fetch !== 'undefined') {
      // @ts-ignore - restoring original fetch
      global.fetch = originalFetch;
    }
  },

  /**
   * Setup mock localStorage
   */
  setupLocalStorage(items: Record<string, string>) {
    if (typeof localStorage !== 'undefined') {
      Object.entries(items).forEach(([key, value]) => {
        localStorage.setItem(key, value);
      });
    }
  },
};

// Store original fetch for restoration
let originalFetch: typeof fetch | undefined;
if (typeof global !== 'undefined' && typeof global.fetch !== 'undefined') {
  originalFetch = global.fetch;
}
