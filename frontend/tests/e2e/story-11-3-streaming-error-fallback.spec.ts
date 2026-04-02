import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
  createMockProduct,
  mockWidgetMessageConditional,
} from '../helpers/widget-test-helpers';
import {
  mockWebSocketStream,
  mockWebSocketFailure,
  mockWebSocketReconnect,
  mockMultiTurnConversation,
  STREAM_EVENTS,
  type StreamedEvent,
} from '../helpers/streaming-test-helpers';

test.describe('Story 11.3 - Streaming Error Handling and Fallback', () => {
  test.describe.configure({ retries: 2, mode: 'serial' });
  test.beforeEach(async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-streaming-session');
  });

  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  test('[P1] 11.3-E2E-006: streaming error mid-stream shows error message', async ({ page }) => {
    await mockWebSocketStream(page, [
      { type: STREAM_EVENTS.START, data: { messageId: 'msg-err-1' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: 'Hello ', messageId: 'msg-err-1' } },
      { type: STREAM_EVENTS.ERROR, data: { messageId: 'msg-err-1', error: 'stream_interrupted' } },
    ], { delay: 100 });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'Tell me about shoes');

    await expect(page.getByTestId('stream-error-indicator')).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId('stream-error-indicator').getByText('Something went wrong')).toBeVisible({ timeout: 10000 });
  });

  test('[P2] 11.3-E2E-007: falls back to REST when WebSocket unavailable', async ({ page }) => {
    await mockWebSocketFailure(page);

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: {
          content: 'Hello! I am here to help.',
        },
      },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'hello');

    await expect(page.getByText('Hello! I am here to help.')).toBeVisible({ timeout: 10000 });
  });

  test('[P2] 11.3-E2E-008: REST fallback preserves products, sources, and quick replies', async ({ page }) => {
    await mockWebSocketFailure(page);

    const mockProduct = createMockProduct({
      title: 'Streaming Test Product',
      price: 49.99,
    });

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('products'),
        response: {
          content: 'Here are some products for you!',
          intent: 'product_search',
          confidence: 0.92,
          products: [mockProduct],
          sources: [
            { title: 'Product Catalog', url: 'https://example.com/catalog' },
          ],
          quick_replies: [
            { id: 'qr-1', text: 'Add to cart' },
            { id: 'qr-2', text: 'See more' },
          ],
        },
      },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'show me products');

    await expect(page.getByText('Here are some products for you!')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('$49.99')).toBeVisible();
    await expect(page.getByTestId(/quick-reply-button/).first()).toBeVisible();
  });

  test('[P2] 11.3-E2E-009: streaming reconnects after temporary disconnect', async ({ page }) => {
    let httpMessageCount = 0;
    let wsHandledCount = 0;
    let connectionIndex = 0;

    const firstEvents: StreamedEvent[] = [
      { type: STREAM_EVENTS.START, data: { messageId: 'msg-disc-1' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: 'Good ', messageId: 'msg-disc-1' } },
      { type: STREAM_EVENTS.ERROR, data: { messageId: 'msg-disc-1', error: 'connection_lost' } },
    ];

    const secondEvents: StreamedEvent[] = [
      { type: STREAM_EVENTS.START, data: { messageId: 'msg-disc-2' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: 'Reconnected ', messageId: 'msg-disc-2' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: 'response', messageId: 'msg-disc-2' } },
      { type: STREAM_EVENTS.END, data: { messageId: 'msg-disc-2', content: 'Reconnected response' } },
    ];

    await page.route('**/api/v1/widget/message', async (route) => {
      httpMessageCount++;
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            message_id: crypto.randomUUID(),
            sender: 'bot',
            content: '',
            created_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.routeWebSocket('**/ws/**', (ws) => {
      const currentConn = connectionIndex;
      connectionIndex++;

      ws.onMessage((msg) => {
        const str = typeof msg === 'string' ? msg : msg.toString();
        try {
          const parsed = JSON.parse(str);
          if (parsed.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch {}
      });

      const events = currentConn === 0 ? firstEvents : secondEvents;

      const pollAndSend = () => {
        if (wsHandledCount < httpMessageCount) {
          wsHandledCount++;
          let i = 0;
          const sendNext = () => {
            if (i < events.length) {
              ws.send(JSON.stringify({ type: events[i].type, data: events[i].data }));
              i++;
              if (i < events.length) {
                setTimeout(sendNext, 100);
              } else if (currentConn === 0) {
                setTimeout(() => {
                  ws.close({ code: 1006, reason: 'Simulated disconnect' });
                }, 100);
              }
            }
          };
          sendNext();
        } else {
          setTimeout(pollAndSend, 50);
        }
      };
      pollAndSend();
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'first message');
    await expect(page.getByTestId('stream-error-indicator')).toBeVisible({ timeout: 10000 });

    await expect(page.getByText('Disconnected - Reconnecting...')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/Disconnected|Connecting/)).toBeHidden({ timeout: 10000 });

    await sendMessage(page, 'second message');
    await expect(page.getByText('Reconnected response').first()).toBeVisible({ timeout: 15000 });
  });

  test('[P2] 11.3-E2E-010: multi-turn conversation with streaming errors', async ({ page }) => {
    await mockMultiTurnConversation(
      page,
      [
        {
          type: 'stream',
          events: [
            { type: STREAM_EVENTS.START, data: { messageId: 'msg-multi-1' } },
            { type: STREAM_EVENTS.TOKEN, data: { token: 'Great ', messageId: 'msg-multi-1' } },
            { type: STREAM_EVENTS.TOKEN, data: { token: 'choice!', messageId: 'msg-multi-1' } },
            { type: STREAM_EVENTS.END, data: { messageId: 'msg-multi-1', content: 'Great choice!' } },
          ],
          closeAfter: true,
        },
        {
          type: 'stream',
          events: [
            { type: STREAM_EVENTS.START, data: { messageId: 'msg-multi-2' } },
            { type: STREAM_EVENTS.TOKEN, data: { token: 'Error...', messageId: 'msg-multi-2' } },
            { type: STREAM_EVENTS.ERROR, data: { messageId: 'msg-multi-2', error: 'stream_failed' } },
          ],
          closeAfter: true,
        },
      ],
      [
        {
          match: (msg) => msg.includes('use fallback'),
          response: {
            message_id: 'msg-multi-3',
            sender: 'bot',
            content: 'REST fallback response with full details.',
          },
        },
      ],
      { delay: 100, refuseAfter: 2 }
    );

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'tell me about this');
    await expect(page.getByText(/Great.*choice/i)).toBeVisible({ timeout: 10000 });

    await sendMessage(page, 'more details');
    await expect(page.getByTestId('stream-error-indicator')).toBeVisible({ timeout: 10000 });

    await expect(page.getByText(/Disconnected|Connection error/)).toBeVisible({ timeout: 10000 });

    const restResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'use fallback');
    await restResponsePromise;
    await expect(page.getByText('REST fallback response with full details.')).toBeVisible({ timeout: 10000 });

    const userMessages = page.locator('[data-testid="message-bubble"].message-bubble--user');
    expect(await userMessages.count()).toBeGreaterThanOrEqual(3);
  });
});
