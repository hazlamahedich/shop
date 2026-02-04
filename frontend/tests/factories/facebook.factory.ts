/**
 * Facebook Integration Data Factory
 *
 * Generates test data for Facebook/Messenger integrations.
 * Simulates OAuth responses and webhook configurations.
 */

import { faker } from '@faker-js/faker';

export interface FacebookIntegrationData {
  pageId: string;
  pageName: string;
  accessToken: string;
  verifyToken: string;
  webhookStatus: 'verified' | 'pending' | 'failed';
  subscribed: boolean;
  appId: string;
}

/**
 * Generate Facebook integration test data
 */
export function createFacebookData(
  overrides: Partial<FacebookIntegrationData> = {}
): FacebookIntegrationData {
  const pageName = `${faker.company.name()} ${faker.helpers.arrayElement(['Shop', 'Store', 'Boutique', 'Market'])}`;

  return {
    pageId: `page-${faker.string.uuid()}`,
    pageName,
    accessToken: `EAA${faker.string.alphanumeric(200)}`,
    verifyToken: `verify-${faker.string.uuid()}`,
    webhookStatus: faker.helpers.arrayElement(['verified', 'pending', 'failed']),
    subscribed: faker.datatype.boolean(),
    appId: `app-${faker.string.uuid()}`,
    ...overrides,
  };
}

/**
 * Generate verified Facebook integration
 */
export function createVerifiedFacebookIntegration(): FacebookIntegrationData {
  return createFacebookData({
    webhookStatus: 'verified',
    subscribed: true,
  });
}

/**
 * Generate pending Facebook integration
 */
export function createPendingFacebookIntegration(): FacebookIntegrationData {
  return createFacebookData({
    webhookStatus: 'pending',
    subscribed: false,
  });
}

/**
 * Generate multiple Facebook integrations
 */
export function createMultipleFacebookIntegrations(
  count: number,
  baseOverrides: Partial<FacebookIntegrationData> = {}
): FacebookIntegrationData[] {
  return Array.from({ length: count }, () => createFacebookData(baseOverrides));
}
