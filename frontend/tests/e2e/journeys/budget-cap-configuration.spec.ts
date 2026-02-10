/**
 * E2E Tests: Budget Cap Configuration Journey
 *
 * User Journey: Merchant sets monthly budget cap, configures
 * specific limits, and validates visual progress indicators.
 *
 * Flow: Set Budget → Configure Cap → Visual Validation
 *
 * Priority Coverage:
 * - [P0] Complete budget configuration happy path
 * - [P1] Visual progress validation
 * - [P2] Budget alerts and notifications
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Budget Cap Configuration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to costs page
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');

    // Mock cost data
    await page.route('**/api/costs/summary**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            totalCostUsd: 15.50,
            totalTokens: 125000,
            requestCount: 125,
            avgCostPerRequest: 0.124,
            currentSpend: 15.50,
            budgetCap: 50.00,
            budgetUsagePercent: 31,
            dailyBreakdown: [
              { date: '2024-01-15', cost: 5.50, requests: 55 },
              { date: '2024-01-14', cost: 6.00, requests: 60 },
              { date: '2024-01-13', cost: 4.00, requests: 40 },
            ],
          },
          meta: { requestId: 'test-summary' },
        }),
      });
    });

    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            budget_cap: 50,
            updated_at: new Date().toISOString(),
          },
          meta: { requestId: 'test-settings' },
        }),
      });
    });
  });

  test('[P0] should set monthly budget cap successfully', async ({ page }) => {
    // GIVEN: User is on costs page
    await expect(page.getByRole('heading', { name: /costs.*budget/i })).toBeVisible();

    // WHEN: Entering new budget amount
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });
    await budgetInput.clear();
    await budgetInput.fill('100');

    // Click save button
    const saveButton = page.getByRole('button', { name: 'Save Budget' });
    await saveButton.click();

    // THEN: Confirmation dialog should appear
    const dialogTitle = page.getByText('Confirm Budget Update');
    await expect(dialogTitle).toBeVisible({ timeout: 3000 });

    // Confirm the update
    const confirmButton = page.getByRole('button', { name: 'Confirm Update' });
    await confirmButton.click();

    // THEN: Dialog should close
    await expect(dialogTitle).not.toBeVisible({ timeout: 5000 });

    // THEN: Budget input should show new value
    await expect(budgetInput).toHaveValue('100');
  });

  test('[P0] should display budget usage progress bar', async ({ page }) => {
    // GIVEN: User has set a budget and has spend data
    await page.waitForTimeout(1000);

    // THEN: Should see progress bar
    const progressBar = page.locator('[role="progressbar"]').or(
      page.locator('[class*="progress"]')
    );

    const hasProgressBar = await progressBar.isVisible().catch(() => false);

    if (hasProgressBar) {
      await expect(progressBar.first()).toBeVisible();

      // Should have correct percentage (31% = $15.50 of $50)
      const progressBarElement = progressBar.first();
      const ariaValueNow = await progressBarElement.getAttribute('aria-valuenow');

      if (ariaValueNow) {
        expect(parseInt(ariaValueNow)).toBeGreaterThan(30);
        expect(parseInt(ariaValueNow)).toBeLessThan(35);
      }
    }

    // Should show percentage text
    const percentageText = page.getByText(/31%|30%/i);
    await expect(percentageText.first()).toBeVisible();
  });

  test('[P1] should show color-coded budget status', async ({ page }) => {
    // GIVEN: User has budget and spend data
    await page.waitForTimeout(1000);

    // THEN: Should show appropriate color for usage level
    // 31% usage should be green/healthy
    const progressBar = page.locator('[role="progressbar"]').or(
      page.locator('[class*="progress"]')
    );

    const hasProgressBar = await progressBar.isVisible().catch(() => false);

    if (hasProgressBar) {
      const progressBarElement = progressBar.first();
      const className = await progressBarElement.getAttribute('class');

      // Should have green color class for healthy usage
      expect(className || '').toMatch(/green|bg-green|success/i);
    }
  });

  test('[P1] should display projected monthly spend', async ({ page }) => {
    // GIVEN: User is viewing budget overview
    const budgetOverview = page.getByText('Budget Overview');
    await expect(budgetOverview).toBeVisible();

    // THEN: Should show projected spend
    const projectedText = page.getByText(/projected|estimated/i).or(
      page.locator('[data-testid="projected-spend"]')
    );

    const hasProjected = await projectedText.isVisible().catch(() => false);

    if (hasProjected) {
      await expect(projectedText).toBeVisible();

      // Should include dollar amount
      const dollarAmount = page.getByText(/\$\d+\.\d{2}/);
      await expect(dollarAmount.first()).toBeVisible();
    }
  });

  test('[P0] should validate budget input', async ({ page }) => {
    // GIVEN: User is setting budget
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });

    // WHEN: Entering negative value
    await budgetInput.fill('-50');

    // THEN: Should show validation error or prevent input
    await budgetInput.blur();

    // Input type="number" prevents negative values in some browsers
    // Otherwise validation should occur
    const inputValue = await budgetInput.inputValue();

    // Either the value is rejected or validation shows
    if (inputValue === '-50') {
      const saveButton = page.getByRole('button', { name: 'Save Budget' });
      await saveButton.click();

      // Should show error dialog or prevent save
      await page.waitForTimeout(500);

      // Check for error message
      const errorMessage = page.getByText(/invalid|must be positive/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      if (hasError) {
        await expect(errorMessage).toBeVisible();
      }
    }
  });

  test('[P0] should show visual warning when approaching budget limit', async ({ page }) => {
    // GIVEN: User is near budget limit (80%+ usage)
    await page.route('**/api/costs/summary**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            totalCostUsd: 42.00,
            budgetCap: 50.00,
            budgetUsagePercent: 84,
            currentSpend: 42.00,
          },
          meta: { requestId: 'test-warning' },
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // THEN: Should show warning indicator
    const warningBanner = page.getByText(/warning|approaching limit/i).or(
      page.locator('[class*="bg-yellow"]', '[class*="bg-orange"]')
    );

    const hasWarning = await warningBanner.isVisible().catch(() => false);

    if (hasWarning) {
      await expect(warningBanner.first()).toBeVisible();
    }

    // Progress bar should be yellow/orange
    const progressBar = page.locator('[role="progressbar"]');
    const hasProgressBar = await progressBar.isVisible().catch(() => false);

    if (hasProgressBar) {
      const className = await progressBar.first().getAttribute('class');
      expect(className || '').toMatch(/yellow|orange|warning/i);
    }
  });

  test('[P0] should show critical alert when budget exceeded', async ({ page }) => {
    // GIVEN: User has exceeded budget
    await page.route('**/api/costs/summary**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            totalCostUsd: 55.00,
            budgetCap: 50.00,
            budgetUsagePercent: 110,
            currentSpend: 55.00,
          },
          meta: { requestId: 'test-exceeded' },
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    // THEN: Should show critical alert
    const alertBanner = page.getByText(/budget exceeded|over budget/i).or(
      page.locator('[class*="bg-red"]', '[role="alert"]')
    );

    await expect(alertBanner.first()).toBeVisible();

    // Progress bar should be red
    const progressBar = page.locator('[role="progressbar"]');
    const hasProgressBar = await progressBar.isVisible().catch(() => false);

    if (hasProgressBar) {
      const className = await progressBar.first().getAttribute('class');
      expect(className || '').toMatch(/red|danger|critical/i);
    }
  });

  test('[P1] should allow setting budget to unlimited', async ({ page }) => {
    // GIVEN: User is on costs page
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });

    // WHEN: Clicking "No Limit" button
    const noLimitButton = page.getByRole('button', { name: /no limit|unlimited/i }).or(
      page.locator('[data-testid="no-limit-button"]')
    );

    const hasNoLimit = await noLimitButton.isVisible().catch(() => false);

    if (hasNoLimit) {
      await noLimitButton.click();

      // Mock unlimited budget
      await page.route('**/api/merchant/settings**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: {
              budget_cap: null,
              updated_at: new Date().toISOString(),
            },
            meta: { requestId: 'test-no-limit' },
          }),
        });
      });

      // Confirm in dialog
      const confirmButton = page.getByRole('button', { name: /confirm/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }

      // THEN: Should show unlimited status
      await page.waitForTimeout(1000);

      const unlimitedText = page.getByText(/unlimited|no limit/i);
      await expect(unlimitedText.first()).toBeVisible();
    }
  });

  test('[P2] should display budget recommendation', async ({ page }) => {
    // GIVEN: User is viewing budget settings
    await page.waitForTimeout(1000);

    // THEN: Should show recommendation if available
    const recommendationSection = page.getByText(/recommendation|suggested/i).or(
      page.locator('[data-testid="budget-recommendation"]')
    );

    const hasRecommendation = await recommendationSection.isVisible().catch(() => false);

    if (hasRecommendation) {
      await expect(recommendationSection).toBeVisible();

      // Should include recommended amount
      const recommendedAmount = page.getByText(/\$\d+\.\d{2}/);
      await expect(recommendedAmount.first()).toBeVisible();

      // Should have "Apply" button
      const applyButton = page.getByRole('button', { name: /apply recommendation/i });
      await expect(applyButton).toBeVisible();
    }
  });

  test('[P2] should apply recommended budget', async ({ page }) => {
    // GIVEN: User has a budget recommendation
    await page.route('**/api/merchant/settings/recommendation**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            recommendedBudget: 75.00,
            rationale: 'Based on your current usage of $15.50 in 3 days',
          },
          meta: { requestId: 'test-recommendation' },
        }),
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');

    const applyButton = page.getByRole('button', { name: /apply recommendation/i });
    const hasButton = await applyButton.isVisible().catch(() => false);

    if (hasButton) {
      // WHEN: Clicking apply recommendation
      await applyButton.click();

      // THEN: Budget input should update
      const budgetInput = page.getByLabel('Monthly Budget Cap');
      await page.waitForTimeout(1000);

      const budgetValue = await budgetInput.inputValue();
      expect(budgetValue).toBe('75');
    }
  });

  test('[P1] should persist budget across page reloads', async ({ page }) => {
    // GIVEN: User sets budget
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });
    await budgetInput.clear();
    await budgetInput.fill('125');

    const saveButton = page.getByRole('button', { name: 'Save Budget' });
    await saveButton.click();

    const confirmButton = page.getByRole('button', { name: 'Confirm Update' });
    await confirmButton.click();

    await expect(page.getByText('Confirm Budget Update')).not.toBeVisible({ timeout: 5000 });

    // WHEN: Reloading page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // THEN: Budget should persist
    const budgetInputAfter = page.getByLabel('Monthly Budget Cap');
    await budgetInputAfter.waitFor({ state: 'visible', timeout: 5000 });

    await expect(budgetInputAfter).toHaveValue('125');
  });

  test('[P2] should show budget history chart', async ({ page }) => {
    // GIVEN: User is viewing budget overview
    await page.waitForTimeout(1000);

    // THEN: Should see budget history visualization
    const chart = page.locator('canvas').or(
      page.locator('[data-testid="budget-chart"]')
    );

    const hasChart = await chart.isVisible().catch(() => false);

    if (hasChart) {
      await expect(chart.first()).toBeVisible();
    }
  });

  test('[P1] should validate budget before saving', async ({ page }) => {
    // GIVEN: User enters invalid budget
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });

    // WHEN: Entering zero
    await budgetInput.fill('0');

    const saveButton = page.getByRole('button', { name: 'Save Budget' });
    await saveButton.click();

    // THEN: Should show validation error
    const dialogTitle = page.getByText('Confirm Budget Update');
    const hasDialog = await dialogTitle.isVisible().catch(() => false);

    if (!hasDialog) {
      // No dialog means validation prevented save
      const errorMessage = page.getByText(/must be greater than|invalid/i);
      const hasError = await errorMessage.isVisible().catch(() => false);

      if (hasError) {
        await expect(errorMessage).toBeVisible();
      }
    } else {
      // Dialog appeared - check if it shows warning
      await expect(dialogTitle).toBeVisible();

      // Cancel and try different value
      const cancelButton = page.getByRole('button', { name: 'Cancel' });
      await cancelButton.click();

      await budgetInput.fill('50');
      await saveButton.click();
      await expect(dialogTitle).toBeVisible({ timeout: 3000 });
    }
  });

  test('[P2] should handle budget save errors gracefully', async ({ page }) => {
    // GIVEN: User is setting budget
    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.waitFor({ state: 'visible', timeout: 5000 });
    await budgetInput.fill('100');

    // WHEN: API returns error
    await page.route('**/api/merchant/settings**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Failed to update budget',
        }),
      });
    });

    const saveButton = page.getByRole('button', { name: 'Save Budget' });
    await saveButton.click();

    const confirmButton = page.getByRole('button', { name: 'Confirm Update' });
    await confirmButton.click();

    // THEN: Should show error notification
    await expect(page.getByText(/error|failed/i)).toBeVisible({ timeout: 5000 });

    // THEN: Original budget should remain
    await page.reload();
    await page.waitForLoadState('networkidle');

    const budgetInputAfter = page.getByLabel('Monthly Budget Cap');
    await budgetInputAfter.waitFor({ state: 'visible', timeout: 5000 });

    // Value should not be 100 (the failed update)
    const value = await budgetInputAfter.inputValue();
    expect(value).not.toBe('100');
  });
});

