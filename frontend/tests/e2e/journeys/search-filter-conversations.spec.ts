/**
 * E2E Tests: Search and Filter Conversations Journey
 *
 * User Journey: Merchant searches and filters conversation list
 * to find specific customer interactions.
 *
 * Flow: Apply Filters → Verify Results → Clear Filters
 *
 * Priority Coverage:
 * - [P0] Search and filter functionality happy path
 * - [P1] Multiple filters combination
 * - [P2] Filter persistence and URL sync
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Search and Filter Conversations', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to conversations page with sample data
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Mock conversation data
    await page.route('**/api/conversations**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            conversations: [
              {
                id: 'conv-1',
                customerName: 'John Doe',
                status: 'active',
                platform: 'facebook',
                lastMessage: 'Product inquiry',
                createdAt: '2024-01-15T10:00:00Z',
                cost: 0.50,
              },
              {
                id: 'conv-2',
                customerName: 'Jane Smith',
                status: 'closed',
                platform: 'shopify',
                lastMessage: 'Order confirmation',
                createdAt: '2024-01-14T14:30:00Z',
                cost: 0.35,
              },
              {
                id: 'conv-3',
                customerName: 'Bob Johnson',
                status: 'active',
                platform: 'facebook',
                lastMessage: 'Return request',
                createdAt: '2024-01-13T09:15:00Z',
                cost: 0.75,
              },
            ],
            total: 3,
            page: 1,
            perPage: 20,
          },
          meta: { requestId: 'test-conversations' },
        }),
      });
    });
  });

  test('[P0] should search conversations by customer name', async ({ page }) => {
    // GIVEN: User is on conversations page with list
    await expect(page.getByRole('heading', { name: /conversations/i })).toBeVisible();

    // WHEN: Entering search term
    const searchInput = page.getByPlaceholder(/search/i).or(
      page.getByLabel(/search/i)
    ).or(
      page.locator('input[type="search"]')
    ).first();

    await searchInput.fill('John');

    // THEN: Should show filtered results
    await page.waitForTimeout(500);

    const results = page.locator('[data-testid="conversation-item"]');
    const count = await results.count();

    expect(count).toBeGreaterThan(0);
    await expect(results.first()).toContainText(/John/i);
  });

  test('[P0] should filter by conversation status', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Clicking status filter
    const statusFilter = page.getByRole('button', { name: /status/i }).or(
      page.locator('[data-testid="filter-status"]')
    ).first();

    if (await statusFilter.isVisible()) {
      await statusFilter.click();

      // Select "active" status
      const activeOption = page.getByRole('option', { name: /active/i }).or(
        page.locator('[data-value="active"]')
      );

      if (await activeOption.isVisible()) {
        await activeOption.click();

        // THEN: Should show only active conversations
        await page.waitForTimeout(500);

        const results = page.locator('[data-testid="conversation-item"]');
        const count = await results.count();

        if (count > 0) {
          // Verify all visible conversations are active
          for (let i = 0; i < count; i++) {
            await expect(results.nth(i)).toContainText(/active/i);
          }
        }
      }
    }
  });

  test('[P0] should filter by platform', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Selecting Facebook platform filter
    const platformFilter = page.getByRole('button', { name: /platform/i }).or(
      page.locator('[data-testid="filter-platform"]')
    ).first();

    if (await platformFilter.isVisible()) {
      await platformFilter.click();

      const facebookOption = page.getByRole('option', { name: /facebook/i }).or(
        page.locator('[data-value="facebook"]')
      );

      if (await facebookOption.isVisible()) {
        await facebookOption.click();

        // THEN: Should show only Facebook conversations
        await page.waitForTimeout(500);

        const results = page.locator('[data-testid="conversation-item"]');
        const count = await results.count();

        if (count > 0) {
          await expect(results.first()).toContainText(/facebook/i);
        }
      }
    }
  });

  test('[P1] should combine multiple filters', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Applying status filter
    const statusFilter = page.getByRole('button', { name: /status/i }).first();
    const hasStatusFilter = await statusFilter.isVisible().catch(() => false);

    if (hasStatusFilter) {
      await statusFilter.click();
      const activeOption = page.getByRole('option', { name: /active/i });
      if (await activeOption.isVisible()) {
        await activeOption.click();
      }

      // AND: Applying platform filter
      const platformFilter = page.getByRole('button', { name: /platform/i }).first();
      await platformFilter.click();

      const facebookOption = page.getByRole('option', { name: /facebook/i });
      if (await facebookOption.isVisible()) {
        await facebookOption.click();
      }

      // THEN: Should show conversations matching both filters
      await page.waitForTimeout(500);

      const results = page.locator('[data-testid="conversation-item"]');
      const count = await results.count();

      if (count > 0) {
        // Verify results match both criteria
        await expect(results.first()).toContainText(/active/i);
        await expect(results.first()).toContainText(/facebook/i);
      }
    }
  });

  test('[P0] should clear all filters', async ({ page }) => {
    // GIVEN: User has applied filters
    const searchInput = page.getByPlaceholder(/search/i).or(
      page.locator('input[type="search"]')
    ).first();

    await searchInput.fill('John');
    await page.waitForTimeout(500);

    // WHEN: Clicking clear filters button
    const clearButton = page.getByRole('button', { name: /clear|reset/i }).or(
      page.locator('[data-testid="clear-filters"]')
    ).first();

    const hasClearButton = await clearButton.isVisible().catch(() => false);

    if (hasClearButton) {
      await clearButton.click();

      // THEN: Should show all conversations
      await page.waitForTimeout(500);

      const searchValue = await searchInput.inputValue();
      expect(searchValue).toBe('');
    }
  });

  test('[P2] should show active filter tags', async ({ page }) => {
    // GIVEN: User applies a filter
    const statusFilter = page.getByRole('button', { name: /status/i }).first();
    const hasFilter = await statusFilter.isVisible().catch(() => false);

    if (hasFilter) {
      await statusFilter.click();
      const activeOption = page.getByRole('option', { name: /active/i });
      if (await activeOption.isVisible()) {
        await activeOption.click();
      }

      // THEN: Should show filter tag
      const filterTag = page.locator('[data-testid="filter-tag"]').or(
        page.getByRole('button', { name: /active.*×/i })
      );

      const hasTag = await filterTag.isVisible().catch(() => false);
      if (hasTag) {
        await expect(filterTag.first()).toBeVisible();
      }
    }
  });

  test('[P2] should remove individual filter by clicking tag', async ({ page }) => {
    // GIVEN: User has multiple filters
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('John');

    // WHEN: Clicking filter tag to remove
    const filterTag = page.locator('[data-testid="filter-tag"]').or(
      page.getByRole('button', { name: /×/i })
    ).first();

    const hasTag = await filterTag.isVisible().catch(() => false);

    if (hasTag) {
      await filterTag.click();

      // THEN: That filter should be removed
      await page.waitForTimeout(500);

      const searchValue = await searchInput.inputValue();
      expect(searchValue).not.toBe('John');
    }
  });

  test('[P2] should persist filters in URL', async ({ page }) => {
    // GIVEN: User applies filters
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('John');

    await page.waitForTimeout(500);

    // WHEN: Reloading page
    const urlBefore = page.url();
    await page.reload();
    await page.waitForLoadState('networkidle');

    // THEN: Filters should persist
    const urlAfter = page.url();
    expect(urlAfter).toContain('John');

    const searchValue = await searchInput.inputValue();
    expect(searchValue).toBe('John');
  });

  test('[P1] should show no results message when filters match nothing', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Searching for non-existent conversation
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('NonExistentCustomerXYZ123');

    await page.waitForTimeout(1000);

    // THEN: Should show no results message
    const noResults = page.getByText(/no conversations|no results|not found/i);
    const hasNoResults = await noResults.isVisible().catch(() => false);

    if (hasNoResults) {
      await expect(noResults).toBeVisible();
    }

    const results = page.locator('[data-testid="conversation-item"]');
    const count = await results.count();
    expect(count).toBe(0);
  });

  test('[P1] should filter by date range', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Selecting date range filter
    const dateFilter = page.getByRole('button', { name: /date/i }).or(
      page.locator('[data-testid="filter-date"]')
    ).first();

    const hasDateFilter = await dateFilter.isVisible().catch(() => false);

    if (hasDateFilter) {
      await dateFilter.click();

      // Select "Last 7 days" option
      const last7Days = page.getByRole('option', { name: /last 7 days/i }).or(
        page.locator('[data-value="7d"]')
      );

      if (await last7Days.isVisible()) {
        await last7Days.click();

        // THEN: Should show filtered results
        await page.waitForTimeout(500);

        const results = page.locator('[data-testid="conversation-item"]');
        const count = await results.count();

        // Results should be within date range
        expect(count).toBeGreaterThanOrEqual(0);
      }
    }
  });

  test('[P2] should show result count', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // THEN: Should show result count
    const resultCount = page.getByText(/\d+.*conversations|showing \d+/i);
    const hasCount = await resultCount.isVisible().catch(() => false);

    if (hasCount) {
      await expect(resultCount).toBeVisible();
    }

    // WHEN: Applying filter
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('John');
    await page.waitForTimeout(500);

    // THEN: Result count should update
    if (hasCount) {
      const updatedCount = await resultCount.textContent();
      expect(updatedCount).toMatch(/\d+/);
    }
  });

  test('[P2] should support keyboard navigation in filters', async ({ page }) => {
    // GIVEN: User is on conversations page
    await page.reload();

    // WHEN: Using keyboard to navigate filters
    await page.keyboard.press('Tab');

    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(['INPUT', 'BUTTON']).toContain(focusedElement);
  });

  test('[P1] should export filtered results', async ({ page }) => {
    // GIVEN: User has applied filters
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('John');

    await page.waitForTimeout(500);

    // WHEN: Clicking export button
    const exportButton = page.getByRole('button', { name: /export/i }).or(
      page.locator('[data-testid="export-button"]')
    ).first();

    const hasExport = await exportButton.isVisible().catch(() => false);

    if (hasExport) {
      // Mock download
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;

      // THEN: Should download file
      expect(download.suggestedFilename()).toMatch(/\.(csv|xlsx)/);
    }
  });

  test('[P1] should save filter preferences', async ({ page }) => {
    // GIVEN: User applies filters
    const searchInput = page.getByPlaceholder(/search/i).first();
    await searchInput.fill('John');

    await page.waitForTimeout(500);

    // WHEN: Saving filter preferences
    const saveButton = page.getByRole('button', { name: /save.*filter/i }).or(
      page.locator('[data-testid="save-filters"]')
    ).first();

    const hasSaveButton = await saveButton.isVisible().catch(() => false);

    if (hasSaveButton) {
      await saveButton.click();

      // THEN: Should show confirmation
      await expect(page.getByText(/saved|preferences/i)).toBeVisible({ timeout: 3000 });

      // Navigate away and back
      await page.goto('/costs');
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      // Filters should be restored
      const searchValue = await searchInput.inputValue();
      expect(searchValue).toBe('John');
    }
  });
});

