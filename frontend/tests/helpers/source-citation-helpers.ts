/**
 * Shared Mock Setup for Source Citation Tests
 *
 * Story 10-1: Source Citations Widget
 * Provides reusable mock setup for all source citation test files
 *
 * @tags helper mocks source-citations story-10-1
 */

import { Page, Route } from '@playwright/test';

export type SourceDocumentType = 'pdf' | 'url' | 'text';

export interface SourceCitation {
  documentId: number;
  title: string;
  documentType: SourceDocumentType;
  relevanceScore: number;
  url?: string;
  chunkIndex?: number;
}

export interface WidgetMessageResponse {
  messageId: string;
  content: string;
  sender: 'bot' | 'user';
  createdAt: string;
  sources?: SourceCitation[];
}

export interface MockSourceResponseOptions {
  sources?: SourceCitation[];
  content?: string;
  messageId?: string;
  includeSources?: boolean;
  delay?: number;
  networkError?: boolean;
  serverError?: boolean;
  invalidData?: boolean;
}

const defaultSources: SourceCitation[] = [
  {
    documentId: 1,
    title: 'Product Manual.pdf',
    documentType: 'pdf',
    relevanceScore: 0.95,
    chunkIndex: 5,
  },
  {
    documentId: 2,
    title: 'FAQ Page',
    documentType: 'url',
    relevanceScore: 0.88,
    url: 'https://example.com/faq',
  },
  {
    documentId: 3,
    title: 'Notes.txt',
    documentType: 'text',
    relevanceScore: 0.75,
  },
];

export function createMockSource(overrides: Partial<SourceCitation> = {}): SourceCitation {
  const defaults = defaultSources[0];
  return {
    ...defaults,
    ...overrides,
  };
}

export function createMockSources(count: number, overrides: Partial<SourceCitation>[] = []): SourceCitation[] {
  return Array.from({ length: count }, (_, i) => {
    const override = overrides[i] || {};
    return createMockSource({
      documentId: i + 1,
      title: `Document ${i + 1}`,
      documentType: (['pdf', 'url', 'text'] as const)[i % 3],
      relevanceScore: Math.max(0.5, 0.95 - i * 0.05),
      url: i % 3 === 1 ? `https://example.com/doc-${i + 1}` : undefined,
      ...override,
    });
  });
}

export function createWidgetMessageResponse(options: MockSourceResponseOptions = {}): WidgetMessageResponse {
  const {
    sources = defaultSources,
    content = 'Based on our documentation...',
    messageId = `test-msg-${Date.now()}`,
    includeSources = true,
  } = options;

  const response: WidgetMessageResponse = {
    messageId,
    content,
    sender: 'bot',
    createdAt: new Date().toISOString(),
  };

  if (includeSources) {
    response.sources = sources;
  }

  return response;
}

export async function mockSourceResponse(route: Route, options: MockSourceResponseOptions = {}) {
  const { delay, networkError, serverError, invalidData } = options;

  if (networkError) {
    await route.abort('failed');
    return;
  }

  if (serverError) {
    await route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: 'Internal server error',
      }),
    });
    return;
  }

  if (delay) {
    await new Promise((resolve) => setTimeout(resolve, delay));
  }

  const responseData = invalidData
    ? {
        data: {
          messageId: 'invalid',
          content: 'Response',
          sender: 'bot',
          createdAt: new Date().toISOString(),
          sources: [{ invalidField: true }],
        },
        meta: { requestId: 'test-123', timestamp: new Date().toISOString() },
      }
    : {
        data: createWidgetMessageResponse(options),
        meta: { requestId: 'test-123', timestamp: new Date().toISOString() },
      };

  await route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(responseData),
  });
}

const defaultConfig = {
  enabled: true,
  botName: 'Test Bot',
  welcomeMessage: 'Hello! How can I help you?',
  theme: {
    primaryColor: '#6366f1',
    backgroundColor: '#ffffff',
    textColor: '#1f2937',
    botBubbleColor: '#f3f4f6',
    userBubbleColor: '#6366f1',
    position: 'bottom-right',
    borderRadius: 16,
    width: 380,
    height: 600,
    fontFamily: 'Inter, sans-serif',
    fontSize: 14,
  },
  allowedDomains: [],
};

const defaultSession = {
  sessionId: 'test-session-123',
  merchantId: 4,
  expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
  createdAt: new Date().toISOString(),
  lastActivityAt: new Date().toISOString(),
};

export async function setupSourceCitationMocks(page: Page, options: MockSourceResponseOptions = {}) {
  // Mock config endpoint
  await page.route('**/api/v1/widget/config/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: defaultConfig,
        meta: { requestId: 'config-123', timestamp: new Date().toISOString() },
      }),
    });
  });

  // Mock session endpoint
  await page.route('**/api/v1/widget/session**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: defaultSession,
        meta: { requestId: 'session-123', timestamp: new Date().toISOString() },
      }),
    });
  });

  // Mock message endpoint
  await page.route('**/api/v1/widget/message', async (route) => {
    await mockSourceResponse(route, options);
  });
}

export function getScoreColor(score: number): string {
  if (score >= 0.9) return '#22c55e';
  if (score >= 0.7) return '#3b82f6';
  return '#6b7280';
}

export function formatScore(score: number): string {
  return `${Math.round(score * 100)}%`;
}

export { defaultSources };
