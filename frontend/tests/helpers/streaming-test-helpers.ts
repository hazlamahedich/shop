import { Page, expect } from '@playwright/test';

export type StreamingToken = string;

export interface StreamingEventConfig {
  wsUrlPattern?: string;
  tokenDelay?: number;
}

interface StreamingEvent {
  type: string;
  data: Record<string, unknown>;
}

export class StreamingMessageBuilder {
  private messageId = `test-${crypto.randomUUID()}`;
  private tokens: string[] = [];
  private finalContent = '';
  private products: unknown[] | undefined;
  private sources: unknown[] | undefined;
  private suggestedReplies: string[] | undefined;
  private quickReplies: unknown[] | undefined;
  private contactOptions: unknown[] | undefined;
  private consentPrompt: boolean | undefined;

  withMessageId(id: string): this {
    this.messageId = id;
    return this;
  }

  withTokens(tokens: string[]): this {
    this.tokens = tokens;
    return this;
  }

  withFinalContent(content: string): this {
    this.finalContent = content;
    return this;
  }

  withProducts(products: unknown[]): this {
    this.products = products;
    return this;
  }

  withSources(sources: unknown[]): this {
    this.sources = sources;
    return this;
  }

  withSuggestedReplies(replies: string[]): this {
    this.suggestedReplies = replies;
    return this;
  }

  withQuickReplies(replies: unknown[]): this {
    this.quickReplies = replies;
    return this;
  }

  withContactOptions(options: unknown[]): this {
    this.contactOptions = options;
    return this;
  }

  withConsentPrompt(required: boolean): this {
    this.consentPrompt = required;
    return this;
  }

  build(): StreamingEvent[] {
    const events: StreamingEvent[] = [];
    const now = new Date().toISOString();

    events.push({
      type: 'bot_stream_start',
      data: {
        messageId: this.messageId,
        sender: 'bot',
        createdAt: now,
      },
    });

    for (const token of this.tokens) {
      events.push({
        type: 'bot_stream_token',
        data: {
          messageId: this.messageId,
          token,
        },
      });
    }

    const endData: Record<string, unknown> = {
      messageId: this.messageId,
      content: this.finalContent || this.tokens.join(''),
      createdAt: new Date().toISOString(),
    };

    if (this.products !== undefined) endData.products = this.products;
    if (this.sources !== undefined) endData.sources = this.sources;
    if (this.suggestedReplies !== undefined) endData.suggestedReplies = this.suggestedReplies;
    if (this.quickReplies !== undefined) endData.quick_replies = this.quickReplies;
    if (this.contactOptions !== undefined) endData.contactOptions = this.contactOptions;
    if (this.consentPrompt !== undefined) endData.consent_prompt_required = this.consentPrompt;

    events.push({
      type: 'bot_stream_end',
      data: endData,
    });

    return events;
  }

  buildError(error: string): StreamingEvent[] {
    return [
      {
        type: 'bot_stream_error',
        data: {
          messageId: this.messageId,
          error,
        },
      },
    ];
  }

  getMessageId(): string {
    return this.messageId;
  }
}

export const STREAM_EVENTS = {
  START: 'bot_stream_start',
  TOKEN: 'bot_stream_token',
  END: 'bot_stream_end',
  ERROR: 'bot_stream_error',
} as const;

export interface StreamedEvent {
  type: string;
  data: Record<string, unknown>;
}

function buildMinimalMessageResponse(): string {
  return JSON.stringify({
    data: {
      message_id: crypto.randomUUID(),
      sender: 'bot',
      content: '',
      created_at: new Date().toISOString(),
    },
  });
}

function sendEventsWithDelay(
  ws: { send: (data: string) => void },
  events: Array<{ type: string; data: Record<string, unknown> }>,
  delay: number
): void {
  let i = 0;
  const sendNext = () => {
    if (i < events.length) {
      ws.send(JSON.stringify({ type: events[i].type, data: events[i].data }));
      i++;
      if (i < events.length && delay > 0) {
        setTimeout(sendNext, delay);
      }
    }
  };
  sendNext();
}

export async function mockStreamingWebSocket(
  page: Page,
  builder: StreamingMessageBuilder,
  options: StreamingEventConfig = {}
): Promise<void> {
  const { wsUrlPattern = '**/ws/**', tokenDelay = 10 } = options;
  const events = builder.build();
  let httpMessageSent = false;

  await page.route('**/api/v1/widget/message', async (route) => {
    httpMessageSent = true;
    await route.fulfill({
      status: 200,
      body: buildMinimalMessageResponse(),
    });
  });

  await page.routeWebSocket(wsUrlPattern, (ws) => {
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
      if (httpMessageSent) {
        sendEventsWithDelay(ws, events, tokenDelay);
      } else {
        setTimeout(pollAndSend, 50);
      }
    };
    pollAndSend();
  });
}

export async function mockWebSocketStream(
  page: Page,
  events: StreamedEvent[],
  options: { wsUrlPattern?: string; delay?: number } = {}
): Promise<void> {
  const { wsUrlPattern = '**/ws/**', delay = 10 } = options;
  let httpMessageSent = false;

  await page.route('**/api/v1/widget/message', async (route) => {
    httpMessageSent = true;
    await route.fulfill({
      status: 200,
      body: buildMinimalMessageResponse(),
    });
  });

  await page.routeWebSocket(wsUrlPattern, (ws) => {
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
      if (httpMessageSent) {
        sendEventsWithDelay(ws, events, delay);
      } else {
        setTimeout(pollAndSend, 50);
      }
    };
    pollAndSend();
  });
}