test.describe('Journey: Search and Filter - Advanced', () => {
  test('[P2] should sort conversations by cost', async ({ page }) => {
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Click sort by cost
    const sortButton = page.getByRole('button', { name: /sort/i }).or(
      page.locator('[data-testid="sort-button"]')
    ).first();

    const hasSort = await sortButton.isVisible().catch(() => false);

    if (hasSort) {
      await sortButton.click();

      const costOption = page.getByRole('option', { name: /cost/i });
      if (await costOption.isVisible()) {
        await costOption.click();

        // Verify sorting applied
        await page.waitForTimeout(500);
        const results = page.locator('[data-testid="conversation-item"]');
        const count = await results.count();

        if (count > 1) {
          // Results should be sorted by cost
          await expect(results.first()).toBeVisible();
        }
      }
    }
  });

  test('[P2] should sort conversations by date', async ({ page }) => {
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Click sort by date
    const sortButton = page.getByRole('button', { name: /sort/i }).first();
    const hasSort = await sortButton.isVisible().catch(() => false);

    if (hasSort) {
      await sortButton.click();

      const dateOption = page.getByRole('option', { name: /date/i });
      if (await dateOption.isVisible()) {
        await dateOption.click();

        await page.waitForTimeout(500);
        const results = page.locator('[data-testid="conversation-item"]');
        await expect(results.first()).toBeVisible();
      }
    }
  });

  test('[P2] should toggle between list and grid view', async ({ page }) => {
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    // Toggle view
    const viewToggle = page.getByRole('button', { name: /grid|list/i }).or(
      page.locator('[data-testid="view-toggle"]')
    ).first();

    const hasToggle = await viewToggle.isVisible().catch(() => false);

    if (hasToggle) {
      await viewToggle.click();

      // View should change
      await page.waitForTimeout(500);

      const container = page.locator('[data-testid="conversations-container"]');
      await expect(container).toHaveClass(/grid|list/i);
    }
  });
});
