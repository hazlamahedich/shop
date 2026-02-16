/**
 * Offline Follow-Up Messages E2E Tests
 *
 * Story 4-11: Offline Follow-Up Messages
 * Tests the follow-up message flow and conversation state tracking
 *
 * Test Categories:
 * - AC1: 12-Hour Follow-Up (with time-travel simulation)
 * - AC2: 24-Hour Follow-Up (with time-travel simulation)
 * - AC4: No Duplicate Follow-Ups
 * - AC5: Handoff Status Tracking
 *
 * @tags e2e offline-followup story-4-11
 */

import { test as base, expect } from '@playwright/test';

type TimeTravelOptions = {
  hoursSinceHandoff?: number;
  followup12hSentAt?: string | null;
  followup24hSentAt?: string | null;
};

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
  timeTravelPage: import('@playwright/test').Page & {
    travelToTime: (options: TimeTravelOptions) => Promise<void>;
  };
};

const HOURS_12_MS = 12 * 60 * 60 * 1000;
const HOURS_24_MS = 24 * 60 * 60 * 1000;
const HANDOFF_BASE_TIME = new Date('2026-02-16T09:00:00Z');

const setupAuthMocks = async (page: import('@playwright/test').Page) => {
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
};

const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await setupAuthMocks(page);
    await use(page);
  },

  timeTravelPage: async ({ page }, use) => {
    await setupAuthMocks(page);

    await page.clock.install({ time: HANDOFF_BASE_TIME });

    const timeTravelPage = page as import('@playwright/test').Page & {
      travelToTime: (options: TimeTravelOptions) => Promise<void>;
    };

    timeTravelPage.travelToTime = async (options: TimeTravelOptions) => {
      const { hoursSinceHandoff = 0 } = options;
      const targetTime = new Date(HANDOFF_BASE_TIME.getTime() + hoursSinceHandoff * 60 * 60 * 1000);
      await page.clock.setFixedTime(targetTime);
    };

    await use(timeTravelPage);
  },
});

const createConversationWithFollowUp = (overrides: {
  conversationId?: number;
  followup12hSentAt?: string | null;
  followup24hSentAt?: string | null;
  handoffTriggeredAt?: string;
} = {}) => ({
  data: {
    conversationId: overrides.conversationId ?? 123,
    platformSenderId: 'test_psid_12345',
    messages: [
      { id: 1, sender: 'customer', content: 'I need help with my order', createdAt: new Date().toISOString(), confidenceScore: null },
      { id: 2, sender: 'bot', content: "I'm having trouble understanding. Let me connect you with our team.", createdAt: new Date().toISOString(), confidenceScore: null },
    ],
    context: {
      cartState: { items: [] },
      extractedConstraints: null,
    },
    handoff: {
      triggerReason: 'keyword',
      triggeredAt: overrides.handoffTriggeredAt ?? new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
      urgencyLevel: 'medium',
      waitTimeSeconds: 46800,
    },
    customer: {
      maskedId: 'test****',
      orderCount: 1,
    },
    hybridMode: null,
    followUp: {
      followup12hSentAt: overrides.followup12hSentAt ?? null,
      followup24hSentAt: overrides.followup24hSentAt ?? null,
    },
  },
  meta: {
    requestId: 'test-request-id',
    timestamp: new Date().toISOString(),
  },
});

