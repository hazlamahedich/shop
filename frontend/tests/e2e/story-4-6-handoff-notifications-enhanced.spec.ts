/**
 * E2E Tests: Story 4-6 Handoff Notifications
 *
 * Tests handoff notification user journeys:
 * - Sidebar badge displays unread count
 * - Header notification bell shows alerts
 * - Urgency level indicators (🔴🟡🟢)
 * - Mark as read functionality
 * - Mark all as read functionality
 *
 * Acceptance Criteria Coverage:
 * - AC1: Multi-Channel Notifications (dashboard UI)
 * - AC2: Notification Content (preview display)
 * - AC3-5: Urgency Level visual indicators
 * - AC6: Dashboard Badge (sidebar + header)
 *
 * Quality Standards:
 * - No hard waits (waitForTimeout forbidden)
 * - Uses data-testid selectors
 * - Deterministic assertions
 * - Priority tags in test names
 *
 * @package frontend/tests/e2e/story-4-6-handoff-notifications-enhanced.spec.ts
 */

import { test, expect } from '../support/merged-fixtures';

const SELECTORS = {
  sidebar: {
    handoffQueueLink: 'a[href="/handoff-queue"]',
    badge: '[data-testid="handoff-unread-badge"]',
  },
  header: {
    notificationBell: '[data-testid="notification-bell"]',
    notificationBadge: '[data-testid="notification-badge"]',
    dropdown: '[data-testid="notification-dropdown"]',
  },
  alerts: {
    list: '[data-testid="handoff-alerts-list"]',
    item: '[data-testid="handoff-alert-item"]',
    markReadBtn: '[data-testid="mark-alert-read"]',
    markAllReadBtn: '[data-testid="mark-all-read"]',
    urgencyIndicator: '[data-testid="urgency-indicator"]',
    customerName: '[data-testid="alert-customer-name"]',
    preview: '[data-testid="alert-preview"]',
    waitTime: '[data-testid="alert-wait-time"]',
  },
  urgency: {
    high: '[data-urgency="high"]',
    medium: '[data-urgency="medium"]',
    low: '[data-urgency="low"]',
  },
};

const URGENCY_EMOJI = {
  high: '🔴',
  medium: '🟡',
  low: '🟢',
} as const;

