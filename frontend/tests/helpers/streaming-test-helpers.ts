import { Page, expect } from '@playwright/test';

export type StreamingToken = string;

export interface StreamingEventConfig {
  sessionId?: string;
  autoRespond?: boolean;
  onMessage?: (message: string) => void;
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

interface WebSocketController {
  sendEvent(event: StreamingEvent): void;
  sendEvents(events: StreamingEvent[], delay?: number): Promise<void>;
  close(code?: number, reason?: string): void;
}

const activeSockets = new WeakMap<Page, WebSocketController>();

export async function mockStreamingWebSocket(
  page: Page,
  options: StreamingEventConfig = {}
): Promise<WebSocketController> {
  const {
    autoRespond = false,
    onMessage,
    wsUrlPattern = '**/ws/**',
    tokenDelay = 0,
  } = options;

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  let storedController: WebSocketController;

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    const controller: WebSocketController = {
      sendEvent(event: StreamingEvent) {
        ws.send(JSON.stringify(event));
      },

      async sendEvents(events: StreamingEvent[], delay: number = tokenDelay) {
        for (const event of events) {
          this.sendEvent(event);
          if (delay > 0) {
            await new Promise((resolve) => setTimeout(resolve, delay));
          }
        }
      },

      close(code?: number, reason?: string) {
        ws.close({ code, reason });
      },
    };

    storedController = controller;
    activeSockets.set(page, controller);

    if (autoRespond) {
      ws.onMessage((message) => {
        const messageStr = typeof message === 'string' ? message : message.toString();
        onMessage?.(messageStr);

        const builder = new StreamingMessageBuilder();
        const events = builder
          .withTokens(['Hello', '! ', 'How', ' ', 'can', ' ', 'I', ' ', 'help', '?'])
          .build();

        controller.sendEvents(events, tokenDelay);
      });
    } else {
      ws.onMessage((message) => {
        const messageStr = typeof message === 'string' ? message : message.toString();
        onMessage?.(messageStr);
      });
    }
  });

  return new Proxy({} as WebSocketController, {
    get(_target, prop) {
      const ctrl = activeSockets.get(page);
      if (!ctrl) {
        throw new Error(
          'No active WebSocket connection. Ensure the page has connected to the WebSocket before calling this method.'
        );
      }
      const value = (ctrl as unknown as Record<string, unknown>)[prop as string];
      if (typeof value === 'function') {
        return value.bind(ctrl);
      }
      return value;
    },
  });
}

export async function simulateStreamingResponse(
  page: Page,
  builder: StreamingMessageBuilder,
  delay: number = 10
): Promise<void> {
  const controller = activeSockets.get(page);
  if (!controller) {
    throw new Error(
      'No active WebSocket mock found. Call mockStreamingWebSocket() first and ensure the page has connected.'
    );
  }

  const events = builder.build();
  await controller.sendEvents(events, delay);
}

export async function waitForStreamingStart(page: Page, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-indicator')).toBeVisible({ timeout });
}

export async function waitForStreamingToken(page: Page, expectedText: string, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-message').getByText(expectedText, { exact: false })).toBeVisible({ timeout });
}

export async function waitForStreamingEnd(page: Page, timeout: number = 10000) {
  await expect(page.getByTestId('streaming-indicator')).toBeHidden({ timeout });
  await expect(page.getByTestId('streaming-message')).toHaveAttribute('data-streaming', 'false', { timeout });
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

export function createProductStreamingEvents(
  overrides: { productCount?: number; basePrice?: number } = {}
): StreamingEvent[] {
  const { productCount = 1, basePrice = 29.99 } = overrides;
  const products = Array.from({ length: productCount }, (_, i) => ({
    id: crypto.randomUUID(),
    variant_id: crypto.randomUUID(),
    title: `Streaming Product ${i + 1}`,
    price: basePrice + i * 10,
    available: true,
  }));

  return new StreamingMessageBuilder()
    .withTokens(['Here', ' ', 'are', ' ', 'some', ' ', 'products', '!'])
    .withProducts(products)
    .build();
}

export function createErrorStreamingEvents(error: string = 'Stream interrupted'): StreamingEvent[] {
  return new StreamingMessageBuilder().buildError(error);
}

export const STREAM_EVENTS = {
  START: 'bot_stream_start',
  TOKEN: 'bot_stream_token',
  END: 'bot_stream_end',
  ERROR: 'bot_stream_error',
} as const;

export interface StreamedEvent {
  event: string;
  data: Record<string, unknown>;
}

export async function mockWebSocketStream(
  page: Page,
  events: StreamedEvent[],
  options: { wsUrlPattern?: string; delay?: number } = {}
): Promise<void> {
  const { wsUrlPattern = '**/ws/**', delay = 5 } = options;

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    ws.onMessage(async () => {
      for (const evt of events) {
        ws.send(JSON.stringify({ type: evt.event, data: evt.data }));
        if (delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    });
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
  const { firstStreamEvents, secondStreamEvents, wsUrlPattern = '**/ws/**', delay = 5 } = config;

  let callCount = 0;

  await page.routeWebSocket(wsUrlPattern, (ws) => {
    callCount++;
    const currentEvents = callCount <= 1 ? firstStreamEvents : secondStreamEvents;

    ws.onMessage(async () => {
      for (const evt of currentEvents) {
        ws.send(JSON.stringify({ type: evt.event, data: evt.data }));
        if (delay > 0) {
          await new Promise((resolve) => setTimeout(resolve, delay));
        }
      }
    });

    if (callCount === 1) {
      setTimeout(() => {
        ws.close({ code: 1006, reason: 'Simulated disconnect' });
      }, currentEvents.length * delay + 50);
    }
  });

  return {
    triggerReconnect() {},
  };
}
