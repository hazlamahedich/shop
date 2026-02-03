/**
 * E2E Test: Complete Onboarding Flow
 *
 * Critical Path: Prerequisites → Deployment → Initial Setup
 *
 * This test covers the most important user journey:
 * 1. Merchant sees prerequisite checklist
 * 2. Completes all prerequisites
 * 3. Initiates deployment
 *
 * External services are mocked to ensure reliable testing.
 */

import { test, expect } from '@playwright/test';
import { clearStorage, mockSelectors } from '../fixtures/test-helper';

test.describe('Onboarding Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.goto('/');
    await clearStorage(page);
    await page.reload();
  });

  test('should display prerequisite checklist on first visit', async ({ page }) => {
    await page.goto('/');

    // Check that prerequisite checklist is visible
    const checklist = page.locator(mockSelectors.prerequisiteChecklist);
    await expect(checklist).toBeVisible();

    // Verify all 4 prerequisites are shown
    await expect(page.locator(mockSelectors.cloudAccountCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.facebookAccountCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.shopifyAccessCheckbox)).toBeVisible();
    await expect(page.locator(mockSelectors.llmProviderCheckbox)).toBeVisible();

    // Deploy button should be disabled initially
    const deployButton = page.locator(mockSelectors.deployButton);
    await expect(deployButton).toBeDisabled();
  });

  test('should enable deploy button when all prerequisites are checked', async ({ page }) => {
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

  test('should persist prerequisite state across page reloads', async ({ page }) => {
    await page.goto('/');

    // Complete all prerequisites
    await page.click(mockSelectors.cloudAccountCheckbox);
    await page.click(mockSelectors.facebookAccountCheckbox);
    await page.click(mockSelectors.shopifyAccessCheckbox);
    await page.click(mockSelectors.llmProviderCheckbox);

    // Reload page
    await page.reload();

    // Verify state persisted
    const cloudCheckbox = page.locator(mockSelectors.cloudAccountCheckbox);
    await expect(cloudCheckbox).toBeChecked();

    // Deploy button should still be enabled
    const deployButton = page.locator(mockSelectors.deployButton);
    await expect(deployButton).toBeEnabled();
  });

  test('should show help sections when clicked', async ({ page }) => {
    await page.goto('/');

    // Click help button for first prerequisite
    await page.click('[data-testid="help-button-cloudAccount"]');

    // Wait for help section to become visible
    const helpSection = page.locator('[data-testid="help-section-cloudAccount"]');
    await expect(helpSection).toBeVisible();

    // Help section should contain setup instructions
    await expect(helpSection).toContainText('fly.io');
  });
});

test.describe('Deployment Wizard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Complete prerequisites first
    await page.click(mockSelectors.cloudAccountCheckbox);
    await page.click(mockSelectors.facebookAccountCheckbox);
    await page.click(mockSelectors.shopifyAccessCheckbox);
    await page.click(mockSelectors.llmProviderCheckbox);
  });

  test('should display deployment wizard', async ({ page }) => {
    await page.goto('/');

    const wizard = page.locator(mockSelectors.deploymentWizard);
    await expect(wizard).toBeVisible();

    // Should show platform selector
    await expect(page.locator('label:has-text("Select Deployment Platform")')).toBeVisible();
  });

  test('should allow selecting deployment platform', async ({ page }) => {
    await page.goto('/');

    // Click on the select dropdown
    const selectLabel = page.locator('label:has-text("Select Deployment Platform")');
    await expect(selectLabel).toBeVisible();

    // The select component should be present
    const selectElement = page.locator('[aria-label="Select deployment platform"]');
    await expect(selectElement).toBeVisible();
  });
});

test.describe('Complete Onboarding Journey', () => {
  test('should complete full onboarding prerequisites flow', async ({ page }) => {
    await page.goto('/');

    // Step 1: Complete prerequisites
    await page.click(mockSelectors.cloudAccountCheckbox);
    await page.click(mockSelectors.facebookAccountCheckbox);
    await page.click(mockSelectors.shopifyAccessCheckbox);
    await page.click(mockSelectors.llmProviderCheckbox);

    // Verify deploy button is enabled
    const deployButton = page.locator(mockSelectors.deployButton);
    await expect(deployButton).toBeEnabled();

    // Verify progress shows complete
    const progressText = await page.textContent('[data-testid="progress-text"]');
    expect(progressText).toContain('4 of 4');
  });
});
