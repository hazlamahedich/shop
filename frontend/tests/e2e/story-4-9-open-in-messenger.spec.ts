/**
 * Open in Messenger Reply E2E Tests
 *
 * Story 4-9: Open in Messenger Reply
 * Tests the complete user journey for opening Messenger conversations and hybrid mode
 * Uses authenticated page fixture with mocked auth state
 *
 * @tags e2e messenger-reply story-4-9
 */

import { test as base, expect } from '@playwright/test';

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
};

const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
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

const createTestConversationHistory = (overrides: {
  conversationId?: number;
  platformSenderId?: string;
  hybridMode?: { enabled: boolean; activatedAt?: string; expiresAt?: string; remainingSeconds?: number };
} = {}) => ({
  data: {
    conversationId: overrides.conversationId ?? 123,
    platformSenderId: overrides.platformSenderId ?? 'test_psid_12345',
    messages: [
      { id: 1, sender: 'customer', content: 'I need help with my order', createdAt: new Date().toISOString(), confidenceScore: null },
      { id: 2, sender: 'bot', content: "I'd be happy to help!", createdAt: new Date().toISOString(), confidenceScore: 0.85 },
    ],
    context: {
      cartState: { items: [] },
      extractedConstraints: null,
    },
    handoff: {
      triggerReason: 'keyword',
      triggeredAt: new Date().toISOString(),
      urgencyLevel: 'high',
      waitTimeSeconds: 120,
    },
    customer: {
      maskedId: 'test****',
      orderCount: 1,
    },
    hybridMode: overrides.hybridMode ?? null,
  },
  meta: {
    requestId: 'test-request-id',
    timestamp: new Date().toISOString(),
  },
});

test.describe('Story 4-9: Open in Messenger Reply', () => {
  test.describe('AC1 & AC2: Open in Messenger Button', () => {
    test('button is visible on handoff conversation page', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory()),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await expect(page.getByTestId('sticky-action-bar')).toBeVisible();
      await expect(page.getByTestId('open-in-messenger-btn')).toBeVisible();
    });

    test('button opens Messenger URL with correct platform_sender_id', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory()),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.route('**/api/conversations/123/hybrid-mode', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              hybridMode: {
                enabled: true,
                activatedAt: new Date().toISOString(),
                activatedBy: 'merchant',
                expiresAt: new Date(Date.now() + 7200000).toISOString(),
                remainingSeconds: 7200,
              },
            },
            meta: {
              requestId: 'test-request-id',
              timestamp: new Date().toISOString(),
            },
          }),
        });
      });

      // Mock window.open to capture URL
      const openedUrls: string[] = [];
      await page.addInitScript(() => {
        (window as any).originalOpen = window.open;
        window.open = (url: string) => {
          (window as any).openedUrl = url;
          return null;
        };
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('open-in-messenger-btn').click();

      // Verify URL was constructed correctly
      const openedUrl = await page.evaluate(() => (window as any).openedUrl);
      expect(openedUrl).toContain('https://m.me/test_page_123');
      expect(openedUrl).toContain('thread_id=test_psid_12345');
    });

    test('button is disabled when no Facebook page connection', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory()),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: false,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      const button = page.getByTestId('open-in-messenger-btn');
      await expect(button).toBeDisabled();
    });
  });

  test.describe('AC4: Bot Hybrid Mode', () => {
    test('hybrid mode API is called when button is clicked', async ({ authenticatedPage: page }) => {
      let hybridModeCalled = false;
      
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory()),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.route('**/api/conversations/123/hybrid-mode', async (route) => {
        hybridModeCalled = true;
        const body = route.request().postDataJSON();
        expect(body.enabled).toBe(true);
        expect(body.reason).toBe('merchant_responding');
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              hybridMode: {
                enabled: true,
                activatedAt: new Date().toISOString(),
                activatedBy: 'merchant',
                expiresAt: new Date(Date.now() + 7200000).toISOString(),
                remainingSeconds: 7200,
              },
            },
            meta: {
              requestId: 'test-request-id',
              timestamp: new Date().toISOString(),
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('open-in-messenger-btn').click();

      await expect.poll(() => hybridModeCalled).toBe(true);
    });

    test('shows empowering message when hybrid mode activates', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory()),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.route('**/api/conversations/123/hybrid-mode', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversationId: 123,
            hybridMode: {
              enabled: true,
              activatedAt: new Date().toISOString(),
              activatedBy: 'merchant',
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('open-in-messenger-btn').click();

      // The page shows a success message when hybrid mode is activated
      await expect(page.getByText(/now in control/)).toBeVisible();
    });
  });

  test.describe('AC7: Smart Button State', () => {
    test('shows "Return to Bot" button when hybrid mode is active', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            },
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await expect(page.getByTestId('return-to-bot-btn')).toBeVisible();
      await expect(page.getByText('Return to Bot')).toBeVisible();
    });

    test('"Return to Bot" disables hybrid mode', async ({ authenticatedPage: page }) => {
      let disableCalled = false;
      
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            },
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              connected: true,
              pageId: 'test_page_123',
              pageName: 'Test Page',
            },
          }),
        });
      });

      await page.route('**/api/conversations/123/hybrid-mode', async (route) => {
        const body = route.request().postDataJSON();
        if (body.enabled === false) {
          disableCalled = true;
        }
        
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              hybridMode: {
                enabled: body.enabled,
                activatedAt: body.enabled ? new Date().toISOString() : null,
                activatedBy: body.enabled ? 'merchant' : null,
                expiresAt: body.enabled ? new Date(Date.now() + 7200000).toISOString() : null,
                remainingSeconds: body.enabled ? 7200 : 0,
              },
            },
            meta: {
              requestId: 'test-request-id',
              timestamp: new Date().toISOString(),
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      await expect.poll(() => disableCalled).toBe(true);
    });
  });
});
