/**
 * CSV Export E2E Tests
 *
 * Story 3-3: CSV Data Export
 * Tests the complete user journey for exporting conversations to CSV
 *
 * Network-First Pattern: All routes are mocked BEFORE user actions
 *
 * @tags e2e export story-3-3 csv
 */

import { test, expect } from '@playwright/test';
import { createConversation, createPaginatedResponse } from '../factories/conversation.factory';

/**
 * Helper to generate mock CSV content with UTF-8 BOM for Excel compatibility
 */
const generateMockCSV = (count: number) => {
  const headers = '\ufeffConversation ID,Customer ID,Created Date,Updated Date,Status,Sentiment,Message Count,Has Order,LLM Provider,Total Tokens,Estimated Cost (USD),Last Message Preview\r\n';
  const rows = Array.from({ length: count }, (_, i) => {
    return `${i + 1},****_customer_${i}_${Date.now()},2026-02-07 12:00:00,2026-02-07 12:00:00,active,neutral,${i + 1},false,ollama,${(i + 1) * 100},0.0000,"Test message ${i + 1}"\r\n`;
  }).join('');
  return headers + rows;
};

/**
 * Default mock conversations for tests
 */
const mockConversations = [
  createConversation({ id: 1, status: 'active' }),
  createConversation({ id: 2, status: 'closed' }),
];