export async function mockWebSocketFailure(
  page: Page,
  options: { wsUrlPattern?: string } = {}
): Promise<void> {
  const { wsUrlPattern = '**/ws/**' } = options;

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    ws.close({ code: 1006, reason: 'Connection refused' });
  });
}

export interface ReconnectController {
  triggerReconnect(): void;
}

export async function mockWebSocketReconnect(
  page: Page,
  config: {
    firstStreamEvents: StreamedEvent[];
    secondStreamEvents: StreamedEvent[];
    wsUrlPattern?: string;
    delay?: number;
  }
): Promise<ReconnectController> {
  const { firstStreamEvents, secondStreamEvents, wsUrlPattern = '**/ws/**', delay = 10 } = config;
  let connectionIndex = 0;
  let httpMessageCount = 0;
  let wsHandledCount = 0;

  await page.route('**/api/v1/widget/message', async (route) => {
    httpMessageCount++;
    await route.fulfill({
      status: 200,
      body: buildMinimalMessageResponse(),
    });
  });

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    const currentConnection = connectionIndex;
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

    const events = currentConnection === 0 ? firstStreamEvents : secondStreamEvents;

    const pollAndSend = () => {
      if (wsHandledCount < httpMessageCount) {
        wsHandledCount++;
        let i = 0;
        const sendNext = () => {
          if (i < events.length) {
            ws.send(JSON.stringify({ type: events[i].type, data: events[i].data }));
            i++;
            if (i < events.length) {
              setTimeout(sendNext, delay);
            } else if (currentConnection === 0) {
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

  return {
    triggerReconnect() {},
  };
}

export function createStreamingBuilder(): StreamingMessageBuilder {
  return new StreamingMessageBuilder();
}

export function createDefaultStreamingEvents(
  overrides: { content?: string; tokens?: string[]; messageId?: string } = {}
): StreamingEvent[] {
  const { content, tokens, messageId } = overrides;
  const builder = new StreamingMessageBuilder();

  if (messageId) builder.withMessageId(messageId);
  if (tokens) builder.withTokens(tokens);
  if (content) builder.withFinalContent(content);

  return builder.build();
}

export async function waitForStreamingStart(page: Page, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-indicator')).toBeVisible({ timeout });
}

export async function waitForStreamingToken(page: Page, expectedText: string, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-message').getByText(expectedText, { exact: false })).toBeVisible({ timeout });
}

export async function waitForStreamingEnd(page: Page, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-indicator')).toBeHidden({ timeout });
}

export async function waitForWebSocketConnected(page: Page, timeout: number = 10000) {
  await expect(page.getByText(/Connecting\.\.\.|Disconnected|Connection error/)).not.toBeVisible({ timeout });
}

export interface WsTurnConfig {
  type: 'stream' | 'abort';
  events?: StreamedEvent[];
  closeAfter?: boolean;
}

export interface RestTurnConfig {
  match: (message: string) => boolean;
  response: {
    message_id: string;
    sender: string;
    content: string;
  };
}

export interface MultiTurnOptions {
  wsUrlPattern?: string;
  restUrlPattern?: string;
  delay?: number;
  refuseAfter?: number;
}

export async function mockMultiTurnConversation(
  page: Page,
  wsTurns: WsTurnConfig[],
  restResponses: RestTurnConfig[] = [],
  options: MultiTurnOptions = {}
): Promise<void> {
  const { wsUrlPattern = '**/ws/**', restUrlPattern = '**/api/v1/widget/message', delay = 10, refuseAfter } = options;
  let wsMessageIndex = 0;
  let httpMessageCount = 0;
  let connectionIndex = 0;

  await page.route(restUrlPattern, async (route) => {
    httpMessageCount++;
    const body = route.request().postDataJSON();
    const message = body?.message?.toLowerCase() || '';
    const match = restResponses.find((r) => r.match(message));
    if (match) {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          data: {
            ...match.response,
            sender: 'bot',
            created_at: new Date().toISOString(),
          },
        }),
      });
    } else {
      await route.fulfill({
        status: 200,
        body: buildMinimalMessageResponse(),
      });
    }
  });

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    const currentConnection = connectionIndex;
    connectionIndex++;

    if (refuseAfter !== undefined && currentConnection >= refuseAfter) {
      ws.close({ code: 1006, reason: 'Connection refused' });
      return;
    }

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
      if (wsMessageIndex < httpMessageCount && wsMessageIndex < wsTurns.length) {
        const turn = wsTurns[wsMessageIndex];
        wsMessageIndex++;

        if (turn.type === 'stream' && turn.events) {
          let i = 0;
          const sendNext = () => {
            if (i < turn.events!.length) {
              ws.send(JSON.stringify({ type: turn.events![i].type, data: turn.events![i].data }));
              i++;
              if (i < turn.events!.length) {
                setTimeout(sendNext, delay);
              } else if (turn.closeAfter) {
                setTimeout(() => {
                  ws.close({ code: 1006, reason: 'Simulated disconnect' });
                }, 100);
              } else {
                setTimeout(pollAndSend, 50);
              }
            }
          };
          sendNext();
        } else if (turn.type === 'abort') {
          ws.close({ code: 1006, reason: 'Aborting WS connection' });
        } else {
          setTimeout(pollAndSend, 50);
        }
      } else {
        setTimeout(pollAndSend, 50);
      }
    };
    pollAndSend();
  });
}
