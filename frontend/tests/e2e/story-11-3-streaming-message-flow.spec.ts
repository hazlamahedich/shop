import { test, expect } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetConfig,
  mockWidgetSession,
  sendMessage,
  mockWidgetMessage,
  createMockProduct,
} from '../helpers/widget-test-helpers';
import {
  mockStreamingWebSocket,
  waitForStreamingStart,
  waitForStreamingToken,
  waitForStreamingEnd,
  createStreamingBuilder,
  mockWebSocketStream,
  STREAM_EVENTS,
} from '../helpers/streaming-test-helpers';

test.describe('Story 11.3 - Streaming Message Flow (Happy Path)', () => {
  test.describe.configure({ retries: 2, mode: 'serial' });
  test.beforeEach(async ({ page }) => {
    await mockWidgetConfig(page);
    await mockWidgetSession(page, 'test-streaming-session');
  });

  test.afterEach(async ({ page }) => {
    await page.unrouteAll();
  });

  test('[P0] 11.3-E2E-001: streaming message displays token-by-token then finalizes', async ({ page }) => {
    await mockStreamingWebSocket(page, createStreamingBuilder()
      .withMessageId('msg-stream-001')
      .withTokens(['Hello', '! ', 'How', ' ', 'can', ' ', 'I', ' ', 'help', '?'])
      .withFinalContent('Hello! How can I help?'));

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'Hi there');

    await waitForStreamingStart(page);
    await waitForStreamingToken(page, 'Hello');
    await waitForStreamingEnd(page);

    await expect(page.getByText('Hello! How can I help?')).toBeVisible();
  });

  test('[P1] 11.3-E2E-002: streaming response preserves products, sources, and quick replies', async ({ page }) => {
    const mockProduct = createMockProduct({
      title: 'Streaming Widget Product',
      price: 39.99,
    });

    await mockStreamingWebSocket(page, createStreamingBuilder()
      .withMessageId('msg-stream-002')
      .withTokens(['Here', ' ', 'is', ' ', 'a', ' ', 'product', '!'])
      .withFinalContent('Here is a product!')
      .withProducts([mockProduct])
      .withSources([{ title: 'Product Catalog', url: 'https://example.com/catalog' }])
      .withQuickReplies([
        { text: 'Add to cart', action: 'add_to_cart', value: mockProduct.variant_id },
        { text: 'See similar', action: 'search', value: 'similar products' },
      ]));

    await loadWidgetWithSession(page, 'test-streaming-session');

    const bubble = page.getByRole('button', { name: 'Open chat' });
    await bubble.click();
    await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();

    await sendMessage(page, 'show me products');
    await waitForStreamingEnd(page);

    await expect(page.getByText('Here is a product!')).toBeVisible();
    await expect(page.getByText('Streaming Widget Product')).toBeVisible();
    await expect(page.getByText('$39.99')).toBeVisible();
    await expect(page.getByTestId(/quick-reply-button/).first()).toBeVisible();
  });

  test('[P1] 11.3-E2E-003: new streaming message replaces active stream content', async ({ page }) => {
    const builders = [
      createStreamingBuilder()
        .withMessageId('msg-stream-003a')
        .withTokens(['First', ' response'])
        .withFinalContent('First response'),
      createStreamingBuilder()
        .withMessageId('msg-stream-003b')
        .withTokens(['Second', ' response'])
        .withFinalContent('Second response'),
    ];
    let httpMessageCount = 0;
    let wsMessageIndex = 0;

    await page.route('**/api/v1/widget/message', async (route) => {
      httpMessageCount++;
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            message_id: `msg-rest-${httpMessageCount}`,
            sender: 'bot',
            content: '',
            created_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.routeWebSocket('**/ws/**', (ws) => {
      ws.onMessage((msg) => {
        const str = typeof msg === 'string' ? msg : msg.toString();
        try {
          const parsed = JSON.parse(str);
          if (parsed.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch {}
      });

      const pollAndSend = () => {
        if (wsMessageIndex < httpMessageCount && wsMessageIndex < builders.length) {
          const events = builders[wsMessageIndex].build();
          wsMessageIndex++;
          let i = 0;
          const sendNext = () => {
            if (i < events.length) {
              ws.send(JSON.stringify({ type: events[i].type, data: events[i].data }));
              i++;
              if (i < events.length) {
                setTimeout(sendNext, 100);
              } else {
                setTimeout(pollAndSend, 50);
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

    await sendMessage(page, 'first question');
    await waitForStreamingStart(page);
    await waitForStreamingEnd(page);
    await expect(page.getByText('First response')).toBeVisible();

    await sendMessage(page, 'second question');
    await expect(page.getByText('Second response')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('First response')).toBeVisible();

    const finalizedMessages = page.locator('[data-testid="message-bubble"]');
    expect(await finalizedMessages.count()).toBeGreaterThanOrEqual(2);
  });

  test('[P2] 11.3-E2E-004: sequential streaming messages display in order', async ({ page }) => {
    const builders = [
      createStreamingBuilder()
        .withMessageId('msg-stream-004a')
        .withTokens(['Hello', ' there', '!'])
        .withFinalContent('Hello there!'),
      createStreamingBuilder()
        .withMessageId('msg-stream-004b')
        .withTokens(['Nice', ' to', ' meet', ' you', '.'])
        .withFinalContent('Nice to meet you.'),
    ];
    let httpMessageCount = 0;
    let wsMessageIndex = 0;

    await page.route('**/api/v1/widget/message', async (route) => {
      httpMessageCount++;
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            message_id: `msg-rest-${httpMessageCount}`,
            sender: 'bot',
            content: '',
            created_at: new Date().toISOString(),
          },
        }),
      });
    });

    await page.routeWebSocket('**/ws/**', (ws) => {
      ws.onMessage((msg) => {
        const str = typeof msg === 'string' ? msg : msg.toString();
        try {
          const parsed = JSON.parse(str);
          if (parsed.type === 'ping') {
            ws.send(JSON.stringify({ type: 'pong' }));
          }
        } catch {}
      });

      const pollAndSend = () => {
        if (wsMessageIndex < httpMessageCount && wsMessageIndex < builders.length) {
          const events = builders[wsMessageIndex].build();
          wsMessageIndex++;
          let i = 0;
          const sendNext = () => {
            if (i < events.length) {
              ws.send(JSON.stringify({ type: events[i].type, data: events[i].data }));
              i++;
              if (i < events.length) {
                setTimeout(sendNext, 100);
              } else {
                setTimeout(pollAndSend, 50);
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

    await sendMessage(page, 'greeting');
    await waitForStreamingStart(page);
    await waitForStreamingEnd(page);
    await expect(page.getByText('Hello there!')).toBeVisible();

    await sendMessage(page, 'nice to meet you');
    await expect(page.getByText('Nice to meet you.')).toBeVisible({ timeout: 10000 });

    await expect(page.getByText('Hello there!')).toBeVisible();

    const botMessages = page.locator('[data-testid="message-bubble"].message-bubble--bot');
    expect(await botMessages.count()).toBeGreaterThanOrEqual(2);
  });

  test('[P1] 11.3-E2E-005: streaming indicator appears during active stream', async ({ page }) => {
    await mockWebSocketStream(page, [
      { type: STREAM_EVENTS.START, data: { message_id: 'msg-indicator-001' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: 'Loading', message_id: 'msg-indicator-001' } },
      { type: STREAM_EVENTS.TOKEN, data: { token: '...', message_id: 'msg-indicator-001' } },
      { type: STREAM_EVENTS.END, data: { message_id: 'msg-indicator-001', content: 'Loading...' } },
    ], { delay: 100 });

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
