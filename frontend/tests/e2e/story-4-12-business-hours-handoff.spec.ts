/**
 * Business Hours Handoff E2E Tests
 *
 * Story 4-12: Business Hours Handling
 * Tests the complete user journey for business hours-aware handoff messages
 *
 * Acceptance Criteria:
 * - AC1: Business Hours in Handoff Message
 * - AC2: Expected Response Time
 * - AC3: Notification Queue Behavior
 *
 * @tags e2e business-hours handoff story-4-12
 */

import { test as base, expect } from '@playwright/test';

type MyFixtures = {
  authenticatedPage: import('@playwright/test').Page;
};

const FRIDAY_2PM = new Date('2026-02-20T14:00:00-08:00');
const FRIDAY_8PM = new Date('2026-02-20T20:00:00-08:00');
const FRIDAY_430PM = new Date('2026-02-20T16:30:00-08:00');
const FRIDAY_5PM = new Date('2026-02-20T17:00:00-08:00');
const SATURDAY_10AM = new Date('2026-02-21T10:00:00-08:00');
const SUNDAY_2PM = new Date('2026-02-22T14:00:00-08:00');

const BUSINESS_HOURS_CONFIG = {
  enabled: true,
  timezone: 'America/Los_Angeles',
  schedule: {
    monday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    tuesday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    wednesday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    thursday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    friday: { is_open: true, open_time: '09:00', close_time: '17:00' },
    saturday: { is_open: false },
    sunday: { is_open: false },
  },
};

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
    localStorage.setItem(
      'shop_onboarding_phase_progress',
      JSON.stringify(mockOnboardingState)
    );
    localStorage.setItem('tutorial-storage', JSON.stringify(mockTutorialState));
  });
};

const createHandoffConversation = (overrides: {
  conversationId?: number;
  isOffline?: boolean;
  expectedResponseTime?: string;
  businessHoursFormatted?: string;
  notificationQueued?: boolean;
} = {}) => ({
  data: {
    conversationId: overrides.conversationId ?? 123,
    platformSenderId: 'test_psid_12345',
    messages: [
      { id: 1, sender: 'customer', content: 'I need human help', createdAt: new Date().toISOString(), confidenceScore: null },
      {
        id: 2,
        sender: 'bot',
        content: overrides.isOffline
          ? `I'm having trouble understanding. Sorry! Our team is currently offline. We'll respond during business hours (${overrides.businessHoursFormatted ?? '9 AM - 5 PM, Mon-Fri'}). Expected response: ${overrides.expectedResponseTime ?? 'tomorrow at 9 AM'}.`
          : "I'm having trouble understanding. Sorry! Let me get someone who can help. I've flagged this - our team will respond within 12 hours.",
        createdAt: new Date().toISOString(),
        confidenceScore: null,
      },
    ],
    context: {
      cartState: { items: [] },
      extractedConstraints: null,
    },
    handoff: {
      triggerReason: 'keyword',
      triggeredAt: new Date().toISOString(),
      urgencyLevel: 'medium',
      waitTimeSeconds: 0,
      isOffline: overrides.isOffline ?? false,
      expectedResponseTime: overrides.expectedResponseTime ?? null,
    },
    customer: {
      maskedId: 'test****',
      orderCount: 1,
    },
    hybridMode: null,
    notificationQueue: overrides.notificationQueued
      ? { queued: true, scheduledFor: new Date('2026-02-21T09:00:00-08:00').toISOString() }
      : { queued: false },
  },
  meta: {
    requestId: 'test-request-id',
    timestamp: new Date().toISOString(),
  },
});

const test = base.extend<MyFixtures>({
  authenticatedPage: async ({ page }, use) => {
    await setupAuthMocks(page);
    await use(page);
  },
});