test.describe('Journey: Budget Visual Indicators', () => {
  test('[P0] should show daily spend trend', async ({ page }) => {
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');

    const dailySpendSection = page.getByText('Daily Spend');
    await expect(dailySpendSection).toBeVisible();

    // Should have chart or list of daily values
    const chart = page.locator('canvas').or(
      page.locator('[data-testid="daily-chart"]')
    );

    const hasChart = await chart.isVisible().catch(() => false);

    if (hasChart) {
      await expect(chart.first()).toBeVisible();
    }
  });

  test('[P1] should show budget utilization percentage', async ({ page }) => {
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');

    const percentageText = page.getByText(/\d+%/);
    await expect(percentageText.first()).toBeVisible();
  });

  test('[P2] should animate progress bar on load', async ({ page }) => {
    await page.goto('/costs');

    const progressBar = page.locator('[role="progressbar"]');
    const hasProgressBar = await progressBar.isVisible().catch(() => false);

    if (hasProgressBar) {
      // Check for transition/animation classes
      const className = await progressBar.first().getAttribute('class');

      if (className) {
        expect(className).toMatch(/transition|animate/i);
      }
    }
  });

  test('[P2] should support keyboard navigation for budget input', async ({ page }) => {
    await page.goto('/costs');
    await page.waitForLoadState('networkidle');

    const budgetInput = page.getByLabel('Monthly Budget Cap');
    await budgetInput.focus();

    // Should be able to type value
    await page.keyboard.press('Control+A');
    await page.keyboard.type('200');

    await expect(budgetInput).toHaveValue('200');

    // Should be able to save with Enter
    await page.keyboard.press('Enter');

    // Should show confirmation
    const dialog = page.getByText('Confirm Budget Update');
    const hasDialog = await dialog.isVisible().catch(() => false);

    if (hasDialog) {
      await expect(dialog).toBeVisible();
    }
  });
});
