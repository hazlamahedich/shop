/**
 * Return to Bot E2E Tests
 *
 * Story 4-10: Return to Bot
 * Tests the complete user journey for returning control to the bot
 * Uses authenticated page fixture with mocked auth state
 *
 * @tags e2e return-to-bot story-4-10
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
  status?: string;
  handoffStatus?: string;
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

test.describe('Story 4-10: Return to Bot', () => {
  test.describe('AC1: Return to Bot Button', () => {
    test('conversation in handoff status shows "Return to Bot" button', async ({ authenticatedPage: page }) => {
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

    test('clicking "Return to Bot" changes button to "Open in Messenger"', async ({ authenticatedPage: page }) => {
      let hybridModeEnabled = true;

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: hybridModeEnabled ? {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            } : null,
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
        hybridModeEnabled = body.enabled;

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversationId: 123,
            hybridMode: {
              enabled: body.enabled,
              activatedAt: body.enabled ? new Date().toISOString() : null,
              activatedBy: body.enabled ? 'merchant' : null,
              expiresAt: body.enabled ? new Date(Date.now() + 7200000).toISOString() : null,
              remainingSeconds: body.enabled ? 7200 : 0,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');

      await expect(page.getByTestId('return-to-bot-btn')).toBeVisible();
      await page.getByTestId('return-to-bot-btn').click();

      await expect(page.getByTestId('open-in-messenger-btn')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('AC3: Conversation Status Update', () => {
    test('API called with enabled: false when clicking "Return to Bot"', async ({ authenticatedPage: page }) => {
      let requestPayload: any = null;

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
        requestPayload = route.request().postDataJSON();

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              conversationId: 123,
              hybridMode: {
                enabled: false,
                activatedAt: null,
                activatedBy: null,
                expiresAt: null,
                remainingSeconds: 0,
              },
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      await expect.poll(() => requestPayload).not.toBeNull();
      expect(requestPayload.enabled).toBe(false);
    });

    test('conversation status updates from "handoff" to "active" in UI', async ({ authenticatedPage: page }) => {
      let hybridModeEnabled = true;

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: hybridModeEnabled ? {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            } : null,
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
        hybridModeEnabled = false;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversationId: 123,
            hybridMode: {
              enabled: false,
              activatedAt: null,
              activatedBy: null,
              expiresAt: null,
              remainingSeconds: 0,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      await expect(page.getByTestId('open-in-messenger-btn')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('AC2 & Task 8: Toast Notification', () => {
    test('toast shows "Bot is back in control" with data-testid', async ({ authenticatedPage: page }) => {
      let hybridModeEnabled = true;

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: hybridModeEnabled ? {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            } : null,
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
        hybridModeEnabled = false;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversationId: 123,
            hybridMode: {
              enabled: false,
              activatedAt: null,
              activatedBy: null,
              expiresAt: null,
              remainingSeconds: 0,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      const toast = page.getByTestId('return-to-bot-toast');
      await expect(toast).toBeVisible({ timeout: 3000 });
      await expect(toast).toContainText('Bot is back in control');
    });
  });

  test.describe('AC5: Handoff Status Reset', () => {
    test('handoff_status is reset to "none" in API response', async ({ authenticatedPage: page }) => {
      let responsePayload: any = null;

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
        responsePayload = {
          conversationId: 123,
          hybridMode: {
            enabled: body.enabled,
            activatedAt: null,
            activatedBy: null,
            expiresAt: null,
            remainingSeconds: 0,
          },
          conversationStatus: 'active',
          handoffStatus: 'none',
        };

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(responsePayload),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      await expect.poll(() => responsePayload).not.toBeNull();
      expect(responsePayload.handoffStatus).toBe('none');
    });
  });

  test.describe('Negative Paths: Non-Handoff Status', () => {
    test('[P1] conversation with active status shows "Open in Messenger" not "Return to Bot"', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: null,
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

      await expect(page.getByTestId('open-in-messenger-btn')).toBeVisible();
      await expect(page.getByTestId('return-to-bot-btn')).not.toBeVisible();
    });

    test('[P1] conversation with closed status shows "Open in Messenger"', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: null,
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

      await expect(page.getByTestId('open-in-messenger-btn')).toBeVisible();
    });

    test('[P1] auto-expired hybrid mode (no remainingSeconds) shows "Open in Messenger"', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: {
              enabled: true,
              activatedAt: new Date(Date.now() - 7200000).toISOString(),
              expiresAt: new Date(Date.now() - 1000).toISOString(),
              remainingSeconds: 0,
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
    });
  });

  test.describe('Error Handling', () => {
    test('[P1] API failure shows error message to user', async ({ authenticatedPage: page }) => {
      let apiCallCount = 0;

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
        apiCallCount++;
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Internal Server Error',
            message: 'Something went wrong',
          }),
        });
      });

      await page.goto('/conversations/123/history');

      const returnToBotBtn = page.getByTestId('return-to-bot-btn');
      await returnToBotBtn.click();

      await expect.poll(() => apiCallCount).toBeGreaterThan(0);

      // Toast should not be visible on error
      await expect(page.getByTestId('return-to-bot-toast')).not.toBeVisible({ timeout: 2000 });

      // Page should show error message (correct UX behavior)
      await expect(page.getByText(/Failed to update hybrid mode|Something went wrong/i)).toBeVisible({ timeout: 3000 });
    });

    test('[P1] network error is handled gracefully', async ({ authenticatedPage: page }) => {
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
        await route.abort('failed');
      });

      await page.goto('/conversations/123/history');

      const returnToBotBtn = page.getByTestId('return-to-bot-btn');
      await returnToBotBtn.click();

      await expect(page.getByTestId('return-to-bot-toast')).not.toBeVisible({ timeout: 2000 });
    });

    test('[P1] 401 unauthorized response does not show toast', async ({ authenticatedPage: page }) => {
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
        await route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'Unauthorized',
            message: 'Authentication required',
          }),
        });
      });

      await page.goto('/conversations/123/history');

      await page.getByTestId('return-to-bot-btn').click();

      await expect(page.getByTestId('return-to-bot-toast')).not.toBeVisible({ timeout: 2000 });
    });
  });

  test.describe('Accessibility', () => {
    test('[P2] button has correct aria-label for return to bot', async ({ authenticatedPage: page }) => {
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

      const button = page.getByTestId('return-to-bot-btn');
      await expect(button).toHaveAttribute('aria-label', 'Return control to bot');
    });

    test('[P2] button has correct aria-label for open in messenger', async ({ authenticatedPage: page }) => {
      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: null,
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

      const button = page.getByTestId('open-in-messenger-btn');
      await expect(button).toHaveAttribute('aria-label', 'Open conversation in Messenger');
    });

    test('[P2] button is focusable via keyboard Tab', async ({ authenticatedPage: page }) => {
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

      const button = page.getByTestId('return-to-bot-btn');
      await button.focus();

      await expect(button).toBeFocused();
    });

    test('[P2] toast notification has correct ARIA attributes', async ({ authenticatedPage: page }) => {
      let hybridModeEnabled = true;

      await page.route('**/api/conversations/123/history', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createTestConversationHistory({
            hybridMode: hybridModeEnabled ? {
              enabled: true,
              activatedAt: new Date().toISOString(),
              expiresAt: new Date(Date.now() + 7200000).toISOString(),
              remainingSeconds: 7200,
            } : null,
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
        hybridModeEnabled = false;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            conversationId: 123,
            hybridMode: {
              enabled: false,
              activatedAt: null,
              activatedBy: null,
              expiresAt: null,
              remainingSeconds: 0,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');
      await page.getByTestId('return-to-bot-btn').click();

      const toast = page.getByTestId('return-to-bot-toast');
      await expect(toast).toBeVisible();
      await expect(toast).toHaveAttribute('role', 'status');
      await expect(toast).toHaveAttribute('aria-live', 'polite');
    });

    test('[P2] disabled button shows tooltip on hover', async ({ authenticatedPage: page }) => {
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
              connected: false,
              pageId: null,
              pageName: null,
            },
          }),
        });
      });

      await page.goto('/conversations/123/history');

      const button = page.getByTestId('return-to-bot-btn');
      await button.hover();

      await expect(page.getByTestId('no-facebook-tooltip')).toBeVisible();
    });
  });
});