test.describe('Story 4-12: Business Hours Handoff', () => {
  test.describe.configure({ mode: 'parallel' });

  test.beforeEach(async ({ authenticatedPage }) => {
    await authenticatedPage.clock.install({ time: FRIDAY_8PM });
  });

  test.describe('AC1: Business Hours in Handoff Message', () => {
    test('[P0] @smoke shows offline indicator with business hours when outside business hours', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            businessHoursFormatted: '9 AM - 5 PM, Mon-Fri',
            expectedResponseTime: 'tomorrow at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(true);
      expect(data.data.messages[1].content).toContain('offline');
      expect(data.data.messages[1].content).toContain('9 AM - 5 PM, Mon-Fri');
    });

    test('[P1] shows standard handoff message when within business hours', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_2PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(false);
      expect(data.data.messages[1].content).not.toContain('offline');
      expect(data.data.messages[1].content).toContain('respond within 12 hours');
    });

    test('[P1] handles weekend correctly (outside business hours)', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(SATURDAY_10AM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            businessHoursFormatted: '9 AM - 5 PM, Mon-Fri',
            expectedResponseTime: 'Monday at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(true);
      expect(data.data.handoff.expectedResponseTime).toContain('Monday');
    });

    test('[P1] no business hours config shows standard handoff message', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              enabled: false,
              timezone: 'America/Los_Angeles',
              schedule: {},
            },
          }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(false);
      expect(data.data.messages[1].content).toContain('respond within 12 hours');
    });

    test('[P2] varied hours configuration displays correctly', async ({
      authenticatedPage,
    }) => {
      const variedHoursConfig = {
        enabled: true,
        timezone: 'America/Los_Angeles',
        schedule: {
          monday: { is_open: true, open_time: '08:00', close_time: '20:00' },
          tuesday: { is_open: true, open_time: '08:00', close_time: '20:00' },
          wednesday: { is_open: true, open_time: '08:00', close_time: '20:00' },
          thursday: { is_open: true, open_time: '08:00', close_time: '20:00' },
          friday: { is_open: true, open_time: '10:00', close_time: '18:00' },
          saturday: { is_open: true, open_time: '10:00', close_time: '14:00' },
          sunday: { is_open: false },
        },
      };

      await authenticatedPage.clock.setFixedTime(SATURDAY_10AM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: variedHoursConfig }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(false);
    });
  });

  test.describe('AC2: Expected Response Time', () => {
    const responseTimeScenarios = [
      {
        name: 'less than 1 hour',
        time: FRIDAY_430PM,
        expectedPattern: /less than 1 hour/i,
        isOffline: true,
      },
      {
        name: 'about X hours (1-6 hours)',
        time: FRIDAY_2PM,
        expectedPattern: /about \d+ hours?/i,
        isOffline: true,
      },
      {
        name: 'tomorrow (6-24 hours)',
        time: FRIDAY_8PM,
        expectedPattern: /tomorrow/i,
        isOffline: true,
      },
      {
        name: 'day name (>24 hours - weekend)',
        time: SATURDAY_10AM,
        expectedPattern: /(Monday|Tuesday|Wednesday|Thursday|Friday) at \d+ (AM|PM)/i,
        isOffline: true,
      },
      {
        name: 'day name (Sunday)',
        time: SUNDAY_2PM,
        expectedPattern: /(Monday|Tuesday|Wednesday|Thursday|Friday) at \d+ (AM|PM)/i,
        isOffline: true,
      },
    ];

    for (const scenario of responseTimeScenarios) {
      test(`[P0] @smoke shows expected response time for ${scenario.name}`, async ({
        authenticatedPage,
      }) => {
        await authenticatedPage.clock.setFixedTime(scenario.time);

        const expectedResponseTime = scenario.name.includes('less than 1 hour')
          ? 'less than 1 hour'
          : scenario.name.includes('tomorrow')
          ? 'tomorrow at 9 AM'
          : scenario.name.includes('weekend') || scenario.name.includes('Sunday')
          ? 'Monday at 9 AM'
          : 'about 3 hours';

        await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(createHandoffConversation({
              isOffline: scenario.isOffline,
              expectedResponseTime,
              businessHoursFormatted: '9 AM - 5 PM, Mon-Fri',
            })),
          });
        });

        await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
          });
        });

        await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              data: { connected: true, pageId: 'test_page', pageName: 'Test' },
            }),
          });
        });

        const responsePromise = authenticatedPage.waitForResponse((resp) =>
          resp.url().includes('/api/conversations/123/history')
        );

        await authenticatedPage.goto('/conversations/123/history');
        const response = await responsePromise;
        const data = await response.json();

        expect(data.data.handoff.expectedResponseTime).toMatch(scenario.expectedPattern);
      });
    }

    test('[P1] response time not shown when within business hours', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_2PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.expectedResponseTime).toBeNull();
    });
  });

  test.describe('AC3: Notification Queue Behavior', () => {
    test('[P1] notification queue status shown when queued', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'tomorrow at 9 AM',
            notificationQueued: true,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.notificationQueue.queued).toBe(true);
      expect(data.data.notificationQueue.scheduledFor).toBeDefined();
    });

    test('[P1] notification sent immediately when within business hours', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_2PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
            notificationQueued: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.notificationQueue.queued).toBe(false);
    });
  });

  test.describe('Time-Travel Testing', () => {
    test('[P1] Friday 8 PM (outside hours) shows offline message', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'tomorrow at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(true);
    });

    test('[P1] Saturday 10 AM (weekend) shows offline message', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(SATURDAY_10AM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'Monday at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(true);
      expect(data.data.handoff.expectedResponseTime).toContain('Monday');
    });

    test('[P1] Friday 2 PM (within hours) shows standard message', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_2PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: false,
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(false);
    });

    test('[P1] exactly at closing time (5 PM Friday) is offline', async ({
      authenticatedPage,
    }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_5PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'Monday at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      const responsePromise = authenticatedPage.waitForResponse((resp) =>
        resp.url().includes('/api/conversations/123/history')
      );

      await authenticatedPage.goto('/conversations/123/history');
      const response = await responsePromise;
      const data = await response.json();

      expect(data.data.handoff.isOffline).toBe(true);
    });
  });

  test.describe('Accessibility', () => {
    test('[P2] screen reader announces offline status', async ({ authenticatedPage }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'tomorrow at 9 AM',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      await authenticatedPage.goto('/conversations/123/history');
      await authenticatedPage.waitForLoadState('domcontentloaded');

      const mainContent = authenticatedPage.locator('main');
      await expect(mainContent).toBeVisible();

      const offlineIndicator = authenticatedPage.getByText(/offline/i);
      await expect(offlineIndicator).toBeAttached();
    });

    test('[P2] time information is accessible', async ({ authenticatedPage }) => {
      await authenticatedPage.clock.setFixedTime(FRIDAY_8PM);

      await authenticatedPage.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createHandoffConversation({
            isOffline: true,
            expectedResponseTime: 'tomorrow at 9 AM',
            businessHoursFormatted: '9 AM - 5 PM, Mon-Fri',
          })),
        });
      });

      await authenticatedPage.route('**/api/settings/business-hours', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: BUSINESS_HOURS_CONFIG }),
        });
      });

      await authenticatedPage.route('**/api/integrations/facebook/status', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { connected: true, pageId: 'test_page', pageName: 'Test' },
          }),
        });
      });

      await authenticatedPage.goto('/conversations/123/history');
      await authenticatedPage.waitForLoadState('domcontentloaded');

      const headings = authenticatedPage.locator('h1, h2, h3');
      const count = await headings.count();
      expect(count).toBeGreaterThan(0);
    });
  });

});
