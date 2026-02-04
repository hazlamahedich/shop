/**
 * Merchant Data Factory
 *
 * Generates test data for merchants using @faker-js/faker.
 * Parallel-safe data generation ensures unique data across concurrent tests.
 *
 * Factory Pattern:
 * - createMerchantData() - Generate single merchant with optional overrides
 * - createMultipleMerchants() - Generate multiple unique merchants
 * - All data is unique and parallel-safe
 */

import { faker } from '@faker-js/faker';

// Set a random seed for reproducibility in development
faker.seed(Math.random());

export interface MerchantData {
  merchantKey: string;
  platform: 'flyio' | 'railway' | 'render';
  status: 'pending' | 'deploying' | 'active' | 'error';
  config: {
    region?: string;
    organization?: string;
    appName?: string;
  };
  secretKeyHash?: string;
  deployedAt?: Date;
}

/**
 * Generate a single merchant with realistic test data
 *
 * @param overrides - Partial data to override defaults
 * @returns Complete merchant data object
 *
 * @example
 * ```ts
 * const merchant = createMerchantData();
 * const customMerchant = createMerchantData({ platform: 'railway' });
 * ```
 */
export function createMerchantData(overrides: Partial<MerchantData> = {}): MerchantData {
  const platforms: Array<'flyio' | 'railway' | 'render'> = ['flyio', 'railway', 'render'];
  const statuses: Array<'pending' | 'deploying' | 'active' | 'error'> = ['pending', 'deploying', 'active', 'error'];

  const merchantKey = `shop-${faker.string.uuid()}`;

  return {
    merchantKey,
    platform: faker.helpers.arrayElement(platforms),
    status: faker.helpers.arrayElement(statuses),
    config: {
      region: faker.helpers.arrayElement(['iad', 'sjc', 'syd', 'fra']),
      organization: `org-${faker.string.alphanumeric(8)}`,
      appName: `${merchantKey}-app`,
    },
    secretKeyHash: faker.string.uuid(),
    deployedAt: faker.date.recent({ days: 30 }),
    ...overrides,
    // Ensure merchantKey is always unique, even if overridden
    ...(overrides.merchantKey ? {} : { merchantKey }),
  };
}

/**
 * Generate multiple unique merchants
 *
 * @param count - Number of merchants to generate
 * @param baseOverrides - Overrides to apply to all merchants
 * @returns Array of merchant data objects
 *
 * @example
 * ```ts
 * const merchants = createMultipleMerchants(5);
 * const railMerchants = createMultipleMerchants(3, { platform: 'railway' });
 * ```
 */
export function createMultipleMerchants(
  count: number,
  baseOverrides: Partial<MerchantData> = {}
): MerchantData[] {
  return Array.from({ length: count }, () => createMerchantData(baseOverrides));
}

/**
 * Generate a merchant with a specific status
 * Helper for tests that need specific states
 */
export function createMerchantWithStatus(
  status: 'pending' | 'deploying' | 'active' | 'error'
): MerchantData {
  return createMerchantData({ status });
}

/**
 * Generate a merchant for a specific platform
 * Helper for platform-specific tests
 */
export function createMerchantForPlatform(
  platform: 'flyio' | 'railway' | 'render'
): MerchantData {
  return createMerchantData({ platform });
}
