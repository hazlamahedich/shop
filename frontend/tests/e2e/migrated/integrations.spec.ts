/**
 * E2E Test: External Integrations Flow (Migrated)
 *
 * Critical Path: Prerequisites → Deployment → Initial Setup
 *
 * This test covers the visible components:
 * 1. Prerequisite Checklist (always visible)
 * 2. Deployment Wizard (always visible)
 *
 * Note: Facebook, Shopify, and LLM components are conditionally rendered
 * after OAuth connections are made, making them difficult to test in E2E
 * without complex setup. These are better covered by integration tests.
 *
 * MIGRATED: Now uses new selectors and helpers
 */

import { test, expect } from '@playwright/test';
import { clearStorage, mockSelectors } from '../../fixtures/test-helper';

test.describe('Complete Onboarding Flow', () => {
  test('should show prerequisite checklist and deployment wizard', async ({ page }) => {
    await page.goto('/');
    await clearStorage(page);

    // Should show prerequisite checklist
    await expect(page.locator('[data-testid="prerequisite-checklist"]')).toBeVisible();

    // Should show deployment wizard
    await expect(page.locator('[data-testid="deployment-wizard"]')).toBeVisible();
  });

  test('should show all prerequisite items', async ({ page }) => {
    await page.goto('/');

    // Verify all 4 prerequisites are shown
    await expect(page.locator(mockSelectors.cloudAccountCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.facebookAccountCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.shopifyAccessCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.llmProviderCheckbox)).toBeVisible();
  });

  test('should complete prerequisites and enable deploy button', async ({ page }) => {
    await page.goto('/');

    // Complete all prerequisites
    await page.click(mockSelectors.cloudAccountCheckbox);
    await page.click(mockSelectors.facebookAccountCheckbox);
    await page.click(mockSelectors.shopifyAccessCheckbox);
    await page.click(mockSelectors.llmProviderCheckbox);

    // Verify deploy button is enabled
    const deployButton = page.locator(mockSelectors.deployButton);
    await expect(deployButton).toBeEnabled();

    // Verify progress shows 4/4 completed
    const progressText = await page.textContent('[data-testid="progress-text"]');
    expect(progressText).toContain('4 of 4');
  });
});