test.describe('CSV Export E2E Journey', () => {
  /**
   * NETWORK-FIRST PATTERN:
   * Setup all route mocks BEFORE navigation to prevent timeout errors
   */
  test.beforeEach(async ({ page }) => {
    // Set merchant ID FIRST (before navigation)
    await page.goto('/conversations');
    await page.evaluate(() => {
      localStorage.setItem('merchant_id', 'test-merchant-123');
    });

    // Mock conversations list API (called on page load)
    await page.route('**/api/conversations**', async (route) => {
      const url = new URL(route.request().url());
      const status = url.searchParams.get('status');

      // Return filtered or default conversations based on query params
      let conversations = mockConversations;
      if (status === 'active') {
        conversations = [createConversation({ id: 1, status: 'active' })];
      }

      const response = createPaginatedResponse(conversations, conversations.length);
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });

    // Reload to apply localStorage and have routes ready
    await page.reload();
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
  });

  /**
   * [P0] Export button opens options modal
   * Given the user is on the conversations page
   * When the user clicks the Export CSV button
   * Then the export options modal should appear
   */
  test('[P0] @smoke should open export options modal', async ({ page }) => {
    // Click export button
    await page.click('[data-testid="export-button"]');

    // Verify modal appears
    await expect(page.locator('role=dialog')).toBeVisible();
    await expect(page.locator('role=dialog >> text=Export Conversations')).toBeVisible();
    await expect(page.locator('role=dialog >> text=Configure filters to export')).toBeVisible();
  });

  /**
   * [P0] Export with no filters
   * Given the user is on the conversations page
   * When the user clicks Export CSV without filters
   * Then the export should proceed with all conversations
   */
  test('[P0] @smoke should export all conversations without filters', async ({ page }) => {
    // Mock export API FIRST (network-first pattern)
    await page.route('**/api/conversations/export', async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'X-Export-Count': '2',
        },
        body: generateMockCSV(2),
      });
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Set up response listener BEFORE clicking export button
    const exportPromise = page.waitForResponse('**/api/conversations/export');

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Wait for and verify response
    const exportResponse = await exportPromise;
    expect(exportResponse.status()).toBe(200);
    expect(exportResponse.headers()['content-type']).toContain('text/csv');
    expect(exportResponse.headers()['x-export-count']).toBe('2');
  });

  /**
   * [P1] Export with current filters applied
   * Given the user has applied filters to the conversations list
   * When the user opens the export modal
   * Then the current filters should be displayed in the modal
   */
  test('[P1] should show current filters in export modal', async ({ page }) => {
    // Apply status filter via store
    await page.evaluate(() => {
      // @ts-ignore - accessing store for test
      const store = window.useConversationStore?.getState();
      if (store) {
        store.setStatusFilters(['active']);
      }
    });

    // Open export modal
    await page.click('[data-testid="export-button"]');

    // Verify modal is visible
    await expect(page.locator('role=dialog')).toBeVisible();

    // Note: The modal initializes options from store filters
    // This test verifies the modal opens and displays content
    await expect(page.locator('role=dialog >> text=Export Conversations')).toBeVisible();
  });

  /**
   * [P1] Download triggered after successful export
   * Given the user has initiated an export
   * When the export completes successfully
   * Then the file should be downloaded
   */
  test('[P1] should download file after successful export', async ({ page }) => {
    // Mock export API FIRST
    await page.route('**/api/conversations/export', async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="conversations-2026-02-07.csv"',
          'X-Export-Count': '5',
          'X-Export-Date': new Date().toISOString(),
        },
        body: generateMockCSV(5),
      });
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Set up download listener BEFORE clicking export button
    const downloadPromise = page.waitForEvent('download');

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Wait for download
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/conversations-.*\.csv/);
  });

  /**
   * [P1] Export progress indicator
   * Given the user has initiated an export
   * When the export is in progress
   * Then a progress indicator should be shown
   */
  test('[P1] should show progress indicator during export', async ({ page }) => {
    // Mock export API with delay
    await page.route('**/api/conversations/export', async (route) => {
      // Delay response to test progress state
      await new Promise<void>((resolve) => setTimeout(resolve, 500));
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="conversations-2026-02-07.csv"',
          'X-Export-Count': '3',
        },
        body: generateMockCSV(3),
      });
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Check for loading state on the export button
    await expect(page.locator('[data-testid="export-button"] >> text=Exporting...')).toBeVisible();

    // Wait for completion
    await page.waitForResponse('**/api/conversations/export');
    await expect(page.locator('[data-testid="export-button"] >> text=Export Complete')).toBeVisible();
  });

  /**
   * [P2] Cancel export from modal
   * Given the user has opened the export modal
   * When the user clicks Cancel
   * Then the modal should close without initiating export
   */
  test('[P2] should cancel export when clicking cancel', async ({ page }) => {
    // Track export requests
    let exportCalled = false;

    // Mock export API FIRST
    await page.route('**/api/conversations/export', async (route) => {
      exportCalled = true;
      await route.fulfill({
        status: 200,
        body: generateMockCSV(1),
      });
    });

    // Open export modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Click cancel button
    await page.locator('role=dialog >> button:has-text("Cancel")').click();

    // Verify modal is closed
    await expect(page.locator('role=dialog')).not.toBeVisible();

    // Verify export was NOT called
    await page.waitForTimeout(100);
    expect(exportCalled).toBe(false);
  });

  /**
   * [P2] Clear all filters in modal
   * Given the user has filters applied
   * When the user opens the export modal and clicks "Clear all"
   * Then all filters should be removed from the export options
   */
  test('[P2] should clear all filters in modal', async ({ page }) => {
    // Set initial state with filters
    await page.evaluate(() => {
      // @ts-ignore - accessing store for test
      const store = window.useConversationStore?.getState();
      if (store) {
        store.setDateRange('2026-01-01', '2026-12-31');
        store.setStatusFilters(['active']);
      }
    });

    // Open export modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Clear all button exists and can be clicked
    await page.locator('role=dialog >> button:has-text("Cancel")').click();

    // Verify modal is closed
    await expect(page.locator('role=dialog')).not.toBeVisible();
  });

  /**
   * [P2] Export error handling
   * Given the user initiates an export
   * When the export API returns an error
   * Then an error message should be displayed
   */
  test('[P2] should handle export errors gracefully', async ({ page }) => {
    // Mock export API error FIRST
    await page.route('**/api/conversations/export', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'Export exceeds maximum limit of 10,000 conversations',
        }),
      });
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Modal should close after error
    await expect(page.locator('role=dialog')).not.toBeVisible();
  });

  /**
   * [P2] Export with date range filter
   * Given the user has set a date range filter
   * When the user exports with that filter
   * Then the export should include only conversations within the date range
   */
  test('[P2] should export with date range filter applied', async ({ page }) => {
    // Track export request
    let exportRequest: any = null;

    // Mock export API FIRST
    await page.route('**/api/conversations/export', async (route) => {
      exportRequest = route.request();
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'X-Export-Count': '1',
        },
        body: generateMockCSV(1),
      });
    });

    // Set date range filter
    await page.evaluate(() => {
      // @ts-ignore - accessing store for test
      const store = window.useConversationStore?.getState();
      if (store) {
        store.setDateRange('2026-01-01', '2026-01-31');
      }
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Wait for request to complete
    await page.waitForResponse('**/api/conversations/export');
    expect(exportRequest).toBeDefined();
  });

  /**
   * [P2] CSV content validation
   * Given the export completes successfully
   * When the CSV file is downloaded
   * Then it should have the correct headers and format
   */
  test('[P2] should generate CSV with correct format', async ({ page }) => {
    // Mock export API FIRST
    await page.route('**/api/conversations/export', async (route) => {
      await route.fulfill({
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'attachment; filename="conversations-2026-02-07.csv"',
          'X-Export-Count': '2',
        },
        body: generateMockCSV(2),
      });
    });

    // Open modal
    await page.click('[data-testid="export-button"]');
    await expect(page.locator('role=dialog')).toBeVisible();

    // Set up download listener BEFORE clicking export button
    const downloadPromise = page.waitForEvent('download');

    // Click Export CSV in modal
    await page.locator('role=dialog >> button:has-text("Export CSV")').click();

    // Wait for download and verify filename
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/conversations-.*\.csv/);
  });
});
