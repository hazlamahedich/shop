/**
 * Widget Test Helpers
 *
 * Shared utilities for Story 5-10 widget tests.
 * Provides common mocks, fixtures, and assertion helpers.
 *
 * @see tests/helpers/test-health-check.ts for existing helpers
 */

import { Page, APIRequestContext } from '@playwright/test';

export const WIDGET_CONFIG_DEFAULTS = {
  enabled: true,
  botName: 'Shopping Assistant',
  welcomeMessage: 'Hello! What can I help you find?',
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

export interface MockWidgetConfigOptions {
  botName?: string;
  welcomeMessage?: string;
  personalityType?: 'friendly' | 'professional' | 'enthusiastic';
  customGreetingEnabled?: boolean;
  enabled?: boolean;
  theme?: Partial<typeof WIDGET_CONFIG_DEFAULTS.theme>;
}

export async function mockWidgetConfig(page: Page, options: MockWidgetConfigOptions = {}) {
  const config = {
    ...WIDGET_CONFIG_DEFAULTS,
    ...options,
    theme: {
      ...WIDGET_CONFIG_DEFAULTS.theme,
      ...options.theme,
    },
  };

  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ config }),
    });
  });

  return config;
}

export async function mockWidgetSession(page: Page, sessionId?: string) {
  const id = sessionId || crypto.randomUUID();
  const now = new Date();
  const expiresAt = new Date(now.getTime() + 60 * 60 * 1000);

  await page.route('**/api/v1/widget/session', async (route) => {
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          session: {
            session_id: id,
            merchant_id: '1',
            expires_at: expiresAt.toISOString(),
            created_at: now.toISOString(),
            last_activity_at: now.toISOString(),
          },
        }),
      });
    } else {
      await route.continue();
    }
  });

  return id;
}

export async function blockShopifyCalls(page: Page) {
  await page.route('**/*.myshopify.com/**', (route) => route.abort());
}

export interface MockMessageResponse {
  content: string;
  intent?: string;
  confidence?: number;
  products?: Array<{
    id: string;
    variant_id: string;
    title: string;
    price: number;
    available?: boolean;
  }>;
  cart?: {
    items: Array<{
      variant_id: string;
      title: string;
      price: number;
      quantity: number;
    }>;
    item_count: number;
    total: number;
  };
  checkout_url?: string;
  consent_required?: boolean;
  budget_exceeded?: boolean;
  hybrid_ignored?: boolean;
}

export async function mockWidgetMessage(page: Page, response: MockMessageResponse) {
  await page.route('**/api/v1/widget/message', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        message: {
          message_id: crypto.randomUUID(),
          sender: 'bot',
          created_at: new Date().toISOString(),
          ...response,
        },
      }),
    });
  });
}

export async function mockWidgetMessageConditional(
  page: Page,
  handlers: Array<{
    match: (message: string) => boolean;
    response: MockMessageResponse;
  }>
) {
  await page.route('**/api/v1/widget/message', async (route) => {
    const body = route.request().postDataJSON();
    const message = body?.message?.toLowerCase() || '';

    for (const handler of handlers) {
      if (handler.match(message)) {
        await route.fulfill({
          status: 200,
          body: JSON.stringify({
            message: {
              message_id: crypto.randomUUID(),
              sender: 'bot',
              created_at: new Date().toISOString(),
              ...handler.response,
            },
          }),
        });
        return;
      }
    }

    await route.continue();
  });
}

export async function openWidgetChat(page: Page) {
  await page.goto('/widget-test');
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  return {
    input: page.getByPlaceholder('Type a message...'),
    bubble,
  };
}

export async function sendMessage(page: Page, message: string) {
  const input = page.getByPlaceholder('Type a message...');
  await input.fill(message);
  await input.press('Enter');
}

export async function createApiSession(request: APIRequestContext, merchantId = 1): Promise<string | null> {
  const response = await request.post('http://localhost:8000/api/v1/widget/session', {
    data: { merchant_id: merchantId },
    headers: {
      'Content-Type': 'application/json',
      'X-Test-Mode': 'true',
    },
  });

  if (response.status() === 200 || response.status() === 201) {
    const body = await response.json();
    return body.data?.sessionId || body.data?.session_id || body.session?.session_id;
  }

  return null;
}

export function getApiHeaders(testMode = true): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'X-Test-Mode': testMode ? 'true' : 'false',
  };
}

export const ERROR_CODES = {
  WIDGET_CART_EMPTY: 12020,
  WIDGET_NO_SHOPIFY: 12021,
  WIDGET_CHECKOUT_FAILED: 8009,
  WIDGET_SHOPIFY_RATE_LIMITED: 8010,
  WIDGET_SESSION_INVALID: 8011,
  LLM_CONFIG_MISSING: 8012,
  RATE_LIMIT_EXCEEDED: 14029,
  UNAUTHORIZED: 14001,
  NOT_FOUND: 14004,
  INTERNAL_ERROR: 15000,
} as const;

export interface MockProduct {
  id: string;
  variant_id: string;
  title: string;
  price: number;
  image_url?: string;
  available?: boolean;
  product_type?: string;
}

export interface MockCartItem {
  variant_id: string;
  title: string;
  price: number;
  quantity: number;
}

export interface MockCart {
  items: MockCartItem[];
  item_count: number;
  total: number;
}

export function createMockProduct(overrides: Partial<MockProduct> = {}): MockProduct {
  return {
    id: crypto.randomUUID(),
    variant_id: crypto.randomUUID(),
    title: 'Test Product',
    price: 29.99,
    image_url: 'https://example.com/product.jpg',
    available: true,
    product_type: 'Test',
    ...overrides,
  };
}

export function createMockProducts(count: number, overrides: Partial<MockProduct> = {}): MockProduct[] {
  return Array.from({ length: count }, (_, i) =>
    createMockProduct({
      title: `Test Product ${i + 1}`,
      price: 19.99 + i * 10,
      ...overrides,
    })
  );
}

export function createMockCartItem(overrides: Partial<MockCartItem> = {}): MockCartItem {
  return {
    variant_id: crypto.randomUUID(),
    title: 'Cart Item',
    price: 19.99,
    quantity: 1,
    ...overrides,
  };
}

export function createMockCart(items: MockCartItem[] = []): MockCart {
  const cartItems = items.length > 0 ? items : [createMockCartItem()];
  const total = cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const itemCount = cartItems.reduce((sum, item) => sum + item.quantity, 0);

  return {
    items: cartItems,
    item_count: itemCount,
    total,
  };
}

export function createMockMessageResponse(overrides: Partial<MockMessageResponse> = {}): MockMessageResponse {
  return {
    content: 'This is a mock response',
    intent: 'fallback',
    confidence: 0.85,
    ...overrides,
  };
}
