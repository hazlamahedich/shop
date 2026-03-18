import { test, expect, APIRequestContext } from '@playwright/test';

test.describe('Story 9-10: Widget Analytics Events API', () => {
  const API_BASE = 'http://localhost:8000/api/v1';
  const MERCHANT_ID = 1;

  async function createAnalyticsEvent(
    request: APIRequestContext,
    merchantId: number,
    events: Array<{
      type: string;
      timestamp: string;
      session_id: string;
      metadata?: Record<string, unknown>;
    }>
  ) {
    return request.post(`${API_BASE}/analytics/widget/events`, {
      data: { merchant_id: merchantId, events },
      headers: { 'Content-Type': 'application/json', 'X-Test-Mode': 'true' },
    });
  }

  test('[9-10-API-001] [P0] POST /analytics/widget/events accepts valid widget_open event @smoke', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'widget_open',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        metadata: { load_time_ms: 250 },
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(1);
  });

  test('[9-10-API-002] [P0] POST /analytics/widget/events accepts valid message_send event @smoke', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'message_send',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        metadata: { message_length: 25 },
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(1);
  });

  test('[9-10-API-003] [P0] POST /analytics/widget/events accepts batch of events @smoke', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const now = new Date().toISOString();
    const events = [
      { type: 'widget_open', timestamp: now, session_id: sessionId },
      { type: 'message_send', timestamp: now, session_id: sessionId },
      { type: 'quick_reply_click', timestamp: now, session_id: sessionId, metadata: { button_label: 'Track Order' } },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(3);
  });

  test('[9-10-API-004] [P1] POST /analytics/widget/events accepts all event types', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const now = new Date().toISOString();
    const validEventTypes = [
      'widget_open',
      'message_send',
      'quick_reply_click',
      'voice_input',
      'proactive_trigger',
      'carousel_engagement',
    ];

    const events = validEventTypes.map((type) => ({
      type,
      timestamp: now,
      session_id: sessionId,
      metadata: { test: true },
    }));

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(validEventTypes.length);
  });

  test('[9-10-API-005] [P1] POST /analytics/widget/events rejects invalid event type', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'invalid_event_type',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(0);
  });

  test('[9-10-API-006] [P1] POST /analytics/widget/events handles missing timestamp gracefully', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'widget_open',
        timestamp: '',
        session_id: sessionId,
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(1);
  });

  test('[9-10-API-007] [P1] POST /analytics/widget/events accepts event with metadata', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'carousel_engagement',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        metadata: {
          carousel_action: 'swipe_left',
          product_id: 'prod_123',
          duration_ms: 500,
        },
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(1);
  });

  test('[9-10-API-008] [P2] POST /analytics/widget/events handles empty events array', async ({ request }) => {
    const response = await createAnalyticsEvent(request, MERCHANT_ID, []);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(0);
  });

  test('[9-10-API-009] [P2] POST /analytics/widget/events handles partial valid events in batch', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const now = new Date().toISOString();
    const events = [
      { type: 'widget_open', timestamp: now, session_id: sessionId },
      { type: 'invalid_type', timestamp: now, session_id: sessionId },
      { type: 'message_send', timestamp: now, session_id: sessionId },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(2);
  });

  test('[9-10-API-010] [P1] POST /analytics/widget/events handles missing merchant_id', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'widget_open',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
      },
    ];

    const response = await request.post(`${API_BASE}/analytics/widget/events`, {
      data: { events },
      headers: { 'Content-Type': 'application/json', 'X-Test-Mode': 'true' },
    });

    expect([200, 400, 422]).toContain(response.status());
  });

  test('[9-10-API-011] [P1] POST /analytics/widget/events handles concurrent requests', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const now = new Date().toISOString();
    const events = [{ type: 'widget_open', timestamp: now, session_id: sessionId }];

    const responses = await Promise.all([
      createAnalyticsEvent(request, MERCHANT_ID, events),
      createAnalyticsEvent(request, MERCHANT_ID, events),
      createAnalyticsEvent(request, MERCHANT_ID, events),
    ]);

    responses.forEach((response) => {
      expect(response.status()).toBe(200);
    });
  });

  test('[9-10-API-012] [P2] POST /analytics/widget/events validates metadata schema', async ({ request }) => {
    const sessionId = crypto.randomUUID();
    const events = [
      {
        type: 'carousel_engagement',
        timestamp: new Date().toISOString(),
        session_id: sessionId,
        metadata: {
          nested_object: { key: 'value' },
          array_value: [1, 2, 3],
          string_value: 'test',
          number_value: 42,
          boolean_value: true,
        },
      },
    ];

    const response = await createAnalyticsEvent(request, MERCHANT_ID, events);

    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body.accepted).toBe(1);
  });
});
