/**
 * Data Factories for Test Automation
 *
 * Provides reusable factory functions for generating test data
 * using Faker.js for realistic but deterministic test values.
 *
 * Usage:
 *   import { createProductPinData, createMerchantData } from '../fixtures/data-factories';
 *   const testData = createProductPinData({ title: 'Custom Product' });
 *
 * @tags fixtures test-data factories
 */

import { faker } from '@faker-js/faker';

// ============================================================
// Product Pin Data Factories
// ============================================================

/**
 * Create a product pin item with realistic defaults
 * @param overrides - Optional properties to override defaults
 * @returns ProductPinItem object
 */
export const createProductPinData = (overrides: Partial<ProductPinItem> = {}): ProductPinItem => {
  const productId = `shopify_${faker.string.uuid()}`;
  const baseProduct = {
    product_id: productId,
    title: faker.commerce.productName(),
    image_url: faker.image.url({ width: 400, height: 400 }),
    is_pinned: faker.datatype.boolean(),
    pinned_order: faker.datatype.number({ min: 1, max: 10 }),
    pinned_at: faker.date.recent().toISOString(),
  };

  return { ...baseProduct, ...overrides };
};

/**
 * Create an array of product pin items
 * @param count - Number of products to create
 * @param overrides - Optional overrides for all items
 * @returns Array of ProductPinItem objects
 */
export const createProductPinList = (
  count: number,
  overrides: Partial<ProductPinItem> = {}
): ProductPinItem[] => {
  return Array.from({ length: count }, () => createProductPinData(overrides));
};

/**
 * Create pinned products only
 * @param count - Number of pinned products
 * @returns Array of pinned ProductPinItem objects
 */
export const createPinnedProducts = (count: number): ProductPinItem[] => {
  return Array.from({ length: count }, (_, i) =>
    createProductPinData({
      is_pinned: true,
      pinned_order: i + 1,
      pinned_at: faker.date.recent().toISOString(),
    })
  );
};

/**
 * Create unpinned products only
 * @param count - Number of unpinned products
 * @returns Array of unpinned ProductPinItem objects
 */
export const createUnpinnedProducts = (count: number): ProductPinItem[] => {
  return Array.from({ length: count }, () =>
    createProductPinData({
      is_pinned: false,
      pinned_order: undefined,
      pinned_at: undefined,
    })
  );
};

// ============================================================
// Pagination Data Factories
// ============================================================

/**
 * Create pagination metadata
 * @param overrides - Optional properties to override defaults
 * @returns PaginationMeta object
 */
export const createPaginationData = (overrides: Partial<PaginationMeta> = {}): PaginationMeta => {
  const basePagination = {
    page: faker.datatype.number({ min: 1, max: 10 }),
    limit: 20,
    total: faker.datatype.number({ min: 0, max: 500 }),
    has_more: faker.datatype.boolean(),
  };

  return { ...basePagination, ...overrides };
};

/**
 * Create pagination for first page
 * @returns PaginationMeta for page 1
 */
export const createFirstPagePagination = (): PaginationMeta => {
  return createPaginationData({ page: 1, has_more: true });
};

/**
 * Create pagination for last page
 * @returns PaginationMeta with no more pages
 */
export const createLastPagePagination = (): PaginationMeta => {
  return createPaginationData({ has_more: false });
};

// ============================================================
// Pin Limit Info Factories
// ============================================================

/**
 * Create pin limit information
 * @param overrides - Optional properties to override defaults
 * @returns PinLimitInfo object
 */
export const createPinLimitInfo = (overrides: Partial<PinLimitInfo> = {}): PinLimitInfo => {
  const baseLimit = {
    pin_limit: 10,
    pinned_count: faker.datatype.number({ min: 0, max: 10 }),
  };

  return { ...baseLimit, ...overrides };
};

/**
 * Create pin limit at maximum capacity
 * @returns PinLimitInfo with pinned_count equal to pin_limit
 */
export const createMaxPinLimit = (): PinLimitInfo => {
  return createPinLimitInfo({ pinned_count: 10 });
};

/**
 * Create pin limit under capacity
 * @param count - Current number of pinned products
 * @returns PinLimitInfo with specified count
 */
export const createPartialPinLimit = (count: number): PinLimitInfo => {
  return createPinLimitInfo({ pinned_count: Math.min(count, 10) });
};

// ============================================================
// API Response Factories
// ============================================================

/**
 * Create a successful API response envelope
 * @param data - Response data
 * @param meta - Optional metadata overrides
 * @returns MinimalEnvelope response object
 */
export const createSuccessResponse = <T>(
  data: T,
  meta: { request_id?: string; timestamp?: string } = {}
): ApiEnvelope<T> => {
  return {
    data,
    meta: {
      request_id: faker.string.uuid(),
      timestamp: new Date().toISOString(),
      ...meta,
    },
  };
};

/**
 * Create an error API response
 * @param errorCode - Error code number
 * @param message - Error message
 * @param details - Optional error details
 * @returns Error response object
 */
export const createErrorResponse = (
  errorCode: number,
  message: string,
  details: any = {}
): { error: string; error_code: number; details: any; meta: { request_id: string; timestamp: string } } => {
  return {
    error: message,
    error_code: errorCode,
    details,
    meta: {
      request_id: faker.string.uuid(),
      timestamp: new Date().toISOString(),
    },
  };
};

// ============================================================
// Product Data Factories for Search Testing
// ============================================================

/**
 * Create products matching a search term
 * @param searchTerm - Search term to match
 * @param count - Number of matching products
 * @returns Array of ProductPinItem objects
 */
export const createSearchMatchingProducts = (
  searchTerm: string,
  count: number
): ProductPinItem[] => {
  return Array.from({ length: count }, (_, i) =>
    createProductPinData({
      title: `${searchTerm} ${faker.commerce.productAdjective()}`,
      is_pinned: faker.datatype.boolean(),
    })
  );
};

/**
 * Create products NOT matching a search term
 * @param searchTerm - Search term to avoid
 * @param count - Number of non-matching products
 * @returns Array of ProductPinItem objects
 */
export const createSearchNonMatchingProducts = (
  searchTerm: string,
  count: number
): ProductPinItem[] => {
  const otherTerms = ['Running', 'Walking', 'Training', 'Basketball', 'Yoga'];
  return Array.from({ length: count }, () =>
    createProductPinData({
      title: `${faker.helpers.arrayElement(otherTerms)} ${faker.commerce.productAdjective()}`,
      is_pinned: faker.datatype.boolean(),
    })
  );
};

// ============================================================
// Type Definitions
// ============================================================

export interface ProductPinItem {
  product_id: string;
  title: string;
  image_url?: string;
  is_pinned: boolean;
  pinned_order?: number;
  pinned_at?: string;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
}

export interface PinLimitInfo {
  pin_limit: number;
  pinned_count: number;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: {
    request_id: string;
    timestamp: string;
    [key: string]: any;
  };
}

/**
 * Faker seed for reproducible tests
 * Call this at test setup if you need deterministic values
 */
export const setFakerSeed = (seed: number): void => {
  faker.seed(seed);
};

/**
 * Reset faker to random seed
 * Call this to restore random behavior
 */
export const resetFakerSeed = (): void => {
  faker.seed(Math.random());
};
