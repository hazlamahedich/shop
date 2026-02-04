/**
 * API Client Fixture
 *
 * Provides API-first setup helpers for E2E tests.
 * Using API calls instead of UI interactions is 10-50x faster.
 *
 * This fixture wraps the API client helper for use in tests.
 */

import { test as base, APIRequestContext, APIResponse } from '@playwright/test';
import { seedMerchant, setupWebhooks, cleanupTestData, MerchantData } from '../helpers/api-client';

type ApiClientFixtures = {
  seedTestMerchant: (overrides?: Partial<MerchantData>) => Promise<MerchantData>;
  setupTestWebhooks: (merchantKey: string, platforms: string[]) => Promise<void>;
  cleanupTestData: (merchantKey?: string) => Promise<void>;
  apiResponse: {
    seedMerchant: (data: MerchantData) => Promise<APIResponse>;
    setupWebhooks: (merchantKey: string, platforms: string[]) => Promise<APIResponse>;
  };
};

export const apiClientFixture = base.extend<ApiClientFixtures>({
  /**
   * Seed a test merchant via API
   * Much faster than going through the UI
   */
  seedTestMerchant: async ({ request }, use) => {
    const seed = async (overrides?: Partial<MerchantData>) => {
      return await seedMerchant(request, overrides);
    };
    await use(seed);
  },

  /**
   * Setup webhooks via API
   * Bypasses OAuth flows for faster test execution
   */
  setupTestWebhooks: async ({ request }, use) => {
    const setup = async (merchantKey: string, platforms: string[]) => {
      await setupWebhooks(request, merchantKey, platforms);
    };
    await use(setup);
  },

  /**
   * Cleanup test data
   * Ensures test isolation by removing created data
   */
  cleanupTestData: async ({ request }, use) => {
    const cleanup = async (merchantKey?: string) => {
      await cleanupTestData(request, merchantKey);
    };
    await use(cleanup);
  },

  /**
   * Raw API response helpers
   * For tests that need to inspect API responses
   */
  apiResponse: async ({ request }, use) => {
    const helpers = {
      seedMerchant: async (data: MerchantData) => {
        return await seedMerchant(request, {}, data);
      },
      setupWebhooks: async (merchantKey: string, platforms: string[]) => {
        return await setupWebhooks(request, merchantKey, platforms, true);
      },
    };
    await use(helpers);
  },
});
