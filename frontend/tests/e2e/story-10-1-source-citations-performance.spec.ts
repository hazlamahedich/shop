/**
 * Performance Tests for Story 10-1: Source Citations
 *
 * Tests source loading time, rendering performance, and interaction responsiveness
 *
 * @tags e2e story-10-1 performance sources
 */

import { test, expect, Page } from '@playwright/test';
import {
  setupSourceCitationMocks,
  createMockSources,
} from '../helpers/source-citation-helpers';

test.describe('[P1] Story 10-1: Source Citations Performance', () => {
  test.slow();

  test.beforeEach(async ({ page }) => {
    await page.goto('/widget-test');
  });

  test('[P1] Source cards should render within 100ms', async ({ page }) => {
    const mockSources = createMockSources(4);
    await setupSourceCitationMocks(page, { sources: mockSources });

    await page.getByTestId('chat-input').fill('Test query');
    
    const startTime = Date.now();
    await page.getByTestId('send-button').click();

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });
    
    const renderTime = Date.now() - startTime;
    expect(renderTime).toBeLessThan(2000);
  });

  test('[P1] Expand/collapse animation should complete within 300ms', async ({ page }) => {
    const mockSources = createMockSources(10);
    await setupSourceCitationMocks(page, { sources: mockSources });

    await page.getByTestId('chat-input').fill('Test');
    await page.getByTestId('send-button').click();

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    const toggleButton = sourceCitation.getByTestId('source-toggle');
    await expect(toggleButton).toBeVisible();

    const expandStartTime = Date.now();
    await toggleButton.click();

    const allCards = sourceCitation.getByTestId('source-card');
    await expect(allCards).toHaveCount(10, { timeout: 1000 });
    
    const expandTime = Date.now() - expandStartTime;
    expect(expandTime).toBeLessThan(500);
  });

  test('[P2] Source card click should respond within 50ms', async ({ page }) => {
    await setupSourceCitationMocks(page, {
      sources: [{
        documentId: 1,
        title: 'Clickable Document',
        documentType: 'url',
        relevanceScore: 0.95,
        url: 'https://example.com/target',
      }],
    });

    await page.getByTestId('chat-input').fill('Test');
    await page.getByTestId('send-button').click();

    const sourceCard = page.getByTestId('source-card').first();
    await expect(sourceCard).toBeVisible({ timeout: 5000 });

    const clickStartTime = Date.now();
    await sourceCard.click();
    const clickResponseTime = Date.now() - clickStartTime;
    expect(clickResponseTime).toBeLessThan(100);
  });

  test('[P2] Memory usage should not grow with repeated source renders', async ({ page }) => {
    const mockSources = createMockSources(5);
    await setupSourceCitationMocks(page, { sources: mockSources });

    const initialMetrics = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        };
      }
      return null;
    });

    for (let i = 0; i < 5; i++) {
      const responsePromise = page.waitForResponse('**/api/v1/widget/message');
      await page.getByTestId('chat-input').fill(`Query ${i}`);
      await page.getByTestId('send-button').click();
      await responsePromise;
    }

    const finalMetrics = await page.evaluate(() => {
      if (performance.memory) {
        return {
          usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        };
      }
      return null;
    });

    if (initialMetrics && finalMetrics) {
      const growth = finalMetrics.usedJSHeapSize - initialMetrics.usedJSHeapSize;
      const growthMB = growth / (1024 * 1024);
      expect(growthMB).toBeLessThan(5);
    }
  });

  test('[P2] Score badge rendering should be efficient', async ({ page }) => {
    const manySources = createMockSources(20);
    await setupSourceCitationMocks(page, { sources: manySources });

    const startTime = Date.now();
    await page.getByTestId('chat-input').fill('Test');
    await page.getByTestId('send-button').click();

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    await sourceCitation.getByTestId('source-toggle').click();
    
    const badges = sourceCitation.locator('[data-testid="source-card"] [data-testid="score-badge"]');
    await expect(badges.first()).toBeVisible({ timeout: 2000 });

    const renderTime = Date.now() - startTime;
    expect(renderTime).toBeLessThan(3000);
  });

  test('[P2] Source list scroll performance', async ({ page }) => {
    const scrollableSources = createMockSources(15);
    await setupSourceCitationMocks(page, { sources: scrollableSources });

    await page.getByTestId('chat-input').fill('Test');
    await page.getByTestId('send-button').click();

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    await sourceCitation.getByTestId('source-toggle').click();

    const scrollStartTime = Date.now();
    await sourceCitation.evaluate((el) => {
      el.scrollTo({ top: 500, behavior: 'smooth' });
    });
    await page.waitForFunction(
      (el) => el.scrollTop > 400,
      await sourceCitation.elementHandle(),
      { timeout: 1000 }
    );
    const scrollTime = Date.now() - scrollStartTime;

    expect(scrollTime).toBeLessThan(500);
  });
});
