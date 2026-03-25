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
          botName: 'Mantisbot',
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
  
  // Wait for config API response before proceeding (network-first pattern)
  const configPromise = page.waitForResponse('**/api/v1/widget/config/*');
  await page.goto(`/widget-test?sessionId=${TEST_SESSION_ID}`);
  await configPromise;

  // Wait for chat bubble to be visible (deterministic wait for UI ready)
  const chatBubble = page.locator('.shopbot-chat-bubble');
  await chatBubble.waitFor({ state: 'visible', timeout: 10000 });

  await page.evaluate(() => {
    sessionStorage.removeItem('widget-proactive-dismissed');
    sessionStorage.removeItem('widget-proactive-cooldown');
  });
}

async function loadWidgetPageWithHistory(page: Page, options: WidgetMockConfig = {}): Promise<void> {
  await loadWidgetPage(page, options);
  // Wait for widget initialization to complete (deterministic)
  await page.waitForFunction(() => {
    const bubble = document.querySelector('.shopbot-chat-bubble');
    return bubble !== null && document.readyState === 'complete';
  }, { timeout: 5000 });
}

async function waitForProactiveModal(page: Page): Promise<Locator> {
  const modal = page.locator('[data-testid="proactive-modal"]');
  await expect(modal).toBeVisible({ timeout: 10000 });
  return modal;
}

async function triggerExitIntent(page: Page): Promise<void> {
  await page.evaluate(() => {
    document.dispatchEvent(new MouseEvent('mouseleave', {
      bubbles: true,
      cancelable: true,
      view: window,
      clientY: -1,
      clientX: 100
    }));
  });
}

test.describe('Story 9-6: Proactive Engagement Triggers', () => {
  test.describe('AC1: Exit Intent Detection', () => {
    test('9.6-E2E-001: should show modal on mouseleave at viewport top', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()
    })
  })

  test.describe('AC2: Time on Page Trigger', () => {
    test('9.6-E2E-002: should trigger after time threshold [P2]', async ({ page }) => {
      // Install clock before loading page to control time
      await page.clock.install({ time: new Date('2024-01-01T00:00:00Z') });
      
      await loadWidgetPage(page, {
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'time_on_page',
              enabled: true,
              threshold: 5, // 5 seconds for faster test
              message: 'Still here? Can we help you find something?',
              actions: [{ text: 'Get Help', prePopulatedMessage: 'I need assistance.' }],
              cooldown: 30
            }
          ]
        }
      })

      // Fast-forward time past the threshold
      await page.clock.fastForward(6000);

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).toBeVisible({ timeout: 5000 })
    })

    test('9.6-E2E-003: should not trigger before time threshold [P2]', async ({ page }) => {
      await page.clock.install({ time: new Date('2024-01-01T00:00:00Z') });
      
      await loadWidgetPage(page, {
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'time_on_page',
              enabled: true,
              threshold: 30, // 30 seconds
              message: 'Still here?',
              actions: [{ text: 'OK' }],
              cooldown: 30
            }
          ]
        }
      })

      // Fast-forward only 10 seconds (less than 30 second threshold)
      await page.clock.fastForward(10000);

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).not.toBeVisible({ timeout: 1000 })
    })
  })

  test.describe('AC3: Scroll Depth Trigger', () => {
    test('9.6-E2E-004: should trigger at scroll threshold [P2]', async ({ page }) => {
      await loadWidgetPage(page, {
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'scroll_depth',
              enabled: true,
              threshold: 50, // 50% scroll
              message: 'Finding what you need?',
              actions: [{ text: 'Get Help', prePopulatedMessage: 'I have a question.' }],
              cooldown: 30
            }
          ]
        }
      })

      // Simulate scroll to 60% (past 50% threshold)
      await page.evaluate(() => {
        // Create scrollable content
        document.body.style.height = '3000px';
        window.scrollTo(0, 1800); // 60% of 3000px
        // Dispatch scroll event
        window.dispatchEvent(new Event('scroll', { bubbles: true }));
      });

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).toBeVisible({ timeout: 5000 })
    })

    test('9.6-E2E-005: should not trigger before scroll threshold [P2]', async ({ page }) => {
      await loadWidgetPage(page, {
        proactiveEngagementConfig: {
          enabled: true,
          triggers: [
            {
              type: 'scroll_depth',
              enabled: true,
              threshold: 75, // 75% scroll
              message: 'Finding what you need?',
              actions: [{ text: 'OK' }],
              cooldown: 30
            }
          ]
        }
      })

      // Simulate scroll to only 30% (less than 75% threshold)
      await page.evaluate(() => {
        document.body.style.height = '3000px';
        window.scrollTo(0, 900); // 30% of 3000px
        window.dispatchEvent(new Event('scroll', { bubbles: true }));
      });

      const modal = page.locator('[data-testid="proactive-modal"]');
      await expect(modal).not.toBeVisible({ timeout: 1000 })
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
      await triggerExitIntent(page)

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

  test.describe('AC8: Modal Actions', () => {
    test('9.6-E2E-021: should open chat with pre-populated message on action click [P1]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()

      await page.click('[data-testid="proactive-action-button-0"]')

      const chatWindow = page.locator('.shopbot-chat-window')
      await expect(chatWindow).toBeVisible({ timeout: 5000 })

      await expect(modal).not.toBeVisible({ timeout: 2000 })
    })
  })

  test.describe('AC9: Dismiss Functionality', () => {
    test('9.6-E2E-022: should close modal on dismiss and keep chat closed [P1]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()

      await page.click('[data-testid="proactive-dismiss-button"]')

      await expect(modal).not.toBeVisible({ timeout: 2000 })

      const chatWindow = page.locator('.shopbot-chat-window')
      await expect(chatWindow).not.toBeVisible()
    })

    test('9.6-E2E-023: should not re-trigger after dismiss in same session [P1]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()

      await page.click('[data-testid="proactive-dismiss-button"]')
      await expect(modal).not.toBeVisible({ timeout: 2000 })

      await triggerExitIntent(page)

      await page.waitForTimeout(500)
      await expect(modal).not.toBeVisible()
    })
  })

  test.describe('AC10: Accessibility Compliance', () => {
    test('9.6-E2E-024: should have correct aria attributes [P1]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);

      await expect(modal).toHaveAttribute('role', 'dialog')
      await expect(modal).toHaveAttribute('aria-modal', 'true')
      await expect(modal).toHaveAttribute('aria-labelledby', 'proactive-title')
      await expect(modal).toHaveAttribute('aria-describedby', 'proactive-message')
    })

    test('9.6-E2E-025: should close on Escape key [P1]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()

      await page.keyboard.press('Escape')

      await expect(modal).not.toBeVisible({ timeout: 2000 })
    })

    test('9.6-E2E-026: should close on overlay click [P2]', async ({ page }) => {
      await loadWidgetPage(page)

      await triggerExitIntent(page)

      const modal = await waitForProactiveModal(page);
      await expect(modal).toBeVisible()

      await modal.click({ position: { x: 5, y: 5 } })

      await expect(modal).not.toBeVisible({ timeout: 2000 })
    })
  })
})
