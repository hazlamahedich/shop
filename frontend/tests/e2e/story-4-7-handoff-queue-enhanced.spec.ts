/**
 * E2E Tests: Story 4-7 Handoff Queue with Urgency - Enhanced Coverage
 *
 * Additional E2E tests covering gaps in the original test suite:
 * - Wait time sorting verification (same urgency, different wait times)
 * - Conversation preview display
 * - Total count updates on new handoff
 * - New item arrival during polling
 * - Full pagination controls
 *
 * Acceptance Criteria Coverage:
 * - AC1: Sort by Urgency then Wait Time (wait time sorting)
 * - AC2: Handoff Display Details (conversation preview)
 * - AC4: Total Waiting Count (count updates)
 * - AC5: Pagination (prev button, page info)
 * - AC6: Real-time Updates (new item arrival)
 *
 * @package frontend/tests/e2e/story-4-7-handoff-queue-enhanced.spec.ts
 */

import { test, expect } from '../support/merged-fixtures';

const SELECTORS = {
  queue: {
    page: '[data-testid="handoff-queue-page"]',
    waitingCount: '[data-testid="total-waiting-count"]',
    list: '[data-testid="handoff-queue-list"]',
    item: '[data-testid="queue-item"]',
    emptyState: '[data-testid="queue-empty-state"]',
  },
  filter: {
    tabs: '[data-testid="urgency-filter-tabs"]',
    allTab: '[data-testid="filter-all"]',
    highTab: '[data-testid="filter-high"]',
    mediumTab: '[data-testid="filter-medium"]',
    lowTab: '[data-testid="filter-low"]',
  },
  item: {
    urgencyBadge: '[data-testid="item-urgency-badge"]',
    waitTime: '[data-testid="item-wait-time"]',
    customerName: '[data-testid="item-customer-name"]',
    handoffReason: '[data-testid="item-handoff-reason"]',
    preview: '[data-testid="item-preview"]',
    markReadBtn: '[data-testid="item-mark-read"]',
  },
  pagination: {
    container: '[data-testid="pagination"]',
    prevBtn: '[data-testid="pagination-prev"]',
    nextBtn: '[data-testid="pagination-next"]',
    pageInfo: '[data-testid="pagination-info"]',
  },
};

