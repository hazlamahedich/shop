/**
 * Conversation History E2E Tests
 *
 * Story 4-8: Conversation History View
 * Tests the complete user journey for viewing conversation history with context
 * Uses authenticated page fixture with mocked auth state
 *
 * @tags e2e conversation-history story-4-8
 */

import { test as base, expect } from '@playwright/test';

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
};

const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Mock auth API to return valid session
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'test-merchant-1',
            email: 'test@test.com',
            name: 'Test Merchant',
            hasStoreConnected: false,
          },
          meta: {
            sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
          },
        }),
      });
    });

    // Set localStorage BEFORE page loads using addInitScript
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 'test-merchant-1',
          email: 'test@test.com',
          name: 'Test Merchant',
          hasStoreConnected: false,
        },
        sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        isLoading: false,
        error: null,
      };

      const mockOnboardingState = {
        state: {
          completedSteps: ['prerequisites', 'deployment', 'integrations', 'bot-config'],
          currentPhase: 'complete',
          personalityConfigured: true,
          businessInfoConfigured: true,
          botNamed: true,
          greetingsConfigured: true,
          pinsConfigured: true,
          isFullyOnboarded: true,
          onboardingCompletedAt: new Date().toISOString(),
        },
        version: 0,
      };

      const mockTutorialState = {
        state: {
          isStarted: true,
          isCompleted: true,
          isSkipped: false,
          currentStep: 0,
          completedSteps: [],
        },
        version: 0,
      };

      localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));
      localStorage.setItem('shop_onboarding_phase_progress', JSON.stringify(mockOnboardingState));
      localStorage.setItem('tutorial-storage', JSON.stringify(mockTutorialState));
    });

    await use(page);
  },
});

const createTestHistoryMessage = (overrides: {
  id?: number;
  sender?: 'customer' | 'bot';
  content?: string;
  createdAt?: string;
  confidenceScore?: number | null;
} = {}) => ({
  id: overrides.id ?? 1,
  sender: overrides.sender ?? 'customer',
  content: overrides.content ?? 'Test message',
  createdAt: overrides.createdAt ?? new Date().toISOString(),
  confidenceScore: overrides.confidenceScore ?? null,
});

const createTestHistoryResponse = (overrides: {
  conversationId?: number;
  messages?: ReturnType<typeof createTestHistoryMessage>[];
  context?: object;
  handoff?: object;
  customer?: object;
} = {}) => ({
  data: {
    conversationId: overrides.conversationId ?? 1,
    messages: overrides.messages ?? [createTestHistoryMessage()],
    context: overrides.context ?? {
      cartState: null,
      extractedConstraints: null,
    },
    handoff: overrides.handoff ?? {
      triggerReason: 'keyword',
      triggeredAt: new Date(Date.now() - 300000).toISOString(),
      urgencyLevel: 'medium',
      waitTimeSeconds: 300,
    },
    customer: overrides.customer ?? {
      maskedId: '1234****',
      orderCount: 0,
    },
  },
  meta: {
    requestId: 'test-request-id',
    timestamp: new Date().toISOString(),
  },
});

