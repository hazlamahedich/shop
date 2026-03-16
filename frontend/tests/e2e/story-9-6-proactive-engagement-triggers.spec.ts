import { test, expect, Page, Locator } from '@playwright/test';
import { WidgetMessage, WidgetCart, WidgetProduct } from '../../src/widget/types/widget';



const TEST_SESSION_ID = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';

interface ProactiveEngagementConfig {
  enabled: boolean;
  triggers: Array<{
    type: 'exit_intent' | 'time_on_page' | 'scroll_depth' | 'product_view' | 'cart_abandonment';
    enabled: boolean;
    threshold?: number;
    message: string;
    actions: Array<{ text: string; prePopulatedMessage?: string }>;
    cooldown: number;
  }>;
}

interface WidgetMockConfig {
  proactiveEngagementConfig?: ProactiveEngagementConfig;
  messagesWithCart?: boolean;
  messagesWithProducts?: number;
  mockHistory?: WidgetMessage[];
}

const DEFAULT_PROACTIVE_CONFIG: ProactiveEngagementConfig = {
  enabled: true,
  triggers: [
    {
      type: 'exit_intent',
      enabled: true,
      message: 'Wait! Before you go, can we help you find something?',
      actions: [
        { text: 'Get Help', prePopulatedMessage: 'I need help finding a product.' },
        { text: 'No thanks' },
      ],
      cooldown: 30,
    }
  ]
};

async function setupWidgetMocks(page: Page, options: WidgetMockConfig = {}): Promise<void> {
  const messages: WidgetMessage[] = [];

  if (options.mockHistory) {
    messages.push(...options.mockHistory);
  }

  if (options.messagesWithCart) {
    messages.push({
      messageId: 'mock-cart-msg',
      sender: 'bot',
      content: 'Here are your cart items',
      createdAt: new Date().toISOString(),
      cart: {
        items: [
          { variantId: 'var-1', title: 'Test Product', price: 29.99, quantity: 1 }
        ],
        itemCount: 1,
        total: 29.99
      }
    });
  }

  if (options.messagesWithProducts && options.messagesWithProducts > 0) {
    for (let i = 0; i < options.messagesWithProducts; i++) {
      messages.push({
        messageId: `mock-prod-msg-${i}`,
        sender: 'bot',
        content: `Here is product ${i + 1}`,
        createdAt: new Date().toISOString(),
        products: [
          { id: `prod-${i}`, variantId: `var-${i}`, title: `Product ${i + 1}`, price: 10 + i, available: true }
        ]
      });
    }
  }

  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          enabled: true,
          botName: 'Shopping Assistant',
          welcomeMessage: 'Hello! How can I help you?',
          proactiveEngagementConfig: options.proactiveEngagementConfig ?? DEFAULT_PROACTIVE_CONFIG,
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
            fontSize: 14
          }
        }
      })
    });
  });

  await page.route('**/api/v1/widget/session/*/messages', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          messages
        }
      })
    });
  });

  await page.route('**/api/v1/widget/session/*', async (route) => {
    const request = route.request();
    if (!request.url().includes('/messages')) {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            session_id: TEST_SESSION_ID,
            merchant_id: '4',
            expires_at: new Date(Date.now() + 3600000).toISOString(),
            created_at: new Date().toISOString()
          }
        })
      });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          session_id: TEST_SESSION_ID,
          merchant_id: '4',
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          created_at: new Date().toISOString()
        }
      })
    });
  });
}

async function loadWidgetPage(page: Page, options: WidgetMockConfig = {}): Promise<void> {
  console.log('[E2E Test] Loading widget page with injected session:', TEST_SESSION_ID);
  
  // Set storage for other parts of the app that might need it
  await page.addInitScript((sessionId) => {
    sessionStorage.setItem('widget_session_id', sessionId);
  }, TEST_SESSION_ID);
  
  await setupWidgetMocks(page, options);
  await page.goto(`/widget-test?sessionId=${TEST_SESSION_ID}`);
  await page.waitForLoadState('networkidle');

  const chatBubble = page.locator('.shopbot-chat-bubble');
  await chatBubble.waitFor({ state: 'visible', timeout: 10000 });

  await page.evaluate(() => {
    sessionStorage.removeItem('widget-proactive-dismissed');
    sessionStorage.removeItem('widget-proactive-cooldown');
  });
}

async function loadWidgetPageWithHistory(page: Page, options: WidgetMockConfig = {}): Promise<void> {
  await loadWidgetPage(page, options);
  // Add a small delay to ensure history is loaded and triggers can fire
  await page.waitForTimeout(1000);
}

async function waitForProactiveModal(page: Page): Promise<Locator> {
  const modal = page.locator('[data-testid="proactive-modal"]');
  await expect(modal).toBeVisible({ timeout: 10000 });
  return modal;
}

test.describe('Story 9-6: Proactive Engagement Triggers', () => {
  test.describe('AC1: Exit Intent Detection', () => {
    test('9.6-E2E-001: should show modal on mouseleave at viewport top', async ({ page }) => {
      await loadWidgetPage(page)

      await page.mouse.move(100, 100)
      await page.mouse.move(100, -10)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()
    })
  })

  test.describe('AC4: Cart Abandonment Trigger', () => {
    test('9.6-E2E-018: should trigger when exiting with items in cart [P1]', async ({ page }) => {
      await loadWidgetPageWithHistory(page, {
        messagesWithCart: true,
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'cart_abandonment',
              enabled: true,
              message: 'You have items in your cart! Can we help you checkout?',
              actions: [{ text: 'Checkout Now', prePopulatedMessage: 'I want to checkout' }],
              cooldown: 30
            }
          ]
        }
      })
      await page.mouse.move(100, 100)
      // Trigger exit intent by dispatching mouseleave on document
      await page.evaluate(() => {
        document.dispatchEvent(new MouseEvent('mouseleave', {
          bubbles: true,
          cancelable: true,
          view: window,
          clientY: -1,
          clientX: 100
        }));
      });

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).toBeVisible({ timeout: 5000 })
    })
  })

  test.describe('AC5: Product View Trigger', () => {
    test('9.6-E2E-020: should trigger after viewing threshold products [P1]', async ({ page }) => {
      await loadWidgetPageWithHistory(page, {
        messagesWithProducts: 3,
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'product_view',
              enabled: true,
              threshold: 3,
              message: 'You viewed 3 products!',
              actions: [{ text: 'Get Help', prePopulatedMessage: 'Help me choose' }],
              cooldown: 60
            }
          ]
        }
      })

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).toBeVisible({ timeout: 5000 })
    })
  })
})