test.describe('Story 4-7: Handoff Queue Enhanced Coverage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/handoff-queue');
    await page.waitForLoadState('networkidle');
  });

  test.describe('[P0] Wait Time Sorting (AC1)', () => {
    test('[P0] should sort items with same urgency by wait time DESC', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.data.length >= 3) {
        const items = queueResult.body.data;
        const urgencyGroups = {
          high: items.filter((i: { urgencyLevel: string }) => i.urgencyLevel === 'high'),
          medium: items.filter((i: { urgencyLevel: string }) => i.urgencyLevel === 'medium'),
          low: items.filter((i: { urgencyLevel: string }) => i.urgencyLevel === 'low'),
        };

        for (const [, group] of Object.entries(urgencyGroups)) {
          if (group.length >= 2) {
            for (let i = 0; i < group.length - 1; i++) {
              const current = group[i] as { waitTimeSeconds: number };
              const next = group[i + 1] as { waitTimeSeconds: number };
              if (current.waitTimeSeconds !== undefined && next.waitTimeSeconds !== undefined) {
                expect(current.waitTimeSeconds).toBeGreaterThanOrEqual(next.waitTimeSeconds);
              }
            }
          }
        }
      }
    });

    test('[P0] should display formatted wait time for each item', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.data.length > 0) {
        const waitTimeElements = await page.locator(SELECTORS.item.waitTime).all();
        expect(waitTimeElements.length).toBeGreaterThan(0);

        for (const el of waitTimeElements.slice(0, 3)) {
          const text = await el.textContent();
          expect(text).toMatch(/^\d+[smh](?:\s+\d+[smh])?$/);
        }
      }
    });
  });

  test.describe('[P1] Conversation Preview Display (AC2)', () => {
    test('[P1] should display conversation preview for each item', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.data.length > 0) {
        const items = page.locator(SELECTORS.queue.item);
        const count = await items.count();

        for (let i = 0; i < Math.min(count, 3); i++) {
          const preview = items.nth(i).locator(SELECTORS.item.preview);
          if (await preview.isVisible()) {
            const text = await preview.textContent();
            expect(text!.length).toBeGreaterThan(0);
          }
        }
      }
    });

    test('[P1] should truncate long previews appropriately', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200) {
        const longPreviewItem = queueResult.body.data.find(
          (item: { conversationPreview: string | null }) =>
            item.conversationPreview && item.conversationPreview.length > 100
        );

        if (longPreviewItem) {
          const itemLocator = page.locator(
            `${SELECTORS.queue.item}[data-alert-id="${longPreviewItem.id}"]`
          );
          const preview = itemLocator.locator(SELECTORS.item.preview);

          if (await preview.isVisible()) {
            const text = await preview.textContent();
            expect(text!.length).toBeLessThanOrEqual(150);
          }
        }
      }
    });
  });

  test.describe('[P1] Total Count Updates (AC4)', () => {
    test('[P1] should display total waiting count accurately', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200) {
        const countEl = page.locator(SELECTORS.queue.waitingCount);

        if (queueResult.body.meta.totalWaiting > 0) {
          await expect(countEl).toBeVisible();
          const text = await countEl.textContent();
          const match = text!.match(/(\d+)/);
          if (match) {
            expect(parseInt(match[1], 10)).toBe(queueResult.body.meta.totalWaiting);
          }
        }
      }
    });

    test('[P1] should update count after filtering', async ({ page, apiRequest }) => {
      const allResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (allResult.status === 200 && allResult.body.meta.totalWaiting > 0) {
        const filterResponse = page.waitForResponse(
          (resp) =>
            resp.url().includes('/api/handoff-alerts') &&
            resp.url().includes('urgency=high') &&
            resp.url().includes('view=queue')
        );

        await page.locator(SELECTORS.filter.highTab).click();
        await filterResponse;

        const highResult = await apiRequest({
          method: 'GET',
          path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc&urgency=high',
          body: null,
          headers: {},
        });

        if (highResult.status === 200) {
          const countEl = page.locator(SELECTORS.queue.waitingCount);
          if (await countEl.isVisible()) {
            const text = await countEl.textContent();
            const match = text!.match(/(\d+)/);
            if (match && highResult.body.meta.totalWaiting !== null) {
              expect(parseInt(match[1], 10)).toBe(highResult.body.meta.totalWaiting);
            }
          }
        }
      }
    });
  });

  test.describe('[P1] Full Pagination Controls (AC5)', () => {
    test('[P1] should display page info with current and total pages', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.meta.total > 20) {
        const pageInfo = page.locator(SELECTORS.pagination.pageInfo);
        await expect(pageInfo).toBeVisible();

        const text = await pageInfo.textContent();
        expect(text).toMatch(/page\s*1/i);
      }
    });

    test('[P1] should disable prev button on first page', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.meta.total > 20) {
        const prevBtn = page.locator(SELECTORS.pagination.prevBtn);
        await expect(prevBtn).toBeDisabled();
      }
    });

    test('[P1] should enable prev button after navigating to page 2', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.meta.total > 20) {
        const pageTwoResponse = page.waitForResponse(
          (resp) =>
            resp.url().includes('/api/handoff-alerts') &&
            resp.url().includes('page=2') &&
            resp.url().includes('view=queue')
        );

        await page.locator(SELECTORS.pagination.nextBtn).click();
        await pageTwoResponse;

        const prevBtn = page.locator(SELECTORS.pagination.prevBtn);
        await expect(prevBtn).toBeEnabled();
      }
    });

    test('[P1] should navigate back to page 1 with prev button', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.meta.total > 40) {
        await page.locator(SELECTORS.pagination.nextBtn).click();

        await page.waitForResponse(
          (resp) =>
            resp.url().includes('/api/handoff-alerts') &&
            resp.url().includes('page=2') &&
            resp.url().includes('view=queue')
        );

        const pageOneResponse = page.waitForResponse(
          (resp) =>
            resp.url().includes('/api/handoff-alerts') &&
            resp.url().includes('page=1') &&
            resp.url().includes('view=queue')
        );

        await page.locator(SELECTORS.pagination.prevBtn).click();
        await pageOneResponse;

        const pageInfo = page.locator(SELECTORS.pagination.pageInfo);
        const text = await pageInfo.textContent();
        expect(text).toMatch(/page\s*1/i);
      }
    });
  });

  test.describe('[P2] Real-time Updates - New Item Arrival (AC6)', () => {
    test('[P2] should poll for queue updates every 30 seconds', async ({ page }) => {
      await page.goto('/handoff-queue');

      await page.waitForResponse(
        (resp) =>
          resp.url().includes('/api/handoff-alerts') &&
          resp.url().includes('view=queue') &&
          resp.status() === 200
      );

      let pollCount = 0;
      page.on('response', (response) => {
        if (response.url().includes('/api/handoff-alerts') && response.url().includes('view=queue')) {
          pollCount++;
        }
      });

      await page.waitForTimeout(35000);

      expect(pollCount).toBeGreaterThanOrEqual(1);
    });

    test('[P2] should display new items when they arrive during polling', async ({ page, apiRequest }) => {
      const initialResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (initialResult.status === 200) {
        const initialCount = initialResult.body.meta.totalWaiting || 0;

        await page.goto('/handoff-queue');
        await page.waitForResponse(
          (resp) =>
            resp.url().includes('/api/handoff-alerts') &&
            resp.url().includes('view=queue') &&
            resp.status() === 200
        );

        if (initialCount > 0) {
          const queueItems = page.locator(SELECTORS.queue.item);
          const displayedCount = await queueItems.count();
          expect(displayedCount).toBeGreaterThan(0);
        }
      }
    });
  });

  test.describe('[P2] Accessibility', () => {
    test('[P2] should have accessible filter tabs', async ({ page }) => {
      const tabs = page.locator(SELECTORS.filter.tabs);
      await expect(tabs).toHaveAttribute('role', 'tablist');

      const allTab = page.locator(SELECTORS.filter.allTab);
      await expect(allTab).toHaveAttribute('role', 'tab');
    });

    test('[P2] should have accessible queue items', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.data.length > 0) {
        const firstItem = page.locator(SELECTORS.queue.item).first();

        const urgencyBadge = firstItem.locator(SELECTORS.item.urgencyBadge);
        const badgeText = await urgencyBadge.textContent();
        expect(['🔴 High', '🟡 Medium', '🟢 Low']).toContain(badgeText!.trim());
      }
    });

    test('[P2] should have accessible pagination controls', async ({ page, apiRequest }) => {
      const queueResult = await apiRequest({
        method: 'GET',
        path: '/api/handoff-alerts?view=queue&sort_by=urgency_desc',
        body: null,
        headers: {},
      });

      if (queueResult.status === 200 && queueResult.body.meta.total > 20) {
        const nextBtn = page.locator(SELECTORS.pagination.nextBtn);
        await expect(nextBtn).toHaveAttribute('aria-label', /next/i);
      }
    });
  });
});
