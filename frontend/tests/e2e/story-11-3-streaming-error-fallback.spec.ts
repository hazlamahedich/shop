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
  STREAM_EVENTS,
} from '../helpers/streaming-test-helpers';

test.describe('Story 11.3 - Streaming Error Handling and Fallback', () => {
  test.beforeEach(async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-streaming-session');
  });

  test('[P1] 11.3-E2E-006: streaming error mid-stream shows error message', async ({ page }) => {
    // Given: Mock WS that sends start + 1 token then bot_stream_error
    await mockWebSocketStream(page, [
      { event: STREAM_EVENTS.START, data: { message_id: 'msg-err-1' } },
      { event: STREAM_EVENTS.TOKEN, data: { token: 'Hello ', message_id: 'msg-err-1' } },
      {
        event: STREAM_EVENTS.ERROR,
        data: { message_id: 'msg-err-1', error: 'stream_interrupted', retryable: true },
      },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    // When: User sends message and streaming error occurs
    await sendMessage(page, 'Tell me about shoes');

    // Then: Error indicator shown, partial content preserved or cleared gracefully
    await expect(page.getByTestId('stream-error-indicator')).toBeVisible();
    await expect(page.getByText(/error|try again|something went wrong/i)).toBeVisible();
    await expect(page.getByText('Hello')).toBeVisible();
  });

  test('[P1] 11.3-E2E-007: fallback to REST when WebSocket unavailable', async ({ page }) => {
    // Given: WebSocket connection fails
    await mockWebSocketFailure(page);

    await mockWidgetMessageConditional(page, [
      {
        match: (msg) => msg.includes('hello'),
        response: {
          content: 'Hello! How can I help you today?',
          intent: 'greeting',
          confidence: 0.95,
        },
      },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    // When: User sends message
    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'hello');
    await responsePromise;

    // Then: Message still sent via REST API, response appears normally
    await expect(page.getByText('Hello! How can I help you today?')).toBeVisible();
    await expect(page.getByTestId('message-bubble')).toBeVisible();
  });

  test('[P1] 11.3-E2E-008: fallback to REST preserves all message fields', async ({ page }) => {
    // Given: WebSocket unavailable, REST API returns full message with products
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
            { text: 'Add to cart', action: 'add_to_cart', value: mockProduct.variant_id },
            { text: 'See more', action: 'search', value: 'similar products' },
          ],
        },
      },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    // When: User sends message
    const responsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'show me products');
    await responsePromise;

    // Then: Response shows products, sources, quick_replies etc.
    await expect(page.getByText('Here are some products for you!')).toBeVisible();
    await expect(page.getByText('Streaming Test Product')).toBeVisible();
    await expect(page.getByText('$49.99')).toBeVisible();
    await expect(page.getByTestId('quick-reply-button')).toBeVisible();
  });

  test('[P2] 11.3-E2E-009: streaming reconnects after temporary disconnect', async ({ page }) => {
    // Given: WS disconnects mid-stream then reconnects
    const reconnectController = await mockWebSocketReconnect(page, {
      firstStreamEvents: [
        { event: STREAM_EVENTS.START, data: { message_id: 'msg-disc-1' } },
        { event: STREAM_EVENTS.TOKEN, data: { token: 'Good ', message_id: 'msg-disc-1' } },
        { event: STREAM_EVENTS.ERROR, data: { message_id: 'msg-disc-1', error: 'connection_lost' } },
      ],
      secondStreamEvents: [
        { event: STREAM_EVENTS.START, data: { message_id: 'msg-disc-2' } },
        { event: STREAM_EVENTS.TOKEN, data: { token: 'Reconnected ', message_id: 'msg-disc-2' } },
        { event: STREAM_EVENTS.TOKEN, data: { token: 'response', message_id: 'msg-disc-2' } },
        { event: STREAM_EVENTS.END, data: { message_id: 'msg-disc-2' } },
      ],
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    // When: First message triggers disconnect
    await sendMessage(page, 'first message');
    await expect(page.getByTestId('stream-error-indicator')).toBeVisible();

    // When: Reconnect happens and new message sent
    reconnectController.triggerReconnect();
    await sendMessage(page, 'second message');

    // Then: New streaming response works correctly
    await expect(page.getByText(/Reconnected.*response/i)).toBeVisible();
    await expect(page.getByTestId('stream-error-indicator')).not.toBeVisible();
  });

  test('[P2] 11.3-E2E-010: multi-turn conversation with streaming errors', async ({ page }) => {
    // Given: Mock multi-turn conversation where first message streams fine, second has error, third falls back to REST
    const firstMessageId = 'msg-multi-1';
    const secondMessageId = 'msg-multi-2';

    let wsCallCount = 0;

    await page.route('**/ws/widget/stream**', async (route) => {
      wsCallCount++;

      if (wsCallCount === 1) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify([
            { event: STREAM_EVENTS.START, data: { message_id: firstMessageId } },
            { event: STREAM_EVENTS.TOKEN, data: { token: 'Great ', message_id: firstMessageId } },
            { event: STREAM_EVENTS.TOKEN, data: { token: 'choice!', message_id: firstMessageId } },
            { event: STREAM_EVENTS.END, data: { message_id: firstMessageId } },
          ]),
        });
      } else if (wsCallCount === 2) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify([
            { event: STREAM_EVENTS.START, data: { message_id: secondMessageId } },
            { event: STREAM_EVENTS.TOKEN, data: { token: 'Oop', message_id: secondMessageId } },
            {
              event: STREAM_EVENTS.ERROR,
              data: { message_id: secondMessageId, error: 'timeout', retryable: true },
            },
          ]),
        });
      } else {
        await route.abort();
      }
    });

    await page.route('**/api/v1/widget/message', async (route) => {
      const body = route.request().postDataJSON();
      const message = body?.message?.toLowerCase() || '';

      if (message.includes('tell me about shoes')) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: firstMessageId,
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: 'Great choice!',
            },
          }),
        });
      } else if (message.includes('more details')) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: secondMessageId,
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: 'Oops, let me try again.',
            },
          }),
        });
      } else if (message.includes('fallback')) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            data: {
              message_id: 'msg-multi-3',
              sender: 'bot',
              created_at: new Date().toISOString(),
              content: 'REST fallback response with full details.',
            },
          }),
        });
      } else {
        await route.continue();
      }
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    // When: First message streams fine
    await sendMessage(page, 'tell me about shoes');
    await expect(page.getByText('Great choice!')).toBeVisible();

    // When: Second message has streaming error
    await sendMessage(page, 'more details');
    await expect(page.getByTestId('stream-error-indicator')).toBeVisible();

    // When: Third message falls back to REST
    const restResponsePromise = page.waitForResponse('**/api/v1/widget/message');
    await sendMessage(page, 'use fallback');
    await restResponsePromise;

    // Then: All three responses appear, error handled gracefully, conversation continues
    await expect(page.getByText('Great choice!')).toBeVisible();
    await expect(page.getByText('REST fallback response with full details.')).toBeVisible();

    const userMessages = page.locator('[data-testid="message-bubble"].message-bubble--user');
    const botMessages = page.locator('[data-testid="message-bubble"].message-bubble--bot');
    expect(await userMessages.count()).toBeGreaterThanOrEqual(3);
    expect(await botMessages.count()).toBeGreaterThanOrEqual(3);
  });
});
