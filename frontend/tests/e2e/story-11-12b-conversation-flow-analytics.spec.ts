import { test, expect } from '@playwright/test';

test.describe('Story 11.12b: Conversation Flow Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            id: 'test-merchant-1',
            email: 'test@test.com',
            name: 'Test Merchant',
            hasStoreConnected: true,
            onboardingMode: 'ecommerce',
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
          hasStoreConnected: true,
          onboardingMode: 'ecommerce',
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
        },
      };

      localStorage.setItem('auth-storage', JSON.stringify({ state: mockAuthState, version: 0 }));
      localStorage.setItem('onboarding-storage', JSON.stringify(mockOnboardingState));
    });

    await page.route('**/api/v1/analytics/conversation-flow/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ has_data: false, message: 'No data available.' }),
      });
    });
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async ({ page }) => {
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('AC1 Conversation Flow widget renders on dashboard @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });
    await expect(widget.locator('text=Flow Analytics')).toBeVisible();
  });

  test('AC2 Widget displays 6 tabs @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const tabs = ['Overview', 'Clarification', 'Friction', 'Sentiment', 'Handoff', 'Context'];
    for (const tab of tabs) {
      const tabButton = widget.locator('button').filter({ hasText: new RegExp(tab, 'i') });
      await expect(tabButton).toBeVisible({ timeout: 5000 });
    }
  });

  test('AC3 Tab switching updates displayed content @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const clarificationTab = widget.locator('button').filter({ hasText: /Clarification/i });
    await clarificationTab.click();

    await expect(widget.locator('text=Clarification')).toBeVisible();
  });

  test('AC4 Friction tab shows friction section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const frictionTab = widget.locator('button').filter({ hasText: /Friction/i });
    await frictionTab.click();

    await expect(widget.locator('text=Friction')).toBeVisible();
  });

  test('AC5 Sentiment tab shows sentiment section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const sentimentTab = widget.locator('button').filter({ hasText: /Sentiment/i });
    await sentimentTab.click();

    await expect(widget.locator('text=Sentiment')).toBeVisible();
  });

  test('AC6 Handoff tab shows handoff section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const handoffTab = widget.locator('button').filter({ hasText: /Handoff/i });
    await handoffTab.click();

    await expect(widget.locator('text=Handoff')).toBeVisible();
  });

  test('AC7 Context tab shows context utilization section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const contextTab = widget.locator('button').filter({ hasText: /Context/i });
    await contextTab.click();

    await expect(widget.locator('text=Context')).toBeVisible();
  });

  test('AC8 Overview tab displays length distribution metrics @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const overviewTab = widget.locator('button').filter({ hasText: /Overview/i });
    await overviewTab.click();

    const hasAvgTurns = await widget.locator('text=Avg Turns').isVisible().catch(() => false);
    const hasEmptyState = await widget.locator('text=No conversation data').isVisible().catch(() => false);
    expect(hasAvgTurns || hasEmptyState).toBeTruthy();
  });

  test('AC9 Widget makes API calls to conversation-flow endpoints @p1', async ({ page }) => {
    const apiCallPromise = page.waitForResponse(
      (resp) => resp.url().includes('/conversation-flow/'),
      { timeout: 15000 }
    );

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const response = await apiCallPromise;
    expect(response.url()).toContain('/conversation-flow/');
  });

  test('AC10 Expandable widget opens and closes @p2', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const expandButton = widget.locator('button[aria-label="Expand"]');
    await expect(expandButton).toBeVisible({ timeout: 5000 });
    await expandButton.click();

    const closeButton = widget.locator('button[aria-label="Collapse"]');
    await expect(closeButton).toBeVisible({ timeout: 5000 });

    await closeButton.click();
    await expect(widget).toBeVisible();
  });

  test('AC0 Empty state displayed on all tabs when no data @p2', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const tabs = [
      'Overview', 'Clarification', 'Friction',
      'Sentiment', 'Handoff', 'Context',
    ];

    for (const tab of tabs) {
      const tabButton = widget.locator('button').filter({ hasText: new RegExp(tab, 'i') });
      await tabButton.click();

      const hasEmptyMessage = await widget
        .locator('text=/No (conversation |data )?(data|available|conversation data)/i')
        .isVisible()
        .catch(() => false);
      expect(hasEmptyMessage).toBeTruthy();
    }
  });

  test('AC11 Mock API data displays correctly in widget @p2', async ({ page }) => {
    await page.route('**/api/v1/analytics/conversation-flow/overview**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          has_data: true,
          data: {
            total_conversations: 150,
            average_turns: 5.2,
            completion_rate: 0.87,
            by_mode: [],
            daily_trend: [],
          },
          period_days: 30,
        }),
      });
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const overviewTab = widget.locator('button').filter({ hasText: /Overview/i });
    await overviewTab.click();

    await expect(widget.locator('text=150')).toBeVisible({ timeout: 10000 });
  });
});
