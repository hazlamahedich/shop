/**
 * Story 10-3: Suggested Reply Chips API Tests
 *
 * Tests for widget message API response structure:
 * - suggestedReplies field presence and format
 * - camelCase alias from snake_case backend
 * - Max 4 suggestions limit
 * - Response envelope structure
 *
 * Prerequisites: Running backend server with test data
 * Run: TEST_MERCHANT_ID=1 TEST_AUTH_TOKEN=xxx npx playwright test frontend/tests/api/story-10-3-suggested-replies-api.spec.ts
 *
 * Acceptance Criteria:
 * - AC2: Server-Side Generation Using RAG Context
 * - AC5: Fallback to Generic Suggestions
 */

import { test, expect } from '@playwright/test';

const API_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const TEST_MERCHANT_ID = parseInt(process.env.TEST_MERCHANT_ID || '1');
const AUTH_TOKEN = process.env.TEST_AUTH_TOKEN || '';

interface WidgetMessageResponse {
  data: {
    messageId: string;
    content: string;
    sender: string;
    createdAt: string;
    suggestedReplies?: string[];
  };
  meta: {
    request_id: string;
    timestamp: string;
  };
}

test.describe('[P0] Story 10-3: Suggested Replies API Contract', () => {
  test.skip(!AUTH_TOKEN, 'Skipping - TEST_AUTH_TOKEN not provided');

  test('[10.3-API-001] Widget message response includes suggestedReplies field', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Tell me about pricing',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    expect(body.data).toHaveProperty('suggestedReplies');
    expect(Array.isArray(body.data.suggestedReplies)).toBeTruthy();
  });

  test('[10.3-API-002] suggestedReplies uses camelCase alias (not snake_case)', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'What are your hours?',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body = await response.json();

    expect(body.data).toHaveProperty('suggestedReplies');
    expect(body.data).not.toHaveProperty('suggested_replies');
  });

  test('[10.3-API-003] Max 4 suggestions returned', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Tell me about your products and services',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    if (body.data.suggestedReplies && body.data.suggestedReplies.length > 0) {
      expect(body.data.suggestedReplies.length).toBeLessThanOrEqual(4);
    }
  });
});

test.describe('[P1] Story 10-3: Response Structure', () => {
  test.skip(!AUTH_TOKEN, 'Skipping - TEST_AUTH_TOKEN not provided');

  test('[10.3-API-004] Response envelope has valid structure', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Hello',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    expect(body).toHaveProperty('data');
    expect(body).toHaveProperty('meta');
    expect(body.meta).toHaveProperty('request_id');
    expect(body.meta).toHaveProperty('timestamp');
  });

  test('[10.3-API-005] Message data has required fields', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'What can you help me with?',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    expect(body.data).toHaveProperty('messageId');
    expect(body.data).toHaveProperty('content');
    expect(body.data).toHaveProperty('sender');
    expect(body.data).toHaveProperty('createdAt');
    expect(body.data.sender).toBe('bot');
  });

  test('[10.3-API-006] Suggestions are strings', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Tell me more',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    if (body.data.suggestedReplies && body.data.suggestedReplies.length > 0) {
      body.data.suggestedReplies.forEach((suggestion) => {
        expect(typeof suggestion).toBe('string');
        expect(suggestion.length).toBeGreaterThan(0);
      });
    }
  });
});

test.describe('[P1] Story 10-3: Fallback Behavior', () => {
  test.skip(!AUTH_TOKEN, 'Skipping - TEST_AUTH_TOKEN not provided');

  test('[10.3-API-007] Fallback suggestions when RAG returns empty', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'xyzabc random query with no context',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    if (body.data.suggestedReplies) {
      expect(body.data.suggestedReplies.length).toBeGreaterThan(0);
      expect(body.data.suggestedReplies.length).toBeLessThanOrEqual(4);
    }
  });

  test('[10.3-API-008] Generic greeting returns fallback suggestions', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Hi',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    expect(body.data.suggestedReplies).toBeDefined();
    if (body.data.suggestedReplies && body.data.suggestedReplies.length > 0) {
      const hasGenericSuggestion = body.data.suggestedReplies.some(
        (s) =>
          s.toLowerCase().includes('more') ||
          s.toLowerCase().includes('help') ||
          s.toLowerCase().includes('tell') ||
          s.toLowerCase().includes('started')
      );
      expect(hasGenericSuggestion).toBeTruthy();
    }
  });
});

test.describe('[P2] Story 10-3: Edge Cases', () => {
  test.skip(!AUTH_TOKEN, 'Skipping - TEST_AUTH_TOKEN not provided');

  test('[10.3-API-009] Response handles null suggestions gracefully', async ({ request }) => {
    const response = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Hello there',
        session_id: crypto.randomUUID(),
      },
    });

    expect(response.ok()).toBeTruthy();
    const body: WidgetMessageResponse = await response.json();

    if (body.data.suggestedReplies === null || body.data.suggestedReplies === undefined) {
      expect(body.data.content).toBeDefined();
    } else {
      expect(Array.isArray(body.data.suggestedReplies)).toBeTruthy();
    }
  });

  test('[10.3-API-010] Multiple messages in same session maintain suggestions', async ({ request }) => {
    const sessionId = crypto.randomUUID();

    const response1 = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Hello',
        session_id: sessionId,
      },
    });

    expect(response1.ok()).toBeTruthy();
    const body1: WidgetMessageResponse = await response1.json();

    const response2 = await request.post(`${API_URL}/api/v1/widget/message`, {
      headers: {
        Authorization: `Bearer ${AUTH_TOKEN}`,
        'Content-Type': 'application/json',
      },
      data: {
        message: 'Tell me more',
        session_id: sessionId,
      },
    });

    expect(response2.ok()).toBeTruthy();
    const body2: WidgetMessageResponse = await response2.json();

    expect(body2.data).toHaveProperty('suggestedReplies');
  });
});
