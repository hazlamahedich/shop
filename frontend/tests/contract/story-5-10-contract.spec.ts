/**
 * Contract Tests for Story 5-10: Widget Full App Integration
 *
 * These tests validate that the backend API schema matches frontend expectations.
 * Run these in CI against staging/production to catch schema drift.
 *
 * @tags contract api story-5-10 ci
 *
 * Usage:
 *   # Run against local
 *   npm run test:contract -- tests/contract/story-5-10-contract.spec.ts
 *
 *   # Run against staging
 *   API_BASE_URL=https://staging.example.com npm run test:contract
 */

import { test, expect } from '@playwright/test';
import {
  SchemaValidator,
  WidgetConfigSchema,
  WidgetSessionSchema,
  WidgetCartSchema,
  WidgetMessageSchema,
  WidgetProductSchema,
  ApiErrorResponseSchema,
  validateISODateString,
} from '../helpers/widget-schema-validators';

const API_BASE = process.env.API_BASE_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = process.env.TEST_MERCHANT_ID || '1';

function formatSchemaErrors(validator: SchemaValidator): string {
  return validator
    .getErrors()
    .map((e) => `${e.path}: expected ${e.expected}, received ${JSON.stringify(e.received)}`)
    .join('\n');
}

test.describe('Story 5-10: Widget Config Contract Tests', () => {
  test('[P0] CONTRACT: Widget config schema matches frontend expectations', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    const validator = new SchemaValidator();

    expect(body).toHaveProperty('data');
    expect(WidgetConfigSchema.validate(body.data, validator)).toBe(true);

    if (validator.hasErrors()) {
      throw new Error(`Schema validation failed:\n${formatSchemaErrors(validator)}`);
    }
  });

  test('[P0] CONTRACT: Widget config theme has valid constraints', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/config/${TEST_MERCHANT_ID}`);

    expect(response.status()).toBe(200);

    const body = await response.json();
    const theme = body.data?.theme;

    expect(theme).toBeDefined();

    expect(theme.primaryColor).toMatch(/^#[0-9a-fA-F]{6}$/);
    expect(theme.backgroundColor).toMatch(/^#[0-9a-fA-F]{6}$/);
    expect(theme.textColor).toMatch(/^#[0-9a-fA-F]{6}$/);
    expect(theme.botBubbleColor).toMatch(/^#[0-9a-fA-F]{6}$/);
    expect(theme.userBubbleColor).toMatch(/^#[0-9a-fA-F]{6}$/);

    expect(['bottom-right', 'bottom-left']).toContain(theme.position);

    expect(theme.borderRadius).toBeGreaterThanOrEqual(0);
    expect(theme.borderRadius).toBeLessThanOrEqual(30);
    expect(theme.width).toBeGreaterThanOrEqual(280);
    expect(theme.width).toBeLessThanOrEqual(500);
    expect(theme.height).toBeGreaterThanOrEqual(400);
    expect(theme.height).toBeLessThanOrEqual(800);
    expect(theme.fontSize).toBeGreaterThanOrEqual(12);
    expect(theme.fontSize).toBeLessThanOrEqual(20);
  });

  test('[P0] CONTRACT: Widget session creation returns valid schema', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: parseInt(TEST_MERCHANT_ID) },
    });

    expect([200, 201]).toContain(response.status());

    const body = await response.json();
    const validator = new SchemaValidator();

    const session = body.data || body.session;
    expect(session).toBeDefined();

    expect(WidgetSessionSchema.validate(session, validator)).toBe(true);

    if (validator.hasErrors()) {
      throw new Error(`Schema validation failed:\n${formatSchemaErrors(validator)}`);
    }
  });

  test('[P0] CONTRACT: Session expires_at is in the future', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: parseInt(TEST_MERCHANT_ID) },
    });

    expect([200, 201]).toContain(response.status());

    const body = await response.json();
    const session = body.data || body.session;
    const expiresAt = session.expires_at || session.expiresAt;

    expect(validateISODateString(expiresAt)).toBe(true);

    const expiresDate = new Date(expiresAt);
    const now = new Date();
    expect(expiresDate.getTime()).toBeGreaterThan(now.getTime());

    const maxExpiry = new Date(now.getTime() + 24 * 60 * 60 * 1000);
    expect(expiresDate.getTime()).toBeLessThan(maxExpiry.getTime());
  });
});

test.describe('Story 5-10: Cart API Contract Tests', () => {
  let sessionId: string | null = null;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: parseInt(TEST_MERCHANT_ID) },
    });

    if (response.status() === 200 || response.status() === 201) {
      const body = await response.json();
      const session = body.data || body.session;
      sessionId = session.session_id || session.sessionId;
    }
  });

  test('[P1] CONTRACT: Add to cart returns expected schema', async ({ request }) => {
    if (!sessionId) {
      test.skip(true, 'Could not create session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'contract-test-variant',
        quantity: 1,
      },
    });

    expect([200, 201, 400]).toContain(response.status());

    if (response.status() === 200 || response.status() === 201) {
      const body = await response.json();
      const validator = new SchemaValidator();

      expect(body).toHaveProperty('data');
      expect(WidgetCartSchema.validate(body.data, validator)).toBe(true);

      if (validator.hasErrors()) {
        throw new Error(`Schema validation failed:\n${formatSchemaErrors(validator)}`);
      }
    }
  });

  test('[P1] CONTRACT: Cart item has required fields', async ({ request }) => {
    if (!sessionId) {
      test.skip(true, 'Could not create session');
      return;
    }

    await request.post(`${API_BASE}/api/v1/widget/cart`, {
      data: {
        session_id: sessionId,
        variant_id: 'contract-test-item',
        quantity: 1,
      },
    });

    const response = await request.get(`${API_BASE}/api/v1/widget/cart?session_id=${sessionId}`);

    expect([200, 400]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();

      if (body.data?.items?.length > 0) {
        const item = body.data.items[0];
        const validator = new SchemaValidator();

        expect(item).toHaveProperty('variant_id');
        expect(item).toHaveProperty('title');
        expect(item).toHaveProperty('price');
        expect(item).toHaveProperty('quantity');

        expect(typeof item.variant_id).toBe('string');
        expect(typeof item.title).toBe('string');
        expect(typeof item.price).toBe('number');
        expect(typeof item.quantity).toBe('number');
        expect(item.quantity).toBeGreaterThanOrEqual(1);
      }
    }
  });
});

test.describe('Story 5-10: Error Response Contract Tests', () => {
  test('[P1] CONTRACT: Error response has consistent schema', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/v1/widget/config/99999`);

    expect([400, 404]).toContain(response.status());

    const body = await response.json();
    const validator = new SchemaValidator();

    expect(ApiErrorResponseSchema.validate(body, validator)).toBe(true);

    if (validator.hasErrors()) {
      throw new Error(`Schema validation failed:\n${formatSchemaErrors(validator)}`);
    }

    expect(body.error_code).toBeDefined();
    expect(typeof body.error_code).toBe('number');
    expect(body.message).toBeDefined();
    expect(typeof body.message).toBe('string');
  });

  test('[P1] CONTRACT: Invalid session returns proper error', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: 'invalid-session-id',
        query: 'test',
      },
    });

    expect([400, 401, 404, 422]).toContain(response.status());

    const body = await response.json();
    const validator = new SchemaValidator();

    expect(ApiErrorResponseSchema.validate(body, validator)).toBe(true);
  });
});