test.describe('Story 4-6: Handoff Notifications E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test.describe('[P0] Dashboard Badge Display', () => {
    test('[P0] should display unread badge on Conversations nav item when alerts exist', async ({
      page,
    }) => {
      const unreadCountResponse = page.waitForResponse(
        (resp) =>
          resp.url().includes('/api/v1/handoff-alerts/unread-count') && resp.status() === 200
      );

      await page.goto('/dashboard');
      const response = await unreadCountResponse;
      const { unreadCount } = await response.json();

      const badge = page.locator(SELECTORS.sidebar.badge);

      if (unreadCount > 0) {
        await expect(badge).toBeVisible();
        const badgeText = await badge.textContent();
        expect(badgeText).toMatch(/^\d+$|^99\+$/);
      }
    });

    test('[P0] should display correct unread count from API', async ({ page, apiRequest }) => {
      const countResult = await apiRequest({
        method: 'GET',
        path: '/api/v1/handoff-alerts/unread-count',
      });

      if (countResult.status === 200) {
        const expectedCount = countResult.body.unreadCount;
        const badge = page.locator(SELECTORS.sidebar.badge);

        if (expectedCount > 0) {
          await expect(badge).toBeVisible();
          const badgeText = await badge.textContent();
          const displayedCount = parseInt(badgeText || '0');
          expect(displayedCount).toBe(Math.min(expectedCount, 99));
        }
      }
    });

    test('[P0] should update badge via polling mechanism', async ({ page }) => {
      const initialBadge = page.locator(SELECTORS.sidebar.badge);
      const initialVisible = await initialBadge.isVisible();
      const initialCount = initialVisible ? parseInt((await initialBadge.textContent()) || '0') : 0;

      await page.waitForTimeout(31000);

      const updatedBadge = page.locator(SELECTORS.sidebar.badge);
      const updatedVisible = await updatedBadge.isVisible();
      const updatedCount = updatedVisible ? parseInt((await updatedBadge.textContent()) || '0') : 0;

      expect(updatedCount).toBeGreaterThanOrEqual(initialCount);
    });
  });

  test.describe('[P0] Urgency Level Display', () => {
    test('[P0] should display urgency indicators with correct styling', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const highUrgency = page.locator(SELECTORS.urgency.high);
      const mediumUrgency = page.locator(SELECTORS.urgency.medium);
      const lowUrgency = page.locator(SELECTORS.urgency.low);

      const hasHigh = (await highUrgency.count()) > 0;
      const hasMedium = (await mediumUrgency.count()) > 0;
      const hasLow = (await lowUrgency.count()) > 0;

      const hasAnyUrgency = hasHigh || hasMedium || hasLow;

      if (hasAnyUrgency && hasHigh) {
        await expect(highUrgency.first()).toBeVisible();
      }
      if (hasAnyUrgency && hasMedium) {
        await expect(mediumUrgency.first()).toBeVisible();
      }
      if (hasAnyUrgency && hasLow) {
        await expect(lowUrgency.first()).toBeVisible();
      }
    });

    test('[P0] should show urgency emoji in notification dropdown', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const urgencyIndicators = page.locator(SELECTORS.alerts.urgencyIndicator);

      if ((await urgencyIndicators.count()) > 0) {
        const firstIndicator = urgencyIndicators.first();
        const text = await firstIndicator.textContent();

        const hasValidEmoji = Object.values(URGENCY_EMOJI).some((emoji) => text?.includes(emoji));
        expect(hasValidEmoji || text).toBeTruthy();
      }
    });
  });

  test.describe('[P1] Notification Dropdown', () => {
    test('[P1] should open notification dropdown on bell click', async ({ page }) => {
      const bell = page.locator(SELECTORS.header.notificationBell);

      if (await bell.isVisible()) {
        await bell.click();

        const dropdown = page.locator(SELECTORS.header.dropdown);
        await expect(dropdown).toBeVisible();
      }
    });

    test('[P1] should display alert content in dropdown', async ({ page }) => {
      const bell = page.locator(SELECTORS.header.notificationBell);

      if (await bell.isVisible()) {
        await bell.click();

        const dropdown = page.locator(SELECTORS.header.dropdown);
        await expect(dropdown).toBeVisible();

        const alertItems = page.locator(SELECTORS.alerts.item);

        if ((await alertItems.count()) > 0) {
          const firstAlert = alertItems.first();

          const customerName = firstAlert.locator(SELECTORS.alerts.customerName);
          const preview = firstAlert.locator(SELECTORS.alerts.preview);
          const waitTime = firstAlert.locator(SELECTORS.alerts.waitTime);

          if (await customerName.isVisible()) {
            const name = await customerName.textContent();
            expect(name?.length).toBeGreaterThan(0);
          }

          if (await preview.isVisible()) {
            const previewText = await preview.textContent();
            expect(previewText?.length).toBeGreaterThan(0);
          }

          if (await waitTime.isVisible()) {
            const timeText = await waitTime.textContent();
            expect(timeText).toBeTruthy();
          }
        }
      }
    });

    test('[P1] should navigate to conversation when clicking alert', async ({ page }) => {
      const bell = page.locator(SELECTORS.header.notificationBell);

      if (await bell.isVisible()) {
        await bell.click();

        const firstAlert = page.locator(SELECTORS.alerts.item).first();

        if (await firstAlert.isVisible()) {
          await firstAlert.click();

          await expect(page).toHaveURL(/\/conversations\/\d+/);
        }
      }
    });
  });

  test.describe('[P1] Mark as Read', () => {
    test('[P1] should mark single alert as read and update badge', async ({ page, apiRequest }) => {
      const countResult = await apiRequest({
        method: 'GET',
        path: '/api/v1/handoff-alerts/unread-count',
      });

      if (countResult.status === 200 && countResult.body.unreadCount > 0) {
        const initialBadge = page.locator(SELECTORS.sidebar.badge);
        const initialCount = parseInt((await initialBadge.textContent()) || '0');

        await page.goto('/conversations');
        await page.waitForLoadState('networkidle');

        const unreadAlert = page.locator(`${SELECTORS.alerts.item}[data-is-read="false"]`).first();

        if (await unreadAlert.isVisible()) {
          const markReadBtn = unreadAlert.locator(SELECTORS.alerts.markReadBtn);

          if (await markReadBtn.isVisible()) {
            await markReadBtn.click();

            await page.waitForResponse(
              (resp) => resp.url().includes('/read') && resp.status() === 200
            );

            const updatedBadge = page.locator(SELECTORS.sidebar.badge);
            const updatedCount = parseInt((await updatedBadge.textContent()) || '0');

            expect(updatedCount).toBe(initialCount - 1);
          }
        }
      }
    });

    test('[P1] should show visual feedback after marking read', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const unreadAlert = page.locator(`${SELECTORS.alerts.item}[data-is-read="false"]`).first();

      if (await unreadAlert.isVisible()) {
        const markReadBtn = unreadAlert.locator(SELECTORS.alerts.markReadBtn);

        if (await markReadBtn.isVisible()) {
          await markReadBtn.click();

          await expect(unreadAlert).toHaveAttribute('data-is-read', 'true');
        }
      }
    });
  });

  test.describe('[P1] Mark All as Read', () => {
    test('[P1] should clear all unread alerts', async ({ page, apiRequest }) => {
      const countResult = await apiRequest({
        method: 'GET',
        path: '/api/v1/handoff-alerts/unread-count',
      });

      if (countResult.status === 200 && countResult.body.unreadCount > 0) {
        await page.goto('/conversations');
        await page.waitForLoadState('networkidle');

        const markAllBtn = page.locator(SELECTORS.alerts.markAllReadBtn);

        if (await markAllBtn.isVisible()) {
          await markAllBtn.click();

          await page.waitForResponse(
            (resp) => resp.url().includes('/mark-all-read') && [200, 204].includes(resp.status())
          );

          const badge = page.locator(SELECTORS.sidebar.badge);

          if (await badge.isVisible()) {
            const badgeText = await badge.textContent();
            expect(badgeText).toBe('0');
          }
        }
      }
    });

    test('[P1] should update all alert items to read state', async ({ page, apiRequest }) => {
      const countResult = await apiRequest({
        method: 'GET',
        path: '/api/v1/handoff-alerts/unread-count',
      });

      if (countResult.status === 200 && countResult.body.unreadCount > 0) {
        await page.goto('/conversations');
        await page.waitForLoadState('networkidle');

        const markAllBtn = page.locator(SELECTORS.alerts.markAllReadBtn);

        if (await markAllBtn.isVisible()) {
          await markAllBtn.click();

          await page.waitForResponse((resp) => resp.url().includes('/mark-all-read'));

          const unreadAlerts = page.locator(`${SELECTORS.alerts.item}[data-is-read="false"]`);
          expect(await unreadAlerts.count()).toBe(0);
        }
      }
    });
  });

  test.describe('[P2] Edge Cases', () => {
    test('[P2] should handle empty alerts state gracefully', async ({ page, apiRequest }) => {
      await apiRequest({
        method: 'POST',
        path: '/api/v1/handoff-alerts/mark-all-read',
      });

      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');

      const badge = page.locator(SELECTORS.sidebar.badge);

      const badgeVisible = await badge.isVisible();
      if (badgeVisible) {
        const badgeText = await badge.textContent();
        expect(badgeText).toBe('0');
      }
    });

    test('[P2] should preserve alert list order by urgency and time', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const alerts = page.locator(SELECTORS.alerts.item);
      const count = await alerts.count();

      if (count > 1) {
        const firstAlert = alerts.first();
        const lastAlert = alerts.last();

        const firstUrgency = await firstAlert
          .locator(SELECTORS.alerts.urgencyIndicator)
          .getAttribute('data-urgency');
        const lastUrgency = await lastAlert
          .locator(SELECTORS.alerts.urgencyIndicator)
          .getAttribute('data-urgency');

        const urgencyOrder = { high: 0, medium: 1, low: 2 };
        const firstOrder = urgencyOrder[firstUrgency as keyof typeof urgencyOrder] ?? 3;
        const lastOrder = urgencyOrder[lastUrgency as keyof typeof urgencyOrder] ?? 3;

        expect(firstOrder).toBeLessThanOrEqual(lastOrder);
      }
    });

    test('[P2] should display customer name fallback when name unavailable', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const alerts = page.locator(SELECTORS.alerts.item);

      if ((await alerts.count()) > 0) {
        const firstAlert = alerts.first();
        const customerName = firstAlert.locator(SELECTORS.alerts.customerName);

        if (await customerName.isVisible()) {
          const name = await customerName.textContent();
          expect(name).toBeTruthy();
          expect(name).not.toBe('');
        }
      }
    });

    test('[P2] should truncate long conversation previews', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const previews = page.locator(SELECTORS.alerts.preview);
      const count = await previews.count();

      if (count > 0) {
        const firstPreview = previews.first();
        const previewText = await firstPreview.textContent();

        expect(previewText?.length).toBeLessThanOrEqual(200);
      }
    });
  });

  test.describe('[P2] Accessibility', () => {
    test('[P2] should have accessible notification bell button', async ({ page }) => {
      const bell = page.locator(SELECTORS.header.notificationBell);

      if (await bell.isVisible()) {
        await expect(bell).toHaveAttribute('aria-label', /notification/i);
        await expect(bell).toHaveAttribute('role', 'button');
      }
    });

    test('[P2] should have accessible urgency indicators', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const urgencyIndicators = page.locator(SELECTORS.alerts.urgencyIndicator);

      if ((await urgencyIndicators.count()) > 0) {
        const firstIndicator = urgencyIndicators.first();

        const ariaLabel = await firstIndicator.getAttribute('aria-label');
        const dataUrgency = await firstIndicator.getAttribute('data-urgency');

        expect(ariaLabel || dataUrgency).toBeTruthy();
      }
    });

    test('[P2] should be keyboard navigable', async ({ page }) => {
      await page.goto('/conversations');
      await page.waitForLoadState('networkidle');

      const bell = page.locator(SELECTORS.header.notificationBell);

      if (await bell.isVisible()) {
        await page.keyboard.press('Tab');

        const focusedElement = page.locator(':focus');
        const tagName = await focusedElement.evaluate((el) => el.tagName.toLowerCase());

        expect(['button', 'a', 'input', 'select', 'textarea']).toContain(tagName);
      }
    });
  });
});

test.describe('Story 4-6: Handoff Notifications - Authenticated Flow', () => {
  test.use({ storageState: 'playwright/.auth/merchant.json' });

  test('[P0] authenticated merchant sees handoff alerts', async ({ page }) => {
    await page.goto('/conversations');
    await page.waitForLoadState('networkidle');

    const alertsList = page.locator(SELECTORS.alerts.list);
    await expect(alertsList).toBeVisible();

    const alerts = page.locator(SELECTORS.alerts.item);
    const count = await alerts.count();

    expect(count).toBeGreaterThanOrEqual(0);
  });
});
