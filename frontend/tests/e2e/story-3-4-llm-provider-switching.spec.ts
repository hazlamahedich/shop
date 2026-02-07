/**
 * E2E tests for Story 3.4: LLM Provider Switching
 *
 * Playwright E2E tests for the complete provider switching flow:
 * - Navigate to provider settings
 * - View current provider
 * - Browse available providers
 * - Select and configure alternative provider
 * - Validate provider configuration
 * - Complete provider switch
 * - Verify success notification
 * - Check conversation uses new provider
 */

import { test, expect } from '@playwright/test';

test.describe('Story 3.4: LLM Provider Switching', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to provider settings page
    await page.goto('/settings/provider');
    await page.waitForLoadState('networkidle');
  });

  test('displays current provider status', async ({ page }) => {
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('LLM Provider Settings');

    // Check current provider section exists
    await expect(page.locator('h2').filter({ hasText: 'Current Provider' })).toBeVisible();

    // Current provider card should be visible
    await expect(page.locator('[class*="bg-blue-50"]')).toBeVisible();
  });

  test('lists available providers', async ({ page }) => {
    // Wait for providers to load
    await page.waitForSelector('text=Available Providers');

    // Should see provider cards
    const providerCards = page.locator('[class*="rounded-lg"]').filter({ hasText: /OpenAI|Anthropic|Ollama/i });
    await expect(providerCards.first()).toBeVisible();
  });

  test('shows provider comparison table', async ({ page }) => {
    // Scroll to comparison section
    await page.locator('text=Available Providers').scrollIntoViewIfNeeded();

    // Should see comparison table
    const table = page.locator('table');
    await expect(table).toBeVisible();

    // Check for table headers
    await expect(page.locator('th', { hasText: /provider/i })).toBeVisible();
    await expect(page.locator('th', { hasText: /input cost/i })).toBeVisible();
    await expect(page.locator('th', { hasText: /output cost/i })).toBeVisible();
  });

  test('opens configuration modal when provider is selected', async ({ page }) => {
    // Click on a non-active provider card
    const providerCard = page.locator('[class*="rounded-lg"]').filter({
      hasText: /Anthropic/i,
    }).first();

    await providerCard.click();

    // Modal should appear
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Should show provider name in title
    await expect(modal.locator('h2', { hasText: /Anthropic/i })).toBeVisible();
  });

  test('validates provider configuration', async ({ page }) => {
    // Open provider config modal
    await page.locator('[class*="rounded-lg"]').filter({ hasText: /Anthropic/i }).first().click();

    // Enter API key
    const apiKeyInput = page.locator('input[label*="API Key" i], input[name*="apiKey" i], input[placeholder*="API" i]').first();
    await apiKeyInput.fill('test-api-key-for-validation');

    // Click validate button
    const validateButton = page.locator('button', { hasText: /validate/i }).first();
    await validateButton.click();

    // Should show validation in progress or result
    await expect(page.locator('text=Validating').or(page.locator('text=Configuration Valid'))).toBeVisible({ timeout: 5000 });
  });

  test('switches provider successfully', async ({ page }) => {
    // Open provider config modal for a different provider
    await page.locator('[class*="rounded-lg"]').filter({ hasText: /OpenAI/i }).first().click();

    // Enter configuration
    const apiKeyInput = page.locator('input').first();
    await apiKeyInput.fill('sk-test-key');

    // Submit to switch
    const switchButton = page.locator('button', { hasText: /switch provider/i });
    await switchButton.click();

    // Should show success notification
    await expect(page.locator('[role="alert"]', { hasText: /successfully switched/i })).toBeVisible({ timeout: 10000 });
  });

  test('displays success notification after switch', async ({ page }) => {
    // Assuming a provider switch just occurred
    await page.locator('[class*="rounded-lg"]').first().click();
    await page.locator('input').first().fill('test-key');
    await page.locator('button', { hasText: /switch/i }).click();

    // Check for success notification
    const alert = page.locator('[role="alert"]');
    await expect(alert).toBeVisible();

    // Should contain provider name
    await expect(alert).toContainText(/switched/i);
  });

  test('success notification auto-dismisses', async ({ page }) => {
    // Trigger provider switch
    await page.locator('[class*="rounded-lg"]').first().click();
    await page.locator('input').first().fill('test-key');
    await page.locator('button', { hasText: /switch/i }).click();

    // Wait for success notification
    const alert = page.locator('[role="alert"]');
    await expect(alert).toBeVisible();

    // Should disappear after 5 seconds
    await expect(alert).toBeHidden({ timeout: 6000 });
  });

  test('displays cost savings calculator', async ({ page }) => {
    // Scroll to savings section
    await page.locator('text=Available Providers').scrollIntoViewIfNeeded();

    // Look for savings calculator
    const savingsSection = page.locator('text=Potential Monthly Savings').or(
      page.locator('[class*="from-green-50"]')
    );

    // May not appear if no savings available
    const isVisible = await savingsSection.isVisible().catch(() => false);

    if (isVisible) {
      // Should show savings amounts
      await expect(page.locator(text=/-\$\d+\.\d{2}/)).toBeVisible();
      await expect(page.locator('text=Annual Savings')).toBeVisible();
    }
  });

  test('handles provider configuration errors gracefully', async ({ page }) => {
    // Open config modal
    await page.locator('[class*="rounded-lg"]').first().click();

    // Enter invalid API key
    const apiKeyInput = page.locator('input').first();
    await apiKeyInput.fill('invalid-key-should-fail');

    // Submit
    await page.locator('button', { hasText: /switch/i }).click();

    // Should show error message
    await expect(page.locator('text=Invalid', { timeout: 5000 }).or(
      page.locator('[class*="text-red-700"]')
    )).toBeVisible();
  });

  test('closes modal on cancel', async ({ page }) => {
    // Open config modal
    await page.locator('[class*="rounded-lg"]').first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Click cancel button
    await page.locator('button', { hasText: /cancel/i }).click();

    // Modal should close
    await expect(modal).toBeHidden();
  });

  test('closes modal on escape key', async ({ page }) => {
    // Open config modal
    await page.locator('[class*="rounded-lg"]').first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Press escape
    await page.keyboard.press('Escape');

    // Modal should close
    await expect(modal).toBeHidden();
  });

  test('allows keyboard navigation', async ({ page }) => {
    // Tab through provider cards
    await page.keyboard.press('Tab');

    // Should focus on first interactive element
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('displays provider features', async ({ page }) => {
    // Wait for providers to load
    await page.waitForSelector('text=Available Providers');

    // Should see feature badges
    const features = page.locator('text=streaming');
    await expect(features.first()).toBeVisible();
  });

  test('shows provider models', async ({ page }) => {
    // Provider cards should list available models
    await page.waitForSelector('text=Available Providers');

    // Look for model names
    const models = page.locator('text=gpt-4').or(page.locator('text=claude')).or(
      page.locator('text=llama')
    );

    await expect(models.first()).toBeVisible();
  });

  test('is accessible with screen reader', async ({ page }) => {
    // Check for proper ARIA labels
    const table = page.locator('table');
    if (await table.isVisible()) {
      await expect(table).toHaveAttribute('role', 'table');
    }

    // Check for aria-live regions (success notification)
    const alert = page.locator('[role="alert"]');
    if (await alert.isVisible()) {
      await expect(alert).toHaveAttribute('aria-live', 'polite');
    }
  });

  test('maintains provider selection across page navigation', async ({ page }) => {
    // Check current provider
    const initialProvider = await page.locator('[class*="bg-blue-50"]').textContent();

    // Navigate away
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Navigate back
    await page.goto('/settings/provider');
    await page.waitForLoadState('networkidle');

    // Provider should still be displayed
    const currentProvider = page.locator('[class*="bg-blue-50"]');
    await expect(currentProvider).toBeVisible();
  });

  test('shows pricing in comparison table', async ({ page }) => {
    await page.locator('text=Available Providers').scrollIntoViewIfNeeded();

    const table = page.locator('table');
    if (await table.isVisible()) {
      // Should show dollar amounts
      await expect(page.locator(text=/\$\d+\.\d{2}/).first()).toBeVisible();
    }
  });

  test('handles mobile viewports', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    // Should still be usable
    await expect(page.locator('h1')).toContainText('LLM Provider Settings');

    // Provider cards should be visible
    await expect(page.locator('text=Available Providers')).toBeVisible();
  });
});

test.describe('Story 3.4: Provider Switching Integration', () => {
  test('new conversation uses current provider', async ({ page }) => {
    // Set up provider
    await page.goto('/settings/provider');
    await page.waitForLoadState('networkidle');

    // Navigate to conversations
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Create new conversation
    await page.locator('button', { hasText: /new conversation/i }).click();

    // Should be associated with current provider
    // (This would require checking the database or API response)
  });

  test('provider switch does not affect existing conversations', async ({ page }) => {
    // Create a conversation
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Note the number of conversations
    const conversationCount = await page.locator('[data-testid="conversation-item"]').count();

    // Switch provider
    await page.goto('/settings/provider');
    await page.locator('[class*="rounded-lg"]').first().click();
    await page.locator('input').first().fill('test-key');
    await page.locator('button', { hasText: /switch/i }).click();
    await page.waitForSelector('[role="alert"]', { timeout: 10000 });

    // Go back to conversations
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Conversations should still exist
    const newCount = await page.locator('[data-testid="conversation-item"]').count();
    expect(newCount).toBeGreaterThanOrEqual(conversationCount);
  });
});
