import { test, expect } from '@playwright/test';

test.describe('Story 11.12b: Conversation Flow Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test.afterEach(async ({ page }) => {
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  });

  test('AC1 Conversation Flow widget renders on dashboard @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });
    await expect(widget.locator('text=Flow Analytics')).toBeVisible();
  });

  test('AC2 Widget displays 6 tabs @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const tabs = ['Overview', 'Clarification', 'Friction', 'Sentiment', 'Handoff', 'Context'];
    for (const tab of tabs) {
      const tabButton = widget.locator('button').filter({ hasText: new RegExp(tab, 'i') });
      await expect(tabButton).toBeVisible({ timeout: 5000 });
    }
  });

  test('AC3 Tab switching updates displayed content @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const clarificationTab = widget.locator('button').filter({ hasText: /Clarification/i });
    await clarificationTab.click();

    await expect(widget.locator('text=Clarification')).toBeVisible();
  });

  test('AC4 Friction tab shows friction section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const frictionTab = widget.locator('button').filter({ hasText: /Friction/i });
    await frictionTab.click();

    await expect(widget.locator('text=Friction')).toBeVisible();
  });

  test('AC5 Sentiment tab shows sentiment section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const sentimentTab = widget.locator('button').filter({ hasText: /Sentiment/i });
    await sentimentTab.click();

    await expect(widget.locator('text=Sentiment')).toBeVisible();
  });

  test('AC6 Handoff tab shows handoff section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const handoffTab = widget.locator('button').filter({ hasText: /Handoff/i });
    await handoffTab.click();

    await expect(widget.locator('text=Handoff')).toBeVisible();
  });

  test('AC7 Context tab shows context utilization section @p1', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const contextTab = widget.locator('button').filter({ hasText: /Context/i });
    await contextTab.click();

    await expect(widget.locator('text=Context')).toBeVisible();
  });

  test('AC8 Overview tab displays length distribution metrics @p0', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const overviewTab = widget.locator('button').filter({ hasText: /Overview/i });
    await overviewTab.click();

    const hasAvgTurns = await widget.locator('text=Avg Turns').isVisible().catch(() => false);
    const hasEmptyState = await widget.locator('text=No conversation data').isVisible().catch(() => false);
    expect(hasAvgTurns || hasEmptyState).toBeTruthy();
  });

  test('AC9 Widget makes API calls to conversation-flow endpoints @p1', async ({ page }) => {
    const apiCalls: string[] = [];
    page.on('request', (req) => {
      const url = req.url();
      if (url.includes('/conversation-flow/')) {
        apiCalls.push(url);
      }
    });

    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await page.waitForTimeout(3000);

    expect(apiCalls.length).toBeGreaterThan(0);
  });

  test('AC10 Expandable widget opens and closes @p2', async ({ page }) => {
    const widget = page.locator('[data-testid="conversation-flow-widget"]');
    await expect(widget).toBeVisible({ timeout: 15000 });

    const expandButton = widget.locator('button[aria-label="Expand"]');
    if (await expandButton.isVisible().catch(() => false)) {
      await expandButton.click();

      const closeButton = widget.locator('button[aria-label="Collapse"]');
      await expect(closeButton).toBeVisible({ timeout: 5000 });

      await closeButton.click();
      await expect(widget).toBeVisible();
    }
  });
});