test.describe('Story 5-10: Search API Contract Tests', () => {
  let sessionId: string | null = null;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: parseInt(TEST_MERCHANT_ID) },
    });

    if (response.status() === 200 || response.status() === 201) {
      const body = await response.json();
      const session = body.data || body.session;
      sessionId = session.session_id || session.sessionId;
    }
  });

  test('[P1] CONTRACT: Search response has valid schema', async ({ request }) => {
    if (!sessionId) {
      test.skip(true, 'Could not create session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/search`, {
      data: {
        session_id: sessionId,
        query: 'test product',
      },
    });

    expect([200, 400, 404, 503]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();
      const validator = new SchemaValidator();

      expect(body).toHaveProperty('data');

      if (body.data?.products && Array.isArray(body.data.products)) {
        body.data.products.forEach((product: unknown, index: number) => {
          if (!WidgetProductSchema.validate(product, validator, index)) {
            throw new Error(`Product ${index} schema validation failed:\n${formatSchemaErrors(validator)}`);
          }
        });
      }

      const total = body.data.total || body.data.totalCount;
      expect(typeof total).toBe('number');
    }
  });
});

test.describe('Story 5-10: Checkout API Contract Tests', () => {
  let sessionId: string | null = null;

  test.beforeAll(async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/v1/widget/session`, {
      data: { merchant_id: parseInt(TEST_MERCHANT_ID) },
    });

    if (response.status() === 200 || response.status() === 201) {
      const body = await response.json();
      const session = body.data || body.session;
      sessionId = session.session_id || session.sessionId;
    }
  });

  test('[P1] CONTRACT: Checkout response has valid schema', async ({ request }) => {
    if (!sessionId) {
      test.skip(true, 'Could not create session');
      return;
    }

    const response = await request.post(`${API_BASE}/api/v1/widget/checkout`, {
      data: { session_id: sessionId },
    });

    expect([200, 400, 503]).toContain(response.status());

    if (response.status() === 200) {
      const body = await response.json();

      expect(body).toHaveProperty('data');
      expect(body.data).toHaveProperty('checkoutUrl');
      expect(typeof body.data.checkoutUrl).toBe('string');
      expect(body.data.checkoutUrl).toMatch(/^https:\/\//);
    } else {
      const body = await response.json();
      const validator = new SchemaValidator();

      expect(ApiErrorResponseSchema.validate(body, validator)).toBe(true);
    }
  });
});