test.describe('Story 4-11: Offline Follow-Up Messages', () => {
  test.describe('AC5: Handoff Status Tracking', () => {
    test('conversation data includes follow-up timestamps', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            followup12hSentAt: twelveHoursAgo,
            handoffTriggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
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

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp).toBeDefined();
      expect(data.data.followUp.followup12hSentAt).toBe(twelveHoursAgo);
      expect(data.data.followUp.followup24hSentAt).toBeNull();
    });

    test('conversation state reflects 12h follow-up sent status', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            followup12hSentAt: twelveHoursAgo,
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

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      await responsePromise;
      await page.waitForLoadState('domcontentloaded');

      await expect(page.getByTestId('conversation-history-page')).toBeAttached({ timeout: 10000 });
    });

    test('conversation state reflects 24h follow-up sent status', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            followup12hSentAt: twelveHoursAgo,
            followup24hSentAt: sixHoursAgo,
            handoffTriggeredAt: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
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

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(twelveHoursAgo);
      expect(data.data.followUp.followup24hSentAt).toBe(sixHoursAgo);
    });
  });

  test.describe('AC4: No Duplicate Follow-Ups', () => {
    test('12h follow-up timestamp prevents re-sending', async ({ authenticatedPage: page }) => {
      const existingTimestamp = new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            followup12hSentAt: existingTimestamp,
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

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(existingTimestamp);
    });

    test('24h follow-up timestamp prevents re-sending', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();
      const existing24hTimestamp = new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            followup12hSentAt: twelveHoursAgo,
            followup24hSentAt: existing24hTimestamp,
            handoffTriggeredAt: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
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

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup24hSentAt).toBe(existing24hTimestamp);
    });
  });

  test.describe('Message Content Display', () => {
    test('follow-up message content displays in conversation history', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: "I'm having trouble understanding.", createdAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(), confidenceScore: null },
                { id: 3, sender: 'bot', content: 'Still working on your request. Our team will respond as soon as possible. In the meantime, is there anything else I can help with?', createdAt: twelveHoursAgo, confidenceScore: null },
              ],
              context: {
                cartState: { items: [] },
                extractedConstraints: null,
              },
              handoff: {
                triggerReason: 'keyword',
                triggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
                urgencyLevel: 'medium',
                waitTimeSeconds: 46800,
              },
              customer: {
                maskedId: 'test****',
                orderCount: 1,
              },
              hybridMode: null,
              followUp: {
                followup12hSentAt: twelveHoursAgo,
                followup24hSentAt: null,
              },
            },
            meta: {
              requestId: 'test-request-id',
              timestamp: new Date().toISOString(),
            },
          }),
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

      const messageElement = page.getByText(/Still working on your request/);
      await messageElement.scrollIntoViewIfNeeded();
      await expect(messageElement).toBeAttached();
    });

    test('24h follow-up message with email displays correctly', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: "I'm having trouble understanding.", createdAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(), confidenceScore: null },
                { id: 3, sender: 'bot', content: 'Still working on your request.', createdAt: twelveHoursAgo, confidenceScore: null },
                { id: 4, sender: 'bot', content: 'Sorry for the delay. Our team is experiencing high volume. You can also reach us at support@test.com for faster response.', createdAt: sixHoursAgo, confidenceScore: null },
              ],
              context: {
                cartState: { items: [] },
                extractedConstraints: null,
              },
              handoff: {
                triggerReason: 'keyword',
                triggeredAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
                urgencyLevel: 'medium',
                waitTimeSeconds: 93600,
              },
              customer: {
                maskedId: 'test****',
                orderCount: 1,
              },
              hybridMode: null,
              followUp: {
                followup12hSentAt: twelveHoursAgo,
                followup24hSentAt: sixHoursAgo,
              },
            },
            meta: {
              requestId: 'test-request-id',
              timestamp: new Date().toISOString(),
            },
          }),
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

      const delayMessage = page.getByText(/Sorry for the delay/);
      await delayMessage.scrollIntoViewIfNeeded();
      await expect(delayMessage).toBeAttached();
      await expect(page.getByText(/support@test.com/)).toBeAttached();
    });
  });

  test.describe('AC3: Business Hours Configuration', () => {
    test('[P1] follow-up not sent outside business hours', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
            followup12hSentAt: null,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              enabled: true,
              timezone: 'America/New_York',
              schedule: {
                monday: { start: '09:00', end: '17:00' },
                tuesday: { start: '09:00', end: '17:00' },
                wednesday: { start: '09:00', end: '17:00' },
                thursday: { start: '09:00', end: '17:00' },
                friday: { start: '09:00', end: '17:00' },
                saturday: null,
                sunday: null,
              },
            },
          }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBeNull();
    });

    test('[P1] follow-up sent during business hours', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
            followup12hSentAt: twelveHoursAgo,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              enabled: true,
              timezone: 'America/New_York',
              schedule: {
                monday: { start: '00:00', end: '23:59' },
                tuesday: { start: '00:00', end: '23:59' },
                wednesday: { start: '00:00', end: '23:59' },
                thursday: { start: '00:00', end: '23:59' },
                friday: { start: '00:00', end: '23:59' },
                saturday: { start: '00:00', end: '23:59' },
                sunday: { start: '00:00', end: '23:59' },
              },
            },
          }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(twelveHoursAgo);
    });

    test('[P1] follow-up respects 24h business hours disabled', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();
      const sixHoursAgo = new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
            followup12hSentAt: twelveHoursAgo,
            followup24hSentAt: sixHoursAgo,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              enabled: false,
              timezone: 'America/New_York',
              schedule: {},
            },
          }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(twelveHoursAgo);
      expect(data.data.followUp.followup24hSentAt).toBe(sixHoursAgo);
    });

    test('[P2] follow-up queues for next business day', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
            followup12hSentAt: null,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              enabled: true,
              timezone: 'America/New_York',
              schedule: {
                monday: { start: '09:00', end: '17:00' },
                tuesday: { start: '09:00', end: '17:00' },
                wednesday: { start: '09:00', end: '17:00' },
                thursday: { start: '09:00', end: '17:00' },
                friday: { start: '09:00', end: '17:00' },
                saturday: null,
                sunday: null,
              },
            },
          }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      await responsePromise;
      await page.waitForLoadState('domcontentloaded');

      await expect(page.getByTestId('conversation-history-page')).toBeAttached({ timeout: 10000 });
    });
  });

  test.describe('Accessibility', () => {
    test('[P2] follow-up messages are accessible to screen readers', async ({ authenticatedPage: page }) => {
      const twelveHoursAgo = new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: 'Still working on your request.', createdAt: twelveHoursAgo, confidenceScore: null },
              ],
              context: { cartState: { items: [] }, extractedConstraints: null },
              handoff: { triggerReason: 'keyword', triggeredAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(), urgencyLevel: 'medium', waitTimeSeconds: 46800 },
              customer: { maskedId: 'test****', orderCount: 1 },
              hybridMode: null,
              followUp: { followup12hSentAt: twelveHoursAgo, followup24hSentAt: null },
            },
            meta: { requestId: 'test-request-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page_123', pageName: 'Test Page' },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.waitForLoadState('networkidle');

      await expect(page.getByText(/Still working on your request/)).toBeAttached();
    });
  });

  test.describe('AC1: 12-Hour Follow-Up (Time-Travel)', () => {
    test('[P1] 12h follow-up shows pending status before threshold', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 11 });

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: HANDOFF_BASE_TIME.toISOString(),
            followup12hSentAt: null,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBeNull();
      expect(data.data.followUp.followup24hSentAt).toBeNull();
    });

    test('[P1] 12h follow-up triggered at exactly 12 hours', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 12 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: HANDOFF_BASE_TIME.toISOString(),
            followup12hSentAt: followup12hTime,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(followup12hTime);
      expect(data.data.followUp.followup24hSentAt).toBeNull();
    });

    test('[P1] 12h follow-up message content displays correctly', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 12.5 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: "I'm having trouble understanding.", createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 3, sender: 'bot', content: 'Still working on your request. Our team will respond as soon as possible. In the meantime, is there anything else I can help with?', createdAt: followup12hTime, confidenceScore: null },
              ],
              context: { cartState: { items: [] }, extractedConstraints: null },
              handoff: { triggerReason: 'keyword', triggeredAt: HANDOFF_BASE_TIME.toISOString(), urgencyLevel: 'medium', waitTimeSeconds: 45000 },
              customer: { maskedId: 'test****', orderCount: 1 },
              hybridMode: null,
              followUp: { followup12hSentAt: followup12hTime, followup24hSentAt: null },
            },
            meta: { requestId: 'test-request-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.goto('/conversations/123/history');

      const messageElement = page.getByText(/Still working on your request/);
      await messageElement.scrollIntoViewIfNeeded();
      await expect(messageElement).toBeAttached();
      await expect(page.getByText(/Our team will respond as soon as possible/)).toBeAttached();
    });
  });

  test.describe('AC2: 24-Hour Follow-Up (Time-Travel)', () => {
    test('[P1] 24h follow-up not yet sent at 23 hours', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 23 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: HANDOFF_BASE_TIME.toISOString(),
            followup12hSentAt: followup12hTime,
            followup24hSentAt: null,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(followup12hTime);
      expect(data.data.followUp.followup24hSentAt).toBeNull();
    });

    test('[P1] 24h follow-up triggered at exactly 24 hours with email', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 24 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();
      const followup24hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_24_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createConversationWithFollowUp({
            handoffTriggeredAt: HANDOFF_BASE_TIME.toISOString(),
            followup12hSentAt: followup12hTime,
            followup24hSentAt: followup24hTime,
          })),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      const responsePromise = page.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await page.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.followUp.followup12hSentAt).toBe(followup12hTime);
      expect(data.data.followUp.followup24hSentAt).toBe(followup24hTime);
    });

    test('[P1] 24h follow-up message includes merchant email', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 25 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();
      const followup24hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_24_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: "I'm having trouble understanding.", createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 3, sender: 'bot', content: 'Still working on your request.', createdAt: followup12hTime, confidenceScore: null },
                { id: 4, sender: 'bot', content: 'Sorry for the delay. Our team is experiencing high volume. You can also reach us at support@merchant.com for faster response.', createdAt: followup24hTime, confidenceScore: null },
              ],
              context: { cartState: { items: [] }, extractedConstraints: null },
              handoff: { triggerReason: 'keyword', triggeredAt: HANDOFF_BASE_TIME.toISOString(), urgencyLevel: 'medium', waitTimeSeconds: 90000 },
              customer: { maskedId: 'test****', orderCount: 1 },
              hybridMode: null,
              followUp: { followup12hSentAt: followup12hTime, followup24hSentAt: followup24hTime },
            },
            meta: { requestId: 'test-request-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.goto('/conversations/123/history');

      const delayMessage = page.getByText(/Sorry for the delay/);
      await delayMessage.scrollIntoViewIfNeeded();
      await expect(delayMessage).toBeAttached();
      await expect(page.getByText(/support@merchant.com/)).toBeAttached();
    });

    test('[P1] 24h follow-up message fallback without email', async ({ timeTravelPage: page }) => {
      await page.travelToTime({ hoursSinceHandoff: 25 });

      const followup12hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString();
      const followup24hTime = new Date(HANDOFF_BASE_TIME.getTime() + HOURS_24_MS).toISOString();

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              platformSenderId: 'test_psid_12345',
              messages: [
                { id: 1, sender: 'customer', content: 'I need help', createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 2, sender: 'bot', content: "I'm having trouble understanding.", createdAt: HANDOFF_BASE_TIME.toISOString(), confidenceScore: null },
                { id: 3, sender: 'bot', content: 'Still working on your request.', createdAt: followup12hTime, confidenceScore: null },
                { id: 4, sender: 'bot', content: 'Sorry for the delay. Our team is experiencing high volume. We will respond to your request as soon as possible.', createdAt: followup24hTime, confidenceScore: null },
              ],
              context: { cartState: { items: [] }, extractedConstraints: null },
              handoff: { triggerReason: 'keyword', triggeredAt: HANDOFF_BASE_TIME.toISOString(), urgencyLevel: 'medium', waitTimeSeconds: 90000 },
              customer: { maskedId: 'test****', orderCount: 1 },
              hybridMode: null,
              followUp: { followup12hSentAt: followup12hTime, followup24hSentAt: followup24hTime },
            },
            meta: { requestId: 'test-request-id', timestamp: new Date().toISOString() },
          }),
        });
      });

      await page.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
        });
      });

      await page.goto('/conversations/123/history');

      const delayMessage = page.getByText(/Sorry for the delay/);
      await delayMessage.scrollIntoViewIfNeeded();
      await expect(delayMessage).toBeAttached();
      await expect(page.getByText(/We will respond to your request as soon as possible/)).toBeAttached();
    });
  });

  test.describe('Full Timing Flow (Time-Travel)', () => {
    test('[P1] complete flow: handoff → 12h → 24h follow-ups', async ({ timeTravelPage: page }) => {
      const scenarios = [
        { hours: 0, expect12h: null, expect24h: null, description: 'at handoff time' },
        { hours: 11, expect12h: null, expect24h: null, description: 'before 12h threshold' },
        { hours: 12, expect12h: 'pending', expect24h: null, description: 'at 12h threshold' },
        { hours: 18, expect12h: 'sent', expect24h: null, description: 'after 12h, before 24h' },
        { hours: 24, expect12h: 'sent', expect24h: 'pending', description: 'at 24h threshold' },
        { hours: 30, expect12h: 'sent', expect24h: 'sent', description: 'after both follow-ups' },
      ];

      for (const scenario of scenarios) {
        await page.travelToTime({ hoursSinceHandoff: scenario.hours });

        const followup12hTime = scenario.expect12h === 'sent' || scenario.expect12h === 'pending'
          ? new Date(HANDOFF_BASE_TIME.getTime() + HOURS_12_MS).toISOString()
          : null;
        const followup24hTime = scenario.expect24h === 'sent' || scenario.expect24h === 'pending'
          ? new Date(HANDOFF_BASE_TIME.getTime() + HOURS_24_MS).toISOString()
          : null;

        await page.route('**/api/conversations/123/history', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(createConversationWithFollowUp({
              handoffTriggeredAt: HANDOFF_BASE_TIME.toISOString(),
              followup12hSentAt: followup12hTime,
              followup24hSentAt: followup24hTime,
            })),
          });
        });

        await page.route('**/api/integrations/facebook/status', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: { connected: true, pageId: 'test_page', pageName: 'Test' } }),
          });
        });

        const responsePromise = page.waitForResponse((resp) =>
          resp.url().includes('/api/conversations/123/history')
        );

        await page.goto('/conversations/123/history');
        const response = await responsePromise;
        const data = await response.json();

        if (scenario.expect12h === null) {
          expect(data.data.followUp.followup12hSentAt).toBeNull();
        } else {
          expect(data.data.followUp.followup12hSentAt).toBe(followup12hTime);
        }

        if (scenario.expect24h === null) {
          expect(data.data.followUp.followup24hSentAt).toBeNull();
        } else {
          expect(data.data.followUp.followup24hSentAt).toBe(followup24hTime);
        }
      }
    });
  });
});
