/**
 * Base Fixtures - TEA-Style Fixture Composition
 *
 * This file implements the base fixture composition pattern using Playwright's mergeTests.
 * Following the Test Everything Agency (TEA) approach for maintainable fixture composition.
 *
 * Usage:
 * ```ts
 * import { test } from './fixtures/base.fixture';
 *
 * test('my test', async ({ authenticatedPage, merchant }) => {
 *   // test with authenticated page and merchant context
 * });
 * ```
 */

import { mergeTests, test as base } from '@playwright/test';
import { authFixture } from './auth.fixture';
import { merchantFixture } from './merchant.fixture';
import { apiClientFixture } from './api-client.fixture';

/**
 * Authenticated page fixture
 * Provides a page with mock authentication context
 */
export const test = mergeTests(
  base,
  authFixture,
  merchantFixture,
  apiClientFixture
);

/**
 * Extendable test for custom fixture combinations
 *
 * Example:
 * ```ts
 * export const myTest = mergeTests(test, myCustomFixture);
 * ```
 */
export const expect = test.expect;
