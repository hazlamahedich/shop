/**
 * E2E tests for Data Tier Separation (Story 6-4)
 * 
 * Tests verify:
 * - Dashboard tier distribution widget displays correctly
 * - Analytics summary loads and displays anonymized data
 * - Consent opt-out flow updates tier status in UI
 */

import { test, expect } from '@playwright/test';

test.describe('Data Tier Separation - Story 6-4', () => {
  test.beforeEach(async ({ page }) => {
    // Login as test merchant
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
  });

  test('9.1 - Dashboard widget displays tier distribution correctly', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.goto('/dashboard/analytics');
    
    // Wait for tier distribution widget to load
    await page.waitForSelector('[data-testid="tier-distribution-widget"]', {
      timeout: 10000
    });

    // Verify all three tiers are displayed
    const voluntarySection = page.locator('[data-testid="tier-voluntary"]');
    const operationalSection = page.locator('[data-testid="tier-operational"]');
    const anonymizedSection = page.locator('[data-testid="tier-anonymized"]');

    await expect(voluntarySection).toBeVisible();
    await expect(operationalSection).toBeVisible();
    await expect(anonymizedSection).toBeVisible();

    // Verify tier labels are correct
    await expect(voluntarySection.locator('.tier-label')).toContainText('Voluntary');
    await expect(operationalSection.locator('.tier-label')).toContainText('Operational');
    await expect(anonymizedSection.locator('.tier-label')).toContainText('Anonymized');

    // Verify counts are displayed (not errors)
    await expect(voluntarySection.locator('.tier-count')).not.toBeEmpty();
    await expect(operationalSection.locator('.tier-count')).not.toBeEmpty();
    await expect(anonymizedSection.locator('.tier-count')).not.toBeEmpty();

    // Verify counts are numeric
    const voluntaryCount = await voluntarySection.locator('.tier-count').textContent();
    const operationalCount = await operationalSection.locator('.tier-count').textContent();
    const anonymizedCount = await anonymizedSection.locator('.tier-count').textContent();

    expect(voluntaryCount).toMatch(/^\d+$/);
    expect(operationalCount).toMatch(/^\d+$/);
    expect(anonymizedCount).toMatch(/^\d+$/);
  });

  test('9.2 - Analytics summary loads and displays anonymized data', async ({ page }) => {
    // Navigate to analytics summary page
    await page.goto('/dashboard/analytics/summary');
    
    // Wait for analytics summary to load
    await page.waitForSelector('[data-testid="analytics-summary"]', {
      timeout: 10000
    });

    // Verify key metrics are displayed
    const totalConversations = page.locator('[data-testid="total-conversations"]');
    const totalMessages = page.locator('[data-testid="total-messages"]');
    const totalOrders = page.locator('[data-testid="total-orders"]');

    await expect(totalConversations).toBeVisible();
    await expect(totalMessages).toBeVisible();
    await expect(totalOrders).toBeVisible();

    // Verify no PII is displayed
    const pageContent = await page.textContent('body');
    
    // Should not contain email addresses
    expect(pageContent).not.toMatch(/[\w.-]+@[\w.-]+\.\w+/);
    
    // Should not contain phone numbers
    expect(pageContent).not.toMatch(/\d{3}-\d{3}-\d{4}/);
    
    // Should not contain session IDs or user IDs
    expect(pageContent).not.toMatch(/user_\w+/);
    expect(pageContent).not.toMatch(/session_\w+/);

    // Verify "Anonymized" badge is displayed
    const anonymizedBadge = page.locator('[data-testid="anonymized-badge"]');
    await expect(anonymizedBadge).toBeVisible();
    await expect(anonymizedBadge).toContainText('Anonymized');
  });

  test('9.3 - Consent opt-out flow updates tier status in UI', async ({ page }) => {
    // Navigate to privacy settings
    await page.goto('/dashboard/settings/privacy');
    
    // Wait for consent settings to load
    await page.waitForSelector('[data-testid="consent-settings"]', {
      timeout: 10000
    });

    // Check current consent status
    const consentStatus = page.locator('[data-testid="consent-status"]');
    const currentStatus = await consentStatus.textContent();

    // If opted in, proceed with opt-out test
    if (currentStatus?.includes('Opted In')) {
      // Click opt-out button
      const optOutButton = page.locator('[data-testid="opt-out-button"]');
      await optOutButton.click();

      // Confirm opt-out in modal
      const confirmModal = page.locator('[data-testid="opt-out-confirm-modal"]');
      await expect(confirmModal).toBeVisible();
      await confirmModal.locator('button:has-text("Confirm")').click();

      // Wait for success message
      await page.waitForSelector('[data-testid="opt-out-success"]', {
        timeout: 10000
      });

      // Verify consent status updated
      await expect(consentStatus).toContainText('Opted Out');

      // Verify tier status indicator shows "Anonymized"
      const tierIndicator = page.locator('[data-testid="data-tier-indicator"]');
      await expect(tierIndicator).toBeVisible();
      await expect(tierIndicator).toContainText('Anonymized');

      // Verify explanation message
      const explanationMessage = page.locator('[data-testid="tier-explanation"]');
      await expect(explanationMessage).toBeVisible();
      await expect(explanationMessage).toContainText('Your conversation history has been anonymized');
    }
  });

  test('9.4 - Tier distribution chart renders correctly', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.goto('/dashboard/analytics');
    
    // Wait for tier distribution chart to render
    await page.waitForSelector('[data-testid="tier-distribution-chart"]', {
      timeout: 10000
    });

    // Verify chart is visible
    const chart = page.locator('[data-testid="tier-distribution-chart"]');
    await expect(chart).toBeVisible();

    // Verify chart legend
    const legend = chart.locator('.chart-legend');
    await expect(legend).toContainText('Voluntary');
    await expect(legend).toContainText('Operational');
    await expect(legend).toContainText('Anonymized');

    // Verify chart segments are present (pie chart or bar chart)
    const segments = chart.locator('.chart-segment');
    const segmentCount = await segments.count();
    expect(segmentCount).toBeGreaterThanOrEqual(3);

    // Verify each segment has correct color coding
    const voluntarySegment = chart.locator('.chart-segment.voluntary');
    const operationalSegment = chart.locator('.chart-segment.operational');
    const anonymizedSegment = chart.locator('.chart-segment.anonymized');

    // Check color classes or inline styles
    await expect(voluntarySegment).toHaveClass(/voluntary/);
    await expect(operationalSegment).toHaveClass(/operational/);
    await expect(anonymizedSegment).toHaveClass(/anonymized/);
  });

  test('9.5 - Analytics summary refreshes correctly', async ({ page }) => {
    // Navigate to analytics summary
    await page.goto('/dashboard/analytics/summary');
    
    // Wait for initial load
    await page.waitForSelector('[data-testid="analytics-summary"]', {
      timeout: 10000
    });

    // Capture initial timestamp
    const initialTimestamp = await page.locator('[data-testid="generated-at"]').textContent();

    // Click refresh button
    const refreshButton = page.locator('[data-testid="refresh-summary-button"]');
    await refreshButton.click();

    // Wait for loading indicator
    await page.waitForSelector('[data-testid="loading-indicator"]', {
      timeout: 5000
    });

    // Wait for new data to load
    await page.waitForSelector('[data-testid="loading-indicator"]', {
      state: 'hidden',
      timeout: 15000
    });

    // Verify timestamp updated
    const newTimestamp = await page.locator('[data-testid="generated-at"]').textContent();
    expect(newTimestamp).not.toBe(initialTimestamp);
  });

  test('9.6 - Tier distribution updates after data changes', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.goto('/dashboard/analytics');
    
    // Capture initial tier distribution
    const voluntaryCount = await page.locator('[data-testid="tier-voluntary"] .tier-count').textContent();
    const initialVoluntary = parseInt(voluntaryCount || '0');

    // Navigate to conversation list
    await page.goto('/dashboard/conversations');
    
    // Delete a voluntary conversation (if any exist)
    const deleteButtons = page.locator('[data-testid="delete-conversation-button"]');
    const buttonCount = await deleteButtons.count();

    if (buttonCount > 0) {
      await deleteButtons.first().click();
      
      // Confirm deletion
      const confirmModal = page.locator('[data-testid="delete-confirm-modal"]');
      await confirmModal.locator('button:has-text("Confirm")').click();

      // Wait for success
      await page.waitForSelector('[data-testid="delete-success"]', {
        timeout: 10000
      });

      // Navigate back to analytics
      await page.goto('/dashboard/analytics');
      
      // Wait for tier distribution to reload
      await page.waitForSelector('[data-testid="tier-distribution-widget"]', {
        timeout: 10000
      });

      // Verify voluntary count decreased
      const newVoluntaryCount = await page.locator('[data-testid="tier-voluntary"] .tier-count').textContent();
      const newVoluntary = parseInt(newVoluntaryCount || '0');
      
      expect(newVoluntary).toBeLessThan(initialVoluntary);
    }
  });

  test('9.7 - Error handling when analytics API fails', async ({ page }) => {
    // Intercept analytics API call and force error
    await page.route('**/api/v1/analytics/summary', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error_code: 1002,
          message: 'Internal server error'
        })
      });
    });

    // Navigate to analytics summary
    await page.goto('/dashboard/analytics/summary');

    // Verify error message is displayed
    const errorMessage = page.locator('[data-testid="error-message"]');
    await expect(errorMessage).toBeVisible();
    await expect(errorMessage).toContainText('Failed to load analytics');

    // Verify retry button is available
    const retryButton = page.locator('[data-testid="retry-button"]');
    await expect(retryButton).toBeVisible();

    // Clear route intercept
    await page.unroute('**/api/v1/analytics/summary');

    // Click retry
    await retryButton.click();

    // Wait for successful load
    await page.waitForSelector('[data-testid="analytics-summary"]', {
      timeout: 10000
    });
  });

  test('9.8 - Accessibility - tier distribution widget', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.goto('/dashboard/analytics');
    
    // Wait for widget to load
    await page.waitForSelector('[data-testid="tier-distribution-widget"]', {
      timeout: 10000
    });

    // Verify ARIA labels
    const widget = page.locator('[data-testid="tier-distribution-widget"]');
    
    // Check for proper heading structure
    const heading = widget.locator('h2, h3');
    await expect(heading).toContainText('Data Tier Distribution');

    // Verify screen reader text for tier counts
    const voluntarySR = widget.locator('[data-testid="tier-voluntary"] .sr-only');
    await expect(voluntarySR).toContainText('Voluntary tier:');

    // Verify keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();

    // Verify color contrast (manual check with accessibility tools)
    // This would typically be done with automated accessibility testing tools
  });
});

test.describe('Data Tier Separation - Mobile', () => {
  test.use({ viewport: { width: 375, height: 667 } });

  test('9.9 - Mobile responsive tier distribution', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    // Navigate to analytics
    await page.goto('/dashboard/analytics');
    
    // Wait for mobile layout
    await page.waitForSelector('[data-testid="tier-distribution-widget"]', {
      timeout: 10000
    });

    // Verify mobile-specific layout
    const widget = page.locator('[data-testid="tier-distribution-widget"]');
    
    // Should stack vertically on mobile
    const voluntarySection = widget.locator('[data-testid="tier-voluntary"]');
    const operationalSection = widget.locator('[data-testid="tier-operational"]');
    const anonymizedSection = widget.locator('[data-testid="tier-anonymized"]');

    // All sections should be visible
    await expect(voluntarySection).toBeVisible();
    await expect(operationalSection).toBeVisible();
    await expect(anonymizedSection).toBeVisible();

    // Verify mobile menu toggle is visible
    const mobileMenuToggle = page.locator('[data-testid="mobile-menu-toggle"]');
    await expect(mobileMenuToggle).toBeVisible();
  });
});
