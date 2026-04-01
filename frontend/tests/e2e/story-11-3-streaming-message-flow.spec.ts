import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
  createMockProduct,
} from '../helpers/widget-test-helpers';
import {
  mockStreamingWebSocket,
  simulateStreamingResponse,
  waitForStreamingStart,
  waitForStreamingToken,
  waitForStreamingEnd,
  createStreamingBuilder,
  STREAM_EVENTS,
  mockWebSocketStream,
} from '../helpers/streaming-test-helpers';

test.describe('Story 11.3 - Streaming Message Flow (Happy Path)', () => {
  test.beforeEach(async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-streaming-session');
  });

  test('[P0] 11.3-E2E-001: streaming message displays token-by-token then finalizes', async ({ page }) => {
    await mockStreamingWebSocket(page, {
      wsUrlPattern: '**/ws/**',
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const builder = createStreamingBuilder()
      .withMessageId('msg-stream-001')
      .withTokens(['Hello', '! ', 'How', ' ', 'can', ' ', 'I', ' ', 'help', '?'])
      .withFinalContent('Hello! How can I help?');

    const sendPromise = page.waitForResponse('**/api/v1/widget/message').catch(() => {});
    await sendMessage(page, 'Hi there');

    await simulateStreamingResponse(page, builder, 10);

    await waitForStreamingStart(page);

    await waitForStreamingToken(page, 'Hello');
    await waitForStreamingToken(page, 'help');

    await waitForStreamingEnd(page);

    await expect(page.getByText('Hello! How can I help?')).toBeVisible();
    await sendPromise;
  });

  test('[P1] 11.3-E2E-002: streaming response preserves products, sources, and quick replies', async ({ page }) => {
    const mockProduct = createMockProduct({
      title: 'Streaming Widget Product',
      price: 39.99,
    });

    await mockStreamingWebSocket(page, {
      wsUrlPattern: '**/ws/**',
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const builder = createStreamingBuilder()
      .withMessageId('msg-stream-002')
      .withTokens(['Here', ' ', 'is', ' ', 'a', ' ', 'product', '!'])
      .withFinalContent('Here is a product!')
      .withProducts([mockProduct])
      .withSources([{ title: 'Product Catalog', url: 'https://example.com/catalog' }])
      .withQuickReplies([
        { text: 'Add to cart', action: 'add_to_cart', value: mockProduct.variant_id },
        { text: 'See similar', action: 'search', value: 'similar products' },
      ]);

    await sendMessage(page, 'show me products');
    await simulateStreamingResponse(page, builder, 10);

    await waitForStreamingEnd(page);

    await expect(page.getByText('Streaming Widget Product')).toBeVisible();
    await expect(page.getByText('$39.99')).toBeVisible();
    await expect(page.getByTestId('quick-reply-button')).toBeVisible();
  });

  test('[P1] 11.3-E2E-003: new streaming message replaces active stream content', async ({ page }) => {
    await mockStreamingWebSocket(page, {
      wsUrlPattern: '**/ws/**',
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const firstBuilder = createStreamingBuilder()
      .withMessageId('msg-stream-003a')
      .withTokens(['First', ' response'])
      .withFinalContent('First response');

    await sendMessage(page, 'first question');
    await simulateStreamingResponse(page, firstBuilder, 5);

    await waitForStreamingStart(page);
    await waitForStreamingToken(page, 'First');

    const secondBuilder = createStreamingBuilder()
      .withMessageId('msg-stream-003b')
      .withTokens(['Second', ' response'])
      .withFinalContent('Second response');

    await sendMessage(page, 'second question');
    await simulateStreamingResponse(page, secondBuilder, 5);

    await waitForStreamingEnd(page);

    await expect(page.getByText('Second response')).toBeVisible();
    const streamingMessages = page.locator('[data-testid="streaming-message"][data-streaming="false"]');
    expect(await streamingMessages.count()).toBeGreaterThanOrEqual(1);
  });

  test('[P2] 11.3-E2E-004: sequential streaming messages display in order', async ({ page }) => {
    await mockStreamingWebSocket(page, {
      wsUrlPattern: '**/ws/**',
    });

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    const firstBuilder = createStreamingBuilder()
      .withMessageId('msg-stream-004a')
      .withTokens(['Hello', ' there', '!'])
      .withFinalContent('Hello there!');

    await sendMessage(page, 'greeting');
    await simulateStreamingResponse(page, firstBuilder, 5);
    await waitForStreamingEnd(page);

    await expect(page.getByText('Hello there!')).toBeVisible();

    const secondBuilder = createStreamingBuilder()
      .withMessageId('msg-stream-004b')
      .withTokens(['Nice', ' to', ' meet', ' you', '.'])
      .withFinalContent('Nice to meet you.');

    await sendMessage(page, 'nice to meet you');
    await simulateStreamingResponse(page, secondBuilder, 5);
    await waitForStreamingEnd(page);

    await expect(page.getByText('Hello there!')).toBeVisible();
    await expect(page.getByText('Nice to meet you.')).toBeVisible();

    const botMessages = page.locator('[data-testid="message-bubble"].message-bubble--bot');
    expect(await botMessages.count()).toBeGreaterThanOrEqual(2);
  });

  test('[P1] 11.3-E2E-005: streaming indicator appears during active stream', async ({ page }) => {
    await mockWebSocketStream(page, [
      { event: STREAM_EVENTS.START, data: { message_id: 'msg-indicator-001' } },
      { event: STREAM_EVENTS.TOKEN, data: { token: 'Loading', message_id: 'msg-indicator-001' } },
      { event: STREAM_EVENTS.TOKEN, data: { token: '...', message_id: 'msg-indicator-001' } },
      { event: STREAM_EVENTS.END, data: { message_id: 'msg-indicator-001', content: 'Loading...' } },
    ]);

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'test streaming indicator');

    await waitForStreamingStart(page);
    await expect(page.getByTestId('streaming-indicator')).toBeVisible();

    await waitForStreamingEnd(page);
    await expect(page.getByTestId('streaming-indicator')).toBeHidden();

    await expect(page.getByText('Loading...')).toBeVisible();
  });
});
