/**
 * E2E Test: Knowledge Base Widget
 * Story 8.10: Frontend Dashboard Mode-Aware Widgets
 * Tests Knowledge Base widget visibility and functionality
 *
 * @tags e2e dashboard story-8-10 knowledge-base
 */

import { test, expect } from '@playwright/test';

test.describe('Story 8.10: Knowledge Base Widget @story-8-10', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      const mockAuthState = {
        isAuthenticated: true,
        merchant: {
          id: 1,
          email: 'test@test.com',
          name: 'Test Merchant',
          has_store_connected: false,
          store_provider: 'none',
          onboardingMode: 'general',
        },
        sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
        isLoading: false,
        error: null,
      };
      localStorage.setItem('shop_auth_state', JSON.stringify(mockAuthState));

      const mockOnboardingState = {
        state: {
          completedSteps: ['prerequisites', 'deploy', 'connect', 'config'],
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
      localStorage.setItem('shop_onboarding_phase_progress', JSON.stringify(mockOnboardingState));

      const mockTutorialState = {
        state: {
          isStarted: false,
          isCompleted: true,
          isSkipped: false,
          currentStep: 0,
          completedSteps: [],
        },
        version: 0,
      };
      localStorage.setItem('shop-tutorial-storage', JSON.stringify(mockTutorialState));
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            merchant: {
              id: 1,
              email: 'test@test.com',
              name: 'Test Merchant',
              merchant_key: 'test-merchant',
              has_store_connected: false,
              store_provider: 'none',
              onboardingMode: 'general',
            },
          },
        }),
      });
    });

    await page.route('**/api/onboarding/prerequisites*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: null }),
      });
    });
  });

  test('[8.10-E2E-007][P1] KB widget shows in general mode', async ({ page }) => {
    await page.route('**/api/merchant/profile', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            id: 1,
            merchant_key: 'test-merchant',
            onboarding_mode: 'general',
            business_name: 'Test Business',
            bot_name: 'General Assistant',
          },
        }),
      });
    });

    await page.route('**/api/knowledge-base/list', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: [
            { id: 1, filename: 'doc1.pdf', status: 'completed' },
            { id: 2, filename: 'doc2.pdf', status: 'completed' },
            { id: 3, filename: 'doc3.pdf', status: 'processing' },
          ],
        }),
      });
    });

    const profilePromise = page.waitForResponse('**/api/merchant/profile');

    await page.goto('/dashboard');
    await profilePromise;

    const kbWidget = page.getByTestId('knowledge-base-widget-container');
    await expect(kbWidget).toBeVisible({ timeout: 15000 });
  });
});