test.describe('Conversation History E2E Journey', () => {
  test('[P0] @smoke should display conversation history page', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          messages: [
            createTestHistoryMessage({ id: 1, sender: 'customer', content: 'Hello' }),
            createTestHistoryMessage({ id: 2, sender: 'bot', content: 'Hi there!', confidenceScore: 0.95 }),
          ],
        })),
      });
    });

    await page.goto('/conversations/1/history');

    await expect(page.getByTestId('conversation-history-page')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Conversation History' })).toBeVisible();
  });

  test('[P0] should display messages in chronological order', async ({ authenticatedPage: page }) => {
    const baseTime = Date.now() - 600000;
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          messages: [
            createTestHistoryMessage({
              id: 1,
              sender: 'customer',
              content: 'First message',
              createdAt: new Date(baseTime).toISOString(),
            }),
            createTestHistoryMessage({
              id: 2,
              sender: 'bot',
              content: 'Second message',
              createdAt: new Date(baseTime + 10000).toISOString(),
              confidenceScore: 0.9,
            }),
            createTestHistoryMessage({
              id: 3,
              sender: 'customer',
              content: 'Third message',
              createdAt: new Date(baseTime + 30000).toISOString(),
            }),
          ],
        })),
      });
    });

    await page.goto('/conversations/1/history');

    const messages = page.getByTestId('message-bubble');
    await expect(messages).toHaveCount(3);

    const messageContents = await messages.allTextContents();
    expect(messageContents[0]).toContain('First message');
    expect(messageContents[1]).toContain('Second message');
    expect(messageContents[2]).toContain('Third message');
  });

  test('[P0] should show confidence score on bot messages', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          messages: [
            createTestHistoryMessage({ id: 1, sender: 'bot', content: 'Bot response', confidenceScore: 0.85 }),
          ],
        })),
      });
    });

    await page.goto('/conversations/1/history');

    const confidenceBadge = page.getByTestId('confidence-badge');
    await expect(confidenceBadge).toBeVisible();
    await expect(confidenceBadge).toContainText('85%');
  });

  test('[P0] should visually distinguish shopper and bot messages', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          messages: [
            createTestHistoryMessage({ id: 1, sender: 'customer', content: 'Customer message' }),
            createTestHistoryMessage({ id: 2, sender: 'bot', content: 'Bot message', confidenceScore: 0.9 }),
          ],
        })),
      });
    });

    await page.goto('/conversations/1/history');

    const customerMessage = page.getByTestId('message-bubble').filter({ hasText: 'Customer message' });
    const botMessage = page.getByTestId('message-bubble').filter({ hasText: 'Bot message' });

    await expect(customerMessage).toHaveAttribute('data-sender', 'customer');
    await expect(botMessage).toHaveAttribute('data-sender', 'bot');
  });

  test('[P0] should display context sidebar with handoff info', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          handoff: {
            triggerReason: 'low_confidence',
            triggeredAt: new Date(Date.now() - 900000).toISOString(),
            urgencyLevel: 'high',
            waitTimeSeconds: 900,
          },
        })),
      });
    });

    await page.goto('/conversations/1/history');

    const sidebar = page.getByTestId('context-sidebar');
    await expect(sidebar).toBeVisible();

    await expect(page.getByTestId('customer-info-section')).toBeVisible();
    await expect(page.getByTestId('handoff-context-section')).toBeVisible();
    await expect(page.getByTestId('bot-state-section')).toBeVisible();

    const urgencyBadge = page.getByTestId('urgency-badge');
    await expect(urgencyBadge).toBeVisible();
    await expect(urgencyBadge).toContainText('High');
  });

  test('[P1] should navigate from HandoffQueue to ConversationHistory', async ({ authenticatedPage: page }) => {
    await page.route('**/api/handoff-alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [{
            id: 1,
            conversationId: 123,
            urgencyLevel: 'medium',
            customerName: 'Test Customer',
            waitTimeSeconds: 300,
            isRead: false,
          }],
          meta: { total: 1 },
        }),
      });
    });

    await page.route('**/api/conversations/123/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({ conversationId: 123 })),
      });
    });

    await page.goto('/handoff-queue');

    const queueItem = page.getByTestId('queue-item').first();
    await expect(queueItem).toBeVisible();
    await queueItem.click();

    await expect(page).toHaveURL(/\/conversations\/123\/history/);
    await expect(page.getByTestId('conversation-history-page')).toBeVisible();
  });

  test('[P1] should handle 404 for non-existent conversation', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/99999/history', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 7001,
          message: 'Conversation not found or access denied',
        }),
      });
    });

    await page.goto('/conversations/99999/history');

    await expect(page.getByText(/not found|Failed to load/i)).toBeVisible();
  });

  test('[P2] should display loading state', async ({ authenticatedPage: page }) => {
    let resolvePromise: (value: unknown) => void;
    const responsePromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    await page.route('**/api/conversations/1/history', async (route) => {
      await responsePromise;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse()),
      });
    });

    await page.goto('/conversations/1/history');

    await expect(page.getByText('Loading conversation')).toBeVisible();

    resolvePromise!(undefined);

    await expect(page.getByTestId('conversation-history-page')).toBeVisible();
  });

  test('[P2] should display cart state in sidebar', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse({
          context: {
            cartState: {
              items: [
                { productId: 'prod-1', name: 'Nike Air Max', quantity: 1 },
                { productId: 'prod-2', name: 'Adidas Runner', quantity: 2 },
              ],
            },
            extractedConstraints: {
              budget: '$100-150',
              size: '10',
              category: 'running',
            },
          },
        })),
      });
    });

    await page.goto('/conversations/1/history');

    const botStateSection = page.getByTestId('bot-state-section');
    await expect(botStateSection.getByText('Nike Air Max')).toBeVisible();
    await expect(botStateSection.getByText('x1')).toBeVisible();
    await expect(botStateSection.getByText('$100-150')).toBeVisible();
  });

  test('[P2] should handle back navigation to queue', async ({ authenticatedPage: page }) => {
    await page.route('**/api/handoff-alerts**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [{
            id: 1,
            conversationId: 1,
            urgencyLevel: 'medium',
            customerName: 'Test Customer',
            waitTimeSeconds: 300,
            isRead: false,
          }],
          meta: { total: 1 },
        }),
      });
    });

    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse()),
      });
    });

    // Navigate via handoff queue (which passes location state)
    await page.goto('/handoff-queue');
    await page.getByTestId('queue-item').first().click();
    await expect(page).toHaveURL(/\/conversations\/1\/history/);

    const backButton = page.getByRole('button', { name: /back/i });
    await backButton.click();

    await expect(page).toHaveURL(/\/handoff-queue/);
  });

  test('[P2] should handle back navigation to conversations', async ({ authenticatedPage: page }) => {
    await page.route('**/api/conversations**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [{
            id: 1,
            platformSenderIdMasked: '1234****',
            status: 'active',
            lastMessage: 'Test message',
            messageCount: 5,
            updatedAt: new Date().toISOString(),
          }],
          meta: { total: 1 },
        }),
      });
    });

    await page.route('**/api/conversations/1/history', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createTestHistoryResponse()),
      });
    });

    // Navigate via conversations page (which passes location state)
    await page.goto('/conversations');
    await page.getByTestId('conversation-card').first().click();
    await expect(page).toHaveURL(/\/conversations\/1\/history/);

    const backButton = page.getByRole('button', { name: /back/i });
    await backButton.click();

    await expect(page).toHaveURL(/\/conversations$/);
  });
});
