/**
 * Merchant Fixture
 *
 * Provides merchant context and data management for E2E tests.
 * Handles merchant-specific setup, state management, and cleanup.
 */

import { test as base } from '@playwright/test';
import { createMerchantData } from '../factories/merchant.factory';

type MerchantContext = {
  merchantKey: string;
  merchantData: {
    merchantKey: string;
    platform: string;
    status: string;
    config: Record<string, unknown>;
  };
};

type MerchantFixtures = {
  merchant: MerchantContext;
  emptyMerchant: MerchantContext;
  withMerchant: (overrides?: Partial<MerchantContext['merchantData']>) => Promise<void>;
  clearMerchantData: () => Promise<void>;
};

export const merchantFixture = base.extend<MerchantFixtures>({
  /**
   * Default merchant context
   * Creates a merchant with test data using factory
   */
  merchant: async ({ page }, use) => {
    const merchantData = createMerchantData();
    const context: MerchantContext = {
      merchantKey: merchantData.merchantKey,
      merchantData,
    };

    // Set merchant context in localStorage
    await page.evaluate((data) => {
      localStorage.setItem('merchant_context', JSON.stringify(data));
    }, context);

    await use(context);

    // Cleanup after test
    await page.evaluate(() => {
      localStorage.removeItem('merchant_context');
    });
  },

  /**
   * Empty merchant context
   * For tests that need to start without merchant data
   */
  emptyMerchant: async ({ page }, use) => {
    const context: MerchantContext = {
      merchantKey: '',
      merchantData: {
        merchantKey: '',
        platform: '',
        status: 'pending',
        config: {},
      },
    };

    await use(context);
  },

  /**
   * Helper to set merchant context with custom data
   * Uses factory with overrides pattern
   */
  withMerchant: async ({ page, merchant }, use) => {
    const setMerchant = async (overrides?: Partial<MerchantContext['merchantData']>) => {
      const merchantData = createMerchantData(overrides);
      const context: MerchantContext = {
        merchantKey: merchantData.merchantKey,
        merchantData,
      };

      await page.evaluate((data) => {
        localStorage.setItem('merchant_context', JSON.stringify(data));
      }, context);

      // Update merchant fixture data
      merchant.merchantKey = context.merchantKey;
      merchant.merchantData = context.merchantData;

      return context;
    };

    await use(setMerchant);
  },

  /**
   * Clear merchant data helper
   * Removes merchant context from storage
   */
  clearMerchantData: async ({ page }, use) => {
    const clearMerchant = async () => {
      await page.evaluate(() => {
        localStorage.removeItem('merchant_context');
        localStorage.removeItem('merchant_key');
        localStorage.removeItem('merchant_config');
      });
    };

    await use(clearMerchant);
  },
});
