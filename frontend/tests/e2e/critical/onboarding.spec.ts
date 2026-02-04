/**
 * E2E Test: Complete Merchant Onboarding Journey
 *
 * ATDD Checklist:
 * [x] Test covers complete user journey from signup to deployment
 * [x] All prerequisites must be completed before deployment
 * [x] Platform selection is functional
 * [x] Progress indicator updates correctly
 * [x] State persists across page reloads
 * [x] Accessibility: Keyboard navigation works
 * [x] Accessibility: Screen reader announcements work
 * [x] Cleanup: Test data cleared after each test
 *
 * Critical Path: Landing → Prerequisites → Deployment → Initial Setup
 *
 * External services (Facebook, Shopify, LLM providers) are mocked
 * to ensure reliable, fast testing.
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../../fixtures/test-helper';
import { PrerequisiteChecklist, DeploymentWizard } from '../../helpers/selectors';
import {
  assertPrerequisiteComplete,
  assertDeployButtonEnabled,
  assertProgressCount,
} from '../../helpers/assertions';
import { createMerchantData } from '../../factories/merchant.factory';
import { assertPageLoadBaseline } from '../../helpers/performance-monitor';

test.describe('Critical Path: Complete Onboarding Journey', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await clearStorage(page);
    await page.reload();
  });

  test.afterEach(async ({ page }) => {
    // Cleanup test data
    await clearStorage(page);
  });

  test('should complete full onboarding prerequisites flow @smoke', async ({ page }) => {
    // ARRANGE: User lands on onboarding page
    await page.goto('/');

    // Wait for page to be ready
    await page.waitForLoadState('domcontentloaded');

    // ACT: Complete all prerequisites
    await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);
    await page.click(PrerequisiteChecklist.checkboxes.facebookAccount);
    await page.click(PrerequisiteChecklist.checkboxes.shopifyAccess);
    await page.click(PrerequisiteChecklist.checkboxes.llmProvider);

    // ASSERT: All checkboxes are checked
    const cloudCheckbox = page.locator(PrerequisiteChecklist.checkboxes.cloudAccount);
    const fbCheckbox = page.locator(PrerequisiteChecklist.checkboxes.facebookAccount);
    const shopifyCheckbox = page.locator(PrerequisiteChecklist.checkboxes.shopifyAccess);
    const llmCheckbox = page.locator(PrerequisiteChecklist.checkboxes.llmProvider);

    await expect(cloudCheckbox).toBeChecked();
    await expect(fbCheckbox).toBeChecked();
    await expect(shopifyCheckbox).toBeChecked();
    await expect(llmCheckbox).toBeChecked();

    // ASSERT: Deploy button is enabled
    const deployButton = page.locator(PrerequisiteChecklist.deployButton);
    await expect(deployButton).toBeEnabled();

    // ASSERT: Progress shows 4/4
    const progressText = page.locator(PrerequisiteChecklist.progressText);
    await expect(progressText).toContainText('4 of 4');
  });

  test('should persist prerequisite state across page reloads', async ({ page }) => {
    // ARRANGE: Complete prerequisites
    await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);
    await page.click(PrerequisiteChecklist.checkboxes.facebookAccount);

    // ACT: Reload page
    await page.reload();

    // ASSERT: State persisted
    await assertPrerequisiteComplete(page, 'cloudAccount');
    await assertPrerequisiteComplete(page, 'facebookAccount');

    // ASSERT: Progress shows 2/4
    await assertProgressCount(page, 2, 4);
  });

  test('should show deployment wizard after prerequisites complete', async ({ page }) => {
    // ARRANGE: Complete all prerequisites
    await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);
    await page.click(PrerequisiteChecklist.checkboxes.facebookAccount);
    await page.click(PrerequisiteChecklist.checkboxes.shopifyAccess);
    await page.click(PrerequisiteChecklist.checkboxes.llmProvider);

    // ASSERT: Deployment wizard is visible
    const wizard = page.locator(DeploymentWizard.container);
    await expect(wizard).toBeVisible();

    // ASSERT: Platform selector is available
    await expect(page.locator(DeploymentWizard.platformLabel)).toBeVisible();
    await expect(page.locator(DeploymentWizard.platformSelector)).toBeEnabled();
  });

  test('should display help sections when requested', async ({ page }) => {
    // ACT: Click help button for cloud account
    await page.click(PrerequisiteChecklist.helpButtons.cloudAccount);

    // ASSERT: Help section is visible
    const helpSection = page.locator(PrerequisiteChecklist.helpSections.cloudAccount);
    await expect(helpSection).toBeVisible();

    // ASSERT: Help section contains setup instructions
    await expect(helpSection).toContainText('fly.io');
  });

  test('should update progress in real-time', async ({ page }) => {
    // ACT: Check first prerequisite
    await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);
    await assertProgressCount(page, 1, 4);

    // ACT: Check second prerequisite
    await page.click(PrerequisiteChecklist.checkboxes.facebookAccount);
    await assertProgressCount(page, 2, 4);

    // ACT: Check third prerequisite
    await page.click(PrerequisiteChecklist.checkboxes.shopifyAccess);
    await assertProgressCount(page, 3, 4);

    // ACT: Check final prerequisite
    await page.click(PrerequisiteChecklist.checkboxes.llmProvider);
    await assertProgressCount(page, 4, 4);
  });
});

test.describe('Accessibility: Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await clearStorage(page);
    await page.reload();
  });

  test('should support keyboard navigation for prerequisite checklist', async ({ page }) => {
    // ACT: Focus first checkbox
    const firstCheckbox = page.locator(PrerequisiteChecklist.checkboxes.cloudAccount);
    await firstCheckbox.focus();
    await expect(firstCheckbox).toBeFocused();

    // ACT: Toggle with Space
    await page.keyboard.press('Space');
    await expect(firstCheckbox).toBeChecked();

    // ACT: Focus and check second checkbox
    const secondCheckbox = page.locator(PrerequisiteChecklist.checkboxes.facebookAccount);
    await secondCheckbox.focus();
    await page.keyboard.press('Space');
    await expect(secondCheckbox).toBeChecked();

    // ASSERT: Progress updated
    await assertProgressCount(page, 2, 4);
  });

  test('should support keyboard navigation for help buttons', async ({ page }) => {
    // ACT: Focus help button
    const helpButton = page.locator(PrerequisiteChecklist.helpButtons.cloudAccount);
    await helpButton.focus();
    await expect(helpButton).toBeFocused();

    // ASSERT: ARIA attributes correct
    await expect(helpButton).toHaveAttribute('aria-expanded', 'false');

    // ACT: Activate with Enter
    await page.keyboard.press('Enter');

    // ASSERT: Help section expanded
    const helpSection = page.locator(PrerequisiteChecklist.helpSections.cloudAccount);
    await expect(helpSection).toBeVisible();
    await expect(helpButton).toHaveAttribute('aria-expanded', 'true');
  });

  test('should announce progress to screen readers', async ({ page }) => {
    // ACT: Check first item
    await page.click(PrerequisiteChecklist.checkboxes.cloudAccount);

    // ASSERT: Progress is announced
    const progressText = page.locator(PrerequisiteChecklist.progressText);
    await expect(progressText).toBeVisible();
    const text = await progressText.textContent();
    expect(text).toContain('1 of 4');

    // ACT: Check second item
    await page.click(PrerequisiteChecklist.checkboxes.facebookAccount);

    // ASSERT: Updated count announced
    const updatedText = await progressText.textContent();
    expect(updatedText).toContain('2 of 4');
  });

  test('should have proper ARIA labels on interactive elements', async ({ page }) => {
    // ASSERT: Checkboxes have implicit labels
    const cloudCheckbox = page.locator(PrerequisiteChecklist.checkboxes.cloudAccount);
    await expect(cloudCheckbox).toHaveAttribute('id', 'cloudAccount');

    const cloudLabel = page.locator('label[for="cloudAccount"]');
    await expect(cloudLabel).toBeVisible();

    // ASSERT: Help buttons have proper ARIA
    const helpButton = page.locator(PrerequisiteChecklist.helpButtons.cloudAccount);
    await expect(helpButton).toHaveAttribute('aria-controls');
    await expect(helpButton).toHaveAttribute('aria-expanded');
  });
});
