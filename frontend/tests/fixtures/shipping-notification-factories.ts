/**
 * Shipping Notification Data Factories
 *
 * Provides factory functions for generating test data
 * for Story 4-3 Shipping Notification tests.
 *
 * Usage:
 *   import { createFulfillmentWebhook, createOrderWithPsid } from '../fixtures/shipping-notification-factories';
 *   const webhook = createFulfillmentWebhook({ order_number: 1001 });
 *
 * @package frontend/tests/fixtures/shipping-notification-factories.ts
 */

import { faker } from '@faker-js/faker';

export type ShopifyFulfillmentStatus = 'fulfilled' | 'partial' | 'restocked' | null;
export type ShopifyFinancialStatus = 'pending' | 'authorized' | 'paid' | 'partially_paid' | 'refunded' | 'voided' | 'partially_refunded';

export interface ShopifyFulfillment {
  id: number;
  tracking_number: string;
  tracking_url: string;
  tracking_company?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ShopifyNoteAttribute {
  name: string;
  value: string;
}

export interface ShopifyFulfillmentWebhook {
  id: number;
  order_number: number;
  email: string;
  financial_status: ShopifyFinancialStatus;
  fulfillment_status: ShopifyFulfillmentStatus;
  tracking_numbers: string[];
  tracking_urls: string[];
  fulfillments: ShopifyFulfillment[];
  note_attributes: ShopifyNoteAttribute[];
  updated_at: string;
  created_at: string;
  phone?: string;
  customer?: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
  shipping_address?: {
    address1: string;
    city: string;
    province: string;
    country: string;
    zip: string;
  };
}

export interface WebhookResponse {
  status: 'success' | 'accepted' | 'skipped' | 'error';
  message?: string;
  notification_sent?: boolean;
  error_code?: string;
  order_id?: number;
  psid?: string;
}

const CARRIERS = [
  { name: 'UPS', prefix: '1Z', url_template: 'https://www.ups.com/track?tracknum=' },
  { name: 'FedEx', prefix: '', url_template: 'https://www.fedex.com/fedextrack/?trknbr=' },
  { name: 'USPS', prefix: '', url_template: 'https://tools.usps.com/go/TrackConfirmAction?tLabels=' },
  { name: 'DHL', prefix: '', url_template: 'https://www.dhl.com/us-en/home/tracking/tracking-parcel.html?submit=1&tracking-id=' },
];

export const createTrackingNumber = (carrier: 'UPS' | 'FedEx' | 'USPS' | 'DHL' = 'UPS'): string => {
  switch (carrier) {
    case 'UPS':
      return `1Z${faker.string.alphanumeric({ length: 16, casing: 'upper' })}`;
    case 'FedEx':
      return faker.string.numeric({ length: 12 });
    case 'USPS':
      return faker.string.numeric({ length: 22 });
    case 'DHL':
      return faker.string.numeric({ length: 10 });
    default:
      return faker.string.alphanumeric({ length: 12, casing: 'upper' });
  }
};

export const createTrackingUrl = (trackingNumber: string, carrier: 'UPS' | 'FedEx' | 'USPS' | 'DHL' = 'UPS'): string => {
  const carrierConfig = CARRIERS.find((c) => c.name === carrier);
  if (!carrierConfig) {
    return `https://tracking.example.com/track/${trackingNumber}`;
  }
  return `${carrierConfig.url_template}${trackingNumber}`;
};

export const createFulfillment = (
  overrides: Partial<ShopifyFulfillment> = {}
): ShopifyFulfillment => {
  const carrier = faker.helpers.arrayElement(['UPS', 'FedEx', 'USPS', 'DHL'] as const);
  const trackingNumber = createTrackingNumber(carrier);

  const base: ShopifyFulfillment = {
    id: faker.number.int({ min: 100000000, max: 999999999 }),
    tracking_number: trackingNumber,
    tracking_url: createTrackingUrl(trackingNumber, carrier),
    tracking_company: carrier,
    status: 'success',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  return { ...base, ...overrides };
};

export const createFulfillmentWebhook = (
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  const carrier = 'UPS';
  const trackingNumber = createTrackingNumber(carrier);
  const fulfillment = createFulfillment({
    tracking_number: trackingNumber,
    tracking_url: createTrackingUrl(trackingNumber, carrier),
  });

  const base: ShopifyFulfillmentWebhook = {
    id: faker.number.int({ min: 1000000000, max: 9999999999 }),
    order_number: faker.number.int({ min: 1000, max: 9999 }),
    email: faker.internet.email(),
    financial_status: 'paid',
    fulfillment_status: 'fulfilled',
    tracking_numbers: [trackingNumber],
    tracking_urls: [createTrackingUrl(trackingNumber, carrier)],
    fulfillments: [fulfillment],
    note_attributes: [
      { name: 'messenger_psid', value: `psid_${faker.string.alphanumeric(16)}` },
    ],
    updated_at: new Date().toISOString(),
    created_at: new Date().toISOString(),
  };

  return { ...base, ...overrides };
};

export const createOrderWithPsid = (
  psid: string,
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  return createFulfillmentWebhook({
    note_attributes: [{ name: 'messenger_psid', value: psid }],
    ...overrides,
  });
};

export const createOrderWithoutPsid = (
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  return createFulfillmentWebhook({
    note_attributes: [],
    ...overrides,
  });
};

export const createOrderWithTracking = (
  trackingNumber: string,
  trackingUrl: string,
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  return createFulfillmentWebhook({
    tracking_numbers: [trackingNumber],
    tracking_urls: [trackingUrl],
    fulfillments: [
      createFulfillment({
        tracking_number: trackingNumber,
        tracking_url: trackingUrl,
      }),
    ],
    ...overrides,
  });
};

export const createOrderWithoutTracking = (
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  return createFulfillmentWebhook({
    tracking_numbers: [],
    tracking_urls: [],
    fulfillments: [],
    ...overrides,
  });
};

export const createPartialFulfillmentWebhook = (
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  return createFulfillmentWebhook({
    fulfillment_status: 'partial',
    ...overrides,
  });
};

export const createMultiTrackingWebhook = (
  trackingCount: number = 2,
  overrides: Partial<ShopifyFulfillmentWebhook> = {}
): ShopifyFulfillmentWebhook => {
  const trackingNumbers: string[] = [];
  const trackingUrls: string[] = [];
  const fulfillments: ShopifyFulfillment[] = [];

  for (let i = 0; i < trackingCount; i++) {
    const trackingNumber = createTrackingNumber('UPS');
    trackingNumbers.push(trackingNumber);
    trackingUrls.push(createTrackingUrl(trackingNumber, 'UPS'));
    fulfillments.push(
      createFulfillment({
        id: faker.number.int({ min: 100000000, max: 999999999 }),
        tracking_number: trackingNumber,
        tracking_url: createTrackingUrl(trackingNumber, 'UPS'),
      })
    );
  }

  return createFulfillmentWebhook({
    tracking_numbers: trackingNumbers,
    tracking_urls: trackingUrls,
    fulfillments,
    ...overrides,
  });
};

export const createWebhookHeaders = (
  shopDomain: string = 'test-shop.myshopify.com',
  hmacSignature: string = 'test_signature'
): Record<string, string> => {
  return {
    'X-Shopify-Topic': 'orders/fulfilled',
    'X-Shopify-Shop-Domain': shopDomain,
    'X-Shopify-Hmac-Sha256': hmacSignature,
    'Content-Type': 'application/json',
  };
};

export const createWebhookSuccessResponse = (
  overrides: Partial<WebhookResponse> = {}
): WebhookResponse => {
  return {
    status: 'success',
    notification_sent: true,
    ...overrides,
  };
};

export const createWebhookSkippedResponse = (
  reason: 'no_consent' | 'rate_limited' | 'duplicate' | 'no_psid',
  overrides: Partial<WebhookResponse> = {}
): WebhookResponse => {
  const messages: Record<string, string> = {
    no_consent: 'User has opted out of notifications',
    rate_limited: 'Daily notification limit reached',
    duplicate: 'Duplicate fulfillment already processed',
    no_psid: 'No Messenger PSID associated with order',
  };

  return {
    status: 'skipped',
    message: messages[reason],
    notification_sent: false,
    ...overrides,
  };
};

export const createWebhookErrorResponse = (
  errorCode: string,
  message: string,
  overrides: Partial<WebhookResponse> = {}
): WebhookResponse => {
  return {
    status: 'error',
    error_code: errorCode,
    message,
    notification_sent: false,
    ...overrides,
  };
};
