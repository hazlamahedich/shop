/**
 * Shopify Integration Data Factory
 *
 * Generates test data for Shopify integrations.
 * Simulates OAuth responses and webhook configurations.
 */

import { faker } from '@faker-js/faker';

export interface ShopifyIntegrationData {
  storeUrl: string;
  accessToken: string;
  shopDomain: string;
  webhookStatus: 'verified' | 'pending' | 'failed';
  subscribedTopics: string[];
  shopifyCompanyId: string;
}

/**
 * Generate Shopify integration test data
 */
export function createShopifyData(
  overrides: Partial<ShopifyIntegrationData> = {}
): ShopifyIntegrationData {
  const storeName = faker.company.name().toLowerCase().replace(/\s+/g, '-');
  const storeUrl = `${storeName}.myshopify.com`;

  const allTopics = [
    'orders/create',
    'orders/updated',
    'app/uninstalled',
    'customers/create',
    'products/create',
  ];

  return {
    storeUrl,
    accessToken: `shpat_${faker.string.alphanumeric(32)}`,
    shopDomain: storeUrl,
    webhookStatus: faker.helpers.arrayElement(['verified', 'pending', 'failed']),
    subscribedTopics: faker.helpers.arrayElements(allTopics, { min: 1, max: 3 }),
    shopifyCompanyId: `company-${faker.string.uuid()}`,
    ...overrides,
  };
}

/**
 * Generate verified Shopify integration
 */
export function createVerifiedShopifyIntegration(): ShopifyIntegrationData {
  return createShopifyData({
    webhookStatus: 'verified',
    subscribedTopics: ['orders/create', 'orders/updated', 'app/uninstalled'],
  });
}

/**
 * Generate pending Shopify integration
 */
export function createPendingShopifyIntegration(): ShopifyIntegrationData {
  return createShopifyData({
    webhookStatus: 'pending',
    subscribedTopics: [],
  });
}

/**
 * Generate Shopify integration with custom topics
 */
export function createShopifyIntegrationWithTopics(
  topics: string[]
): ShopifyIntegrationData {
  return createShopifyData({
    subscribedTopics: topics,
  });
}

/**
 * Generate multiple Shopify integrations
 */
export function createMultipleShopifyIntegrations(
  count: number,
  baseOverrides: Partial<ShopifyIntegrationData> = {}
): ShopifyIntegrationData[] {
  return Array.from({ length: count }, () => createShopifyData(baseOverrides));
}
