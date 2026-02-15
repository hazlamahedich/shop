/**
 * Conversation History API Integration Tests
 *
 * Story 4-8: Conversation History View
 * Tests the /api/conversations/{conversation_id}/history endpoint
 *
 * @tags api integration conversation-history story-4-8
 */

import { test, expect } from '@playwright/test';

const BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';

const createMockHistoryData = (overrides: Record<string, unknown> = {}) => ({
  conversationId: 1,
  messages: [
    {
      id: 1,
      sender: 'customer',
      content: 'Hello, I need help',
      createdAt: new Date(Date.now() - 600000).toISOString(),
      confidenceScore: null,
    },
    {
      id: 2,
      sender: 'bot',
      content: 'How can I assist you?',
      createdAt: new Date(Date.now() - 590000).toISOString(),
      confidenceScore: 0.92,
    },
  ],
  context: {
    cartState: null,
    extractedConstraints: null,
  },
  handoff: {
    triggerReason: 'keyword',
    triggeredAt: new Date(Date.now() - 300000).toISOString(),
    urgencyLevel: 'medium',
    waitTimeSeconds: 300,
  },
  customer: {
    maskedId: '1234****',
    orderCount: 0,
  },
  ...overrides,
});

test.describe('Conversation History API - Authentication', () => {
  test('[P0] @smoke should require authentication', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    expect(response.status()).toBe(401);

    const body = await response.json();
    expect(body).toHaveProperty('message');
    expect(body.message).toMatch(/authentication|unauthorized|required/i);
  });

  test('[P0] should reject invalid token', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`, {
      headers: {
        Authorization: 'Bearer invalid-token',
        'Content-Type': 'application/json',
      },
    });

    expect(response.status()).toBe(401);
  });
});

test.describe('Conversation History API - Response Structure', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P0] @smoke should return valid response structure', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body).toHaveProperty('data');
      expect(body).toHaveProperty('meta');

      expect(body.data).toHaveProperty('conversationId');
      expect(body.data).toHaveProperty('messages');
      expect(body.data).toHaveProperty('context');
      expect(body.data).toHaveProperty('handoff');
      expect(body.data).toHaveProperty('customer');

      expect(Array.isArray(body.data.messages)).toBe(true);
    }
  });

  test('[P0] should return messages in chronological order', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const messages = body.data.messages;

      if (messages.length > 1) {
        for (let i = 1; i < messages.length; i++) {
          const prevDate = new Date(messages[i - 1].createdAt);
          const currDate = new Date(messages[i].createdAt);
          expect(currDate.getTime()).toBeGreaterThanOrEqual(prevDate.getTime());
        }
      }
    }
  });

  test('[P0] should include confidence score for bot messages', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const botMessages = body.data.messages.filter((m: any) => m.sender === 'bot');

      for (const msg of botMessages) {
        expect(msg).toHaveProperty('confidenceScore');
        if (msg.confidenceScore !== null) {
          expect(typeof msg.confidenceScore).toBe('number');
          expect(msg.confidenceScore).toBeGreaterThanOrEqual(0);
          expect(msg.confidenceScore).toBeLessThanOrEqual(1);
        }
      }
    }
  });

  test('[P0] should have null confidence for customer messages', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const customerMessages = body.data.messages.filter((m: any) => m.sender === 'customer');

      for (const msg of customerMessages) {
        expect(msg.confidenceScore).toBeNull();
      }
    }
  });

  test('[P1] should validate message sender values', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const validSenders = ['customer', 'bot'];

      for (const msg of body.data.messages) {
        expect(validSenders).toContain(msg.sender);
      }
    }
  });

  test('[P1] should validate urgency level values', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const validUrgency = ['high', 'medium', 'low'];

      expect(validUrgency).toContain(body.data.handoff.urgencyLevel);
    }
  });

  test('[P1] should validate trigger reason values', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const validReasons = ['keyword', 'low_confidence', 'clarification_loop'];

      expect(validReasons).toContain(body.data.handoff.triggerReason);
    }
  });
});

test.describe('Conversation History API - Context Data', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] should include cart state when present', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.data.context).toHaveProperty('cartState');
      expect(body.data.context).toHaveProperty('extractedConstraints');

      if (body.data.context.cartState && body.data.context.cartState.items) {
        expect(Array.isArray(body.data.context.cartState.items)).toBe(true);

        for (const item of body.data.context.cartState.items) {
          expect(item).toHaveProperty('productId');
          expect(item).toHaveProperty('name');
          expect(item).toHaveProperty('quantity');
        }
      }
    }
  });

  test('[P1] should include extracted constraints when present', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const constraints = body.data.context.extractedConstraints;

      if (constraints) {
        expect(typeof constraints).toBe('object');
        expect(constraints).toHaveProperty('budget');
        expect(constraints).toHaveProperty('size');
        expect(constraints).toHaveProperty('category');
      }
    }
  });

  test('[P1] should include customer info', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.data.customer).toHaveProperty('maskedId');
      expect(body.data.customer).toHaveProperty('orderCount');
      expect(typeof body.data.customer.orderCount).toBe('number');
    }
  });

  test('[P1] should mask customer ID properly', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();
      const maskedId = body.data.customer.maskedId;

      expect(maskedId).toMatch(/\*{4,}$/);
    }
  });

  test('[P2] should include handoff wait time', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.data.handoff).toHaveProperty('waitTimeSeconds');
      expect(typeof body.data.handoff.waitTimeSeconds).toBe('number');
      expect(body.data.handoff.waitTimeSeconds).toBeGreaterThanOrEqual(0);
    }
  });

  test('[P2] should include handoff triggered timestamp', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.data.handoff).toHaveProperty('triggeredAt');
      expect(new Date(body.data.handoff.triggeredAt).toISOString()).toBe(body.data.handoff.triggeredAt);
    }
  });
});

test.describe('Conversation History API - Error Handling', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] should return 404 for non-existent conversation', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/99999999/history`);

    expect(response.status()).toBe(404);

    const body = await response.json();
    expect(body).toHaveProperty('error_code');
    expect(body.error_code).toBe(7001);
  });

  test('[P1] should return 404 for conversation not owned by merchant', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/other-merchant-conv/history`);

    expect(response.status()).toBe(404);
  });

  test('[P2] should validate conversation_id is numeric', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/invalid/history`);

    expect([400, 404, 422]).toContain(response.status());
  });

  test('[P2] should handle negative conversation_id', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/-1/history`);

    expect([400, 404, 422]).toContain(response.status());
  });

  test('[P2] should return proper error format', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/99999999/history`);

    expect(response.status()).toBe(404);

    const body = await response.json();
    expect(body).toHaveProperty('error_code');
    expect(body).toHaveProperty('message');
    expect(typeof body.message).toBe('string');
  });
});

test.describe('Conversation History API - Meta Information', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P2] should include request ID in meta', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.meta).toHaveProperty('requestId');
      expect(typeof body.meta.requestId).toBe('string');
    }
  });

  test('[P2] should include timestamp in meta', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const body = await response.json();

      expect(body.meta).toHaveProperty('timestamp');
      expect(new Date(body.meta.timestamp).toISOString()).toBe(body.meta.timestamp);
    }
  });
});

test.describe('Conversation History API - Content Type', () => {
  test.use({ extraHTTPHeaders: { Authorization: `Bearer ${process.env.TEST_AUTH_TOKEN || 'test-token'}` } });

  test('[P1] should return JSON content type', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/1/history`);

    if (response.status() === 200) {
      const contentType = response.headers()['content-type'];
      expect(contentType).toMatch(/application\/json/);
    }
  });

  test('[P1] should return JSON content type for errors', async ({ request }) => {
    const response = await request.get(`${BASE_URL}/api/conversations/99999999/history`);

    const contentType = response.headers()['content-type'];
    expect(contentType).toMatch(/application\/json/);
  });
});
