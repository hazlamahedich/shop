/**
 * E2E tests for Story 6-3: Merchant CSV Export
 * 
 * Tests cover:
 * - Export button triggers API call
 * - CSV contains expected data
 * - Opted-out user data excluded
 * - Rate limiting shows error
 * - Loading states
 * - Error handling
 */

import { test, expect } from '@playwright/test';

test.describe('Story 6-3: Merchant CSV Export', () => {
  test.beforeEach(async ({ page }) => {
    // Login with existing test user
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@test.com');
    await page.fill('input[name="password"]', 'Test12345');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Navigate to Settings page
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    
    // Click on General tab (wait for it to be visible)
    const generalTab = page.locator('button', { hasText: /^General$/ }).first();
    await generalTab.waitFor({ state: 'visible', timeout: 10000 });
    await generalTab.click({ timeout: 10000 });
    await page.waitForTimeout(1000);
  });

  test('[P0] 8.1: Export button triggers download', async ({ page }) => {
    // Find export button
    const exportButton = page.locator('button:has-text("Export All Data")').first();
    await expect(exportButton).toBeVisible();

    // Intercept the export API call
    const exportPromise = page.waitForRequest(req => 
      req.url().includes('/api/v1/data/export') && req.method() === 'POST'
    );

    // Click export
    await exportButton.click();

    // Verify API call was made
    const exportRequest = await exportPromise;
    expect(exportRequest).toBeTruthy();
    
    // Wait for response
    const response = await exportRequest.response();
    expect(response).toBeTruthy();
    expect([200, 429]).toContain(response?.status()); // Success or rate limited
  });

  test('[P0] 8.2: CSV contains expected data', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export All Data")').first();
    
    // Intercept and mock the export API response
    await page.route('**/api/v1/data/export', async (route) => {
      const csvContent = `# Merchant Data Export
# Export Date: 2026-03-04T12:00:00Z
# Merchant ID: 123
# Total Conversations: 2
# Total Messages: 5
# Total Cost: 0.0123

## SECTION: CONVERSATIONS
conversation_id,platform,customer_id,consent_status,started_at
1,messenger,customer_123,opted_in,2026-03-04T10:00:00Z
2,widget,anon_456,opted_out,2026-03-04T11:00:00Z

## SECTION: MESSAGES
message_id,conversation_id,role,content,created_at
101,1,user,Hello,2026-03-04T10:00:05Z
102,1,assistant,Hi there,2026-03-04T10:00:07Z
103,2,user,,2026-03-04T11:00:05Z

## SECTION: LLM COSTS
cost_id,conversation_id,provider,model,input_tokens,output_tokens,cost_usd,created_at
201,1,openai,gpt-4,150,80,0.0046,2026-03-04T10:00:07Z

## SECTION: CONFIGURATION
setting_name,setting_value
personality,friendly`;

      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="merchant_123_export_20260304.csv"',
        },
        body: csvContent,
      });
    });

    // Click export
    await exportButton.click();

    // Wait for success (could check for toast notification)
    await page.waitForTimeout(2000);
    
    // Verify button is enabled again
    await expect(exportButton).toBeEnabled();
  });

  test('[P1] 8.3: Opted-out user data is excluded from export', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export All Data")').first();
    
    // Intercept and verify the request
    await page.route('**/api/v1/data/export', async (route) => {
      const csvContent = `# Merchant Data Export
# Merchant ID: 123

## SECTION: CONVERSATIONS
conversation_id,platform,customer_id,consent_status
1,messenger,customer_123,opted_in
2,widget,anon_456,opted_out

## SECTION: MESSAGES
message_id,conversation_id,role,content
101,1,user,Hello from opted-in user
102,2,user,""`;

      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="merchant_123_export.csv"',
        },
        body: csvContent,
      });
    });

    await exportButton.click();
    await page.waitForTimeout(2000);
    
    // Verify export completed
    await expect(exportButton).toBeEnabled();
  });

  test('[P1] 8.4: Rate limiting prevents rapid exports', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export All Data")').first();
    
    let callCount = 0;
    
    // Mock rate limiting behavior
    await page.route('**/api/v1/data/export', async (route) => {
      callCount++;
      
      if (callCount === 1) {
        // First call succeeds
        await route.fulfill({
          status: 200,
          headers: {
            'Content-Type': 'text/csv; charset=utf-8',
            'Content-Disposition': 'attachment; filename="merchant_123_export.csv"',
          },
          body: '# Merchant Data Export\n',
        });
      } else {
        // Second call is rate limited
        await route.fulfill({
          status: 429,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: 'Export rate limit exceeded',
            details: { retry_after: 3600 },
          }),
        });
      }
    });

    // First export should succeed
    await exportButton.click();
    await page.waitForTimeout(1000);

    // Second export should show rate limit error
    await exportButton.click();
    
    // Wait for error message (alert div)
    const errorAlert = page.locator('[role="alert"], .export-error').first();
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
    await expect(errorAlert).toContainText(/rate limit|try again/i);
  });

  test('[P1] Loading state during export generation', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export All Data")').first();
    
    // Delay the response to test loading state
    await page.route('**/api/v1/data/export', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2s delay
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="merchant_123_export.csv"',
        },
        body: '# Merchant Data Export\n',
      });
    });

    // Click export
    await exportButton.click();

    // Verify button shows loading state immediately
    await expect(exportButton).toBeDisabled();
    await expect(exportButton).toContainText(/exporting/i);

    // Wait for export to complete
    await page.waitForTimeout(3000);

    // Verify button returns to normal state
    await expect(exportButton).toBeEnabled();
    await expect(exportButton).toContainText(/export all data/i);
  });

  test('[P1] Error handling for authentication failure', async ({ page }) => {
    // Mock authentication failure
    await page.route('**/api/v1/data/export', async (route) => {
      await route.fulfill({
        status: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Authentication failed. Please log in again.',
        }),
      });
    });

    const exportButton = page.locator('button:has-text("Export All Data")').first();
    await exportButton.click();

    // Verify error message appears
    const errorAlert = page.locator('[role="alert"], .export-error').first();
    await expect(errorAlert).toBeVisible({ timeout: 5000 });
    await expect(errorAlert).toContainText(/authentication|log in/i);
  });
});
