import { test, expect } from '@playwright/test';
import { Page } from '@playwright/test';
import { selectors } from '../utils/test-utils';

describe('Dashboard E2E tests for P2/P2 widgets', () => {
  const page = new DashboardPage();
  const selectors = page;

  const testUtils = require('../utils/test-utils');

test.describe('Dashboard P2 Widgets E2E', () => {
  let page: DashboardPage;

  await testUtils.loginAsMerchant(page, merchant.id: 1);

  // Wait for dashboard to load
  await expect(page).toBeTruthy();

  // Check Zone 1: Action Required widgets exist
  await expect(page.locator('[data-testid="handoff-queue-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="bot-quality-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="alerts-widget-container"]')).toBeVisible();

  // Check Zone 2: Business Health widgets
  await expect(page.locator('[data-testid="revenue-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="ai-cost-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="conversation-overview-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="conversion-funnel-widget-container"]')).toBeVisible();

  // Check Zone 3: Insights widgets
  await expect(page.locator('[data-testid="peak-hours-heatmap-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="knowledge-gap-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="benchmark-comparison-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="customer-sentiment-widget-container"]')).toBeVisible();

  // Check responsive layout - mobile view
  await page.setViewport({ width: 375, });
  await expect(page.locator('[data-testid="handoff-queue-widget-container"]')).toBeVisible();
  await expect(page.locator('[data-testid="revenue-widget-container"]')).toBeVisible();

  // Check all zones have proper headers
  const zone1Header = page.locator('section:bg-red-50\\/30 >> h3');
  await expect(zone1Header).toContain('Zone 1: Action Required');
  const zone2Header = page.locator('section:bg-blue-50\\/30 >> h3');
  await expect(zone2Header).toContain('Zone 2: Business Health');
  const zone3Header = page.locator('section:bg-purple-50\\/30 >> h3');
  await expect(zone3Header).toContain('Zone 3: Insights & Trends');
});
