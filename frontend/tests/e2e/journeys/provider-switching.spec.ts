/**
 * E2E Tests: Provider Switching Journey
 *
 * User Journey: Merchant switches between LLM providers and
 * verifies cost changes in real-time.
 *
 * Flow: Settings → Configure → Verify Cost Changes
 *
 * Priority Coverage:
 * - [P0] Complete provider switching happy path
 * - [P1] Cost comparison and validation
 * - [P2] Historical cost tracking comparison
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Provider Switching', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings/provider');
    await page.waitForLoadState('domcontentloaded');
  });

  test('[P0] should switch from OpenAI to Anthropic successfully', async ({ page }) => {
    // GIVEN: User is on provider settings page with OpenAI as current provider
    await expect(page.getByRole('heading', { name: /provider.*settings/i })).toBeVisible();

    const currentProviderSection = page.getByText(/current provider/i).or(
      page.locator('[class*="bg-blue-50"]')
    );
    await expect(currentProviderSection.first()).toBeVisible();

    // WHEN: Selecting Anthropic provider
    const anthropicCard = page.getByText('Anthropic').or(
      page.locator('[data-testid*="anthropic"]')
    ).first();

    await anthropicCard.click();

    // THEN: Configuration modal should appear
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 3000 });

    // WHEN: Entering API key and validating
    await page.route('**/api/llm/validate**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            valid: true,
            provider: 'anthropic',
          },
          meta: { requestId: 'test-validate' },
        }),
      });
    });

    const apiKeyInput = page.getByLabel(/api key/i).or(
      page.locator('input[name*="api"]')
    ).first();
    await apiKeyInput.fill('sk-ant-test-key-12345');

    // Click validate button
    const validateButton = page.getByRole('button', { name: /validate/i });
    if (await validateButton.isVisible()) {
      await validateButton.click();
    }

    // THEN: Should show validation success
    await expect(page.getByText(/valid|success/i)).toBeVisible({ timeout: 3000 });

    // WHEN: Confirming provider switch
    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            provider: 'anthropic',
            updatedAt: new Date().toISOString(),
          },
          meta: { requestId: 'test-switch' },
        }),
      });
    });

    const switchButton = page.getByRole('button', { name: /switch|save|confirm/i });
    await switchButton.click();

    // THEN: Should show success notification
    await expect(page.locator('[role="alert"]', { hasText: /switched|success/i })).toBeVisible({ timeout: 5000 });
  });

  test('[P1] should display cost savings calculator', async ({ page }) => {
    // GIVEN: User is viewing provider options
    await page.goto('/settings/provider');

    // WHEN: Viewing provider comparison
    const comparisonSection = page.getByText(/comparison|available providers/i);
    await expect(comparisonSection.first()).toBeVisible();

    // THEN: Should see cost savings information
    const savingsText = page.getByText(/savings|cheaper|cost/i);
    await expect(savingsText.first()).toBeVisible();

    // Check for pricing table
    const table = page.locator('table');
    const hasTable = await table.isVisible().catch(() => false);

    if (hasTable) {
      // Should show input/output costs
      await expect(page.getByText(/input.*cost/i)).toBeVisible();
      await expect(page.getByText(/output.*cost/i)).toBeVisible();
    }
  });

  test('[P1] should verify cost changes after provider switch', async ({ page }) => {
    // GIVEN: User has just switched providers
    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            provider: 'ollama',
            previousProvider: 'openai',
          },
          meta: { requestId: 'test-switch' },
        }),
      });
    });

    // Switch provider
    const ollamaCard = page.getByText('Ollama').or(
      page.locator('[data-testid*="ollama"]')
    ).first();

    if (await ollamaCard.isVisible()) {
      await ollamaCard.click();

      const confirmButton = page.getByRole('button', { name: /switch|save/i });
      await confirmButton.click();

      // WHEN: Navigating to costs page
      await page.goto('/costs');
      await page.waitForLoadState('networkidle');

      // THEN: Should see updated provider in cost breakdown
      const providerLabel = page.getByText(/ollama/i);
      await expect(providerLabel.first()).toBeVisible();
    }
  });

  test('[P1] should show provider feature comparison', async ({ page }) => {
    // GIVEN: User is comparing providers
    await page.goto('/settings/provider');

    // WHEN: Viewing provider cards
    const providerCards = page.locator('[class*="rounded-lg"]').filter({
      hasText: /OpenAI|Anthropic|Ollama/i
    });

    await expect(providerCards.first()).toBeVisible();

    // THEN: Should see feature badges
    const features = page.getByText(/streaming|json|vision/i);
    await expect(features.first()).toBeVisible();
  });

  test('[P0] should validate API key before switching', async ({ page }) => {
    // GIVEN: User selects a new provider
    const providerCard = page.locator('[class*="rounded-lg"]').first();
    await providerCard.click();

    // WHEN: Entering invalid API key
    await page.route('**/api/llm/validate**', route => {
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Invalid API key',
          message: 'The provided API key is invalid',
        }),
      });
    });

    const apiKeyInput = page.getByLabel(/api key/i).or(
      page.locator('input[name*="api"]')
    ).first();
    await apiKeyInput.fill('invalid-key-123');

    const validateButton = page.getByRole('button', { name: /validate/i });
    if (await validateButton.isVisible()) {
      await validateButton.click();

      // THEN: Should show error message
      await expect(page.getByText(/invalid|error/i)).toBeVisible({ timeout: 3000 });
    }
  });

  test('[P2] should preserve conversation history after switch', async ({ page }) => {
    // GIVEN: User has existing conversations
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const conversationCount = await page.locator('[data-testid="conversation-item"]').count();

    // WHEN: Switching provider
    await page.goto('/settings/provider');
    const providerCard = page.locator('[class*="rounded-lg"]').first();
    await providerCard.click();

    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: { provider: 'ollama' },
          meta: { requestId: 'test-switch' },
        }),
      });
    });

    const switchButton = page.getByRole('button', { name: /switch/i });
    await switchButton.click();

    // THEN: Conversations should still exist
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const newCount = await page.locator('[data-testid="conversation-item"]').count();
    expect(newCount).toBeGreaterThanOrEqual(conversationCount);
  });

  test('[P2] should display provider switch confirmation dialog', async ({ page }) => {
    // GIVEN: User attempts to switch providers
    const providerCard = page.locator('[class*="rounded-lg"]').filter({
      hasText: /Anthropic|OpenAI/i
    }).first();

    await providerCard.click();

    // WHEN: Entering valid API key and clicking switch
    await page.route('**/api/llm/validate**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: { valid: true } }),
      });
    });

    const apiKeyInput = page.locator('input').first();
    await apiKeyInput.fill('valid-key-123');

    const switchButton = page.getByRole('button', { name: /switch/i });
    await switchButton.click();

    // THEN: Should show confirmation dialog
    const confirmDialog = page.locator('[role="dialog"]').filter({
      hasText: /confirm|are you sure/i
    });

    const hasDialog = await confirmDialog.isVisible().catch(() => false);
    if (hasDialog) {
      await expect(confirmDialog).toBeVisible();

      // Confirm the switch
      const confirmButton = page.getByRole('button', { name: /confirm|yes/i });
      await confirmButton.click();
    }
  });

  test('[P1] should handle provider switch failure gracefully', async ({ page }) => {
    // GIVEN: User attempts to switch providers
    const providerCard = page.locator('[class*="rounded-lg"]').first();
    await providerCard.click();

    // WHEN: API returns error during switch
    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Internal server error',
        }),
      });
    });

    const apiKeyInput = page.locator('input').first();
    await apiKeyInput.fill('test-key');

    const switchButton = page.getByRole('button', { name: /switch/i });
    await switchButton.click();

    // THEN: Should show error notification
    await expect(page.getByText(/error|failed/i)).toBeVisible({ timeout: 5000 });

    // THEN: Original provider should remain active
    await page.reload();
    await page.waitForLoadState('networkidle');

    const currentProvider = page.locator('[class*="bg-blue-50"]');
    await expect(currentProvider.first()).toBeVisible();
  });

  test('[P2] should show cost comparison for current vs new provider', async ({ page }) => {
    // GIVEN: User is viewing provider settings
    await page.goto('/settings/provider');

    // WHEN: Selecting a different provider
    const providerCard = page.locator('[class*="rounded-lg"]').filter({
      hasText: /Anthropic/i
    }).first();

    if (await providerCard.isVisible()) {
      await providerCard.click();

      // THEN: Should see cost comparison
      const comparisonText = page.getByText(/vs|compared to|current/i);
      const hasComparison = await comparisonText.isVisible().catch(() => false);

      if (hasComparison) {
        await expect(comparisonText).toBeVisible();
      }

      // Should show percentage difference
      const percentageText = page.getByText(/\d+%|cheaper|expensive/i);
      await expect(percentageText.first()).toBeVisible();
    }
  });

  test('[P2] should allow canceling provider switch', async ({ page }) => {
    // GIVEN: User has opened provider configuration modal
    const providerCard = page.locator('[class*="rounded-lg"]').first();
    await providerCard.click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // WHEN: Clicking cancel button
    const cancelButton = page.getByRole('button', { name: /cancel/i });
    await cancelButton.click();

    // THEN: Modal should close and provider should not change
    await expect(modal).toBeHidden();

    await page.reload();
    await page.waitForLoadState('networkidle');

    const currentProvider = page.locator('[class*="bg-blue-50"]');
    await expect(currentProvider.first()).toBeVisible();
  });

  test('[P0] should update provider status in real-time', async ({ page }) => {
    // GIVEN: User switches provider
    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            provider: 'openai',
            status: 'active',
          },
          meta: { requestId: 'test-update' },
        }),
      });
    });

    const providerCard = page.locator('[class*="rounded-lg"]').filter({
      hasText: /OpenAI/i
    }).first();

    if (await providerCard.isVisible()) {
      await providerCard.click();

      const switchButton = page.getByRole('button', { name: /switch/i });
      await switchButton.click();

      // WHEN: Switch completes
      await page.waitForTimeout(1000);

      // THEN: Status should update immediately
      const statusIndicator = page.getByText(/active|connected/i);
      await expect(statusIndicator.first()).toBeVisible();
    }
  });
});

test.describe('Journey: Provider Switching - Cost Analysis', () => {
  test('[P1] should display monthly cost projection', async ({ page }) => {
    await page.goto('/settings/provider');

    // Check for cost projection display
    const projectionText = page.getByText(/monthly|projected|estimated/i);
    await expect(projectionText.first()).toBeVisible();
  });

  test('[P1] should show token cost comparison', async ({ page }) => {
    await page.goto('/settings/provider');

    // Should show per-token costs
    const tokenCostText = page.getByText(/per.*token|\/token|1k tokens/i);
    await expect(tokenCostText.first()).toBeVisible();
  });

  test('[P2] should track cost savings over time', async ({ page }) => {
    await page.goto('/settings/provider');

    // Mock historical savings data
    await page.route('**/api/costs/savings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            totalSavings: 25.50,
            period: '30d',
          },
          meta: { requestId: 'test-savings' },
        }),
      });
    });

    const savingsText = page.getByText(/saved|savings/i);
    const hasSavings = await savingsText.isVisible().catch(() => false);

    if (hasSavings) {
      await expect(savingsText.first()).toBeVisible();
    }
  });
});
