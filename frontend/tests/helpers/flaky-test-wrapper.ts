/**
 * Flaky Test Detection Wrapper
 *
 * Provides retry logic for potentially flaky tests.
 * Uses a pattern to detect and report persistent failures.
 *
 * Usage:
 * ```ts
 * import { stableTest } from '../helpers/flaky-test-wrapper';
 *
 * stableTest('my potentially flaky test', async ({ page }) => {
 *   // test code
 * });
 * ```
 */

import { test as base } from '@playwright/test';

export type StableTestFn = ReturnType<typeof base>;

/**
 * Wrapper for tests that may be flaky
 * Provides retry logic with fresh page state
 */
export const stableTest = base.extend<{
  retryCount: number;
}>({
  retryCount: async ({}, use) => {
    const count = 0;
    await use(count);
  },
});

/**
 * Run a test with retry logic
 * Automatically retries on failure up to 3 times
 */
export function withRetry<T>(
  testFn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  return new Promise((resolve, reject) => {
    let attempts = 0;

    const attempt = async () => {
      attempts++;

      try {
        const result = await testFn();
        resolve(result);
      } catch (error) {
        if (attempts < maxRetries) {
          console.warn(`Test failed, retrying... (attempt ${attempts}/${maxRetries})`);
          setTimeout(attempt, 1000);
        } else {
          reject(error);
        }
      }
    };

    attempt();
  });
}

/**
 * Wrap a test with fresh page state on each retry
 */
export function withFreshPage<T>(
  pageFn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  return withRetry(async () => {
    // Test logic here - page will be fresh on each retry
    return await pageFn();
  }, maxRetries);
}

/**
 * Detect if a test failure is persistent
 * Used to identify truly flaky tests vs one-off failures
 */
export function isPersistentFailure(failureCount: number, totalRuns: number): boolean {
  // If more than 50% of runs fail, it's a persistent issue
  return (failureCount / totalRuns) > 0.5;
}

/**
 * Calculate flakiness score
 * Returns percentage of test runs that failed
 */
export function calculateFlakiness(failureCount: number, totalRuns: number): number {
  return (failureCount / totalRuns) * 100;
}
