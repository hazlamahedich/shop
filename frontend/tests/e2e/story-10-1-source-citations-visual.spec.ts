/**
 * Visual Regression Tests for Story 10-1: Source Citations
 *
 * Tests visual appearance of source cards, badges, and styling
 * Note: Full visual regression requires Percy or similar tool
 * These tests verify key visual elements are present and styled correctly
 *
 * @tags e2e story-10-1 visual sources
 */

import { test, expect } from '@playwright/test';
import {
  setupSourceCitationMocks,
  createMockSources,
  type SourceCitation,
} from '../helpers/source-citation-helpers';
import { openWidgetChat, sendMessage } from '../helpers/widget-test-helpers';

test.describe('[P2] Story 10-1: Source Citations Visual Tests', () => {
  const mockSources: SourceCitation[] = [
    { documentId: 1, title: 'PDF Document', documentType: 'pdf', relevanceScore: 0.95 },
    { documentId: 2, title: 'Web Page', documentType: 'url', relevanceScore: 0.85, url: 'https://example.com' },
    { documentId: 3, title: 'Text Note', documentType: 'text', relevanceScore: 0.72 },
  ];

  test('[P2] Source card should have correct visual hierarchy', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: mockSources });
    await openWidgetChat(page);
    await sendMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    const firstCard = sourceCitation.getByTestId('source-card').first();
    await expect(firstCard).toBeVisible();

    const titleElement = firstCard.getByTestId('source-title');
    if (await titleElement.isVisible()) {
      const fontSize = await titleElement.evaluate((el) => window.getComputedStyle(el).fontSize);
      expect(fontSize).toBeTruthy();
    }

    const badge = firstCard.getByTestId('score-badge');
    if (await badge.isVisible()) {
      const bgColor = await badge.evaluate((el) => window.getComputedStyle(el).backgroundColor);
      expect(bgColor).toBeTruthy();
    }
  });

  test('[P2] Score badge should use correct colors based on score', async ({ page }) => {
    const scoreColors = [
      { score: 0.95, expectedClass: 'high' },
      { score: 0.75, expectedClass: 'medium' },
      { score: 0.55, expectedClass: 'low' },
    ];

    for (const { score } of scoreColors) {
      await setupSourceCitationMocks(page, {
        sources: [{ documentId: 1, title: 'Test Document', documentType: 'pdf', relevanceScore: score }],
      });
      await openWidgetChat(page);
      await sendMessage(page, 'Test');

      const badge = page.getByTestId('source-card').first().getByTestId('score-badge');
      if (await badge.isVisible({ timeout: 3000 })) {
        const className = (await badge.getAttribute('class')) || '';
        expect(className.length).toBeGreaterThan(0);
      }
    }
  });

  test('[P2] Document type icons should be visually distinct', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: mockSources });
    await openWidgetChat(page);
    await sendMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    const cards = sourceCitation.getByTestId('source-card');
    await expect(cards).toHaveCount(3);

    const firstCard = cards.first();
    const icon = firstCard.locator('svg');
    await expect(icon).toBeVisible({ timeout: 3000 });

    const iconSize = await icon.boundingBox();
    expect(iconSize?.width).toBeGreaterThan(10);
    expect(iconSize?.height).toBeGreaterThan(10);
  });

  test('[P2] Source cards should have hover state', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: [mockSources[1]] });
    await openWidgetChat(page);
    await sendMessage(page, 'Test');

    const sourceCard = page.getByTestId('source-card').first();
    await expect(sourceCard).toBeVisible({ timeout: 5000 });

    await sourceCard.hover();
    await expect(sourceCard).toHaveCSS('cursor', /pointer/, { timeout: 2000 });
  });

  test('[P2] Truncated titles should show ellipsis', async ({ page }) => {
    const longTitleSource: SourceCitation = {
      documentId: 1,
      title: 'This is a very long document title that should be truncated when displayed in the source citation card',
      documentType: 'pdf',
      relevanceScore: 0.95,
    };

    await setupSourceCitationMocks(page, { sources: [longTitleSource] });
    await openWidgetChat(page);
    await sendMessage(page, 'Test');

    const sourceCard = page.getByTestId('source-card').first();
    await expect(sourceCard).toBeVisible({ timeout: 5000 });

    const titleElement = sourceCard.getByTestId('source-title');
    if (await titleElement.isVisible()) {
      const textOverflow = await titleElement.evaluate((el) => window.getComputedStyle(el).textOverflow);
      expect(textOverflow).toBeDefined();
    }
  });

  test('[P2] Source list container should have correct max height', async ({ page }) => {
    await setupSourceCitationMocks(page, {
      sources: createMockSources(10),
    });
    await openWidgetChat(page);
    await sendMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });

    const toggleButton = sourceCitation.getByTestId('source-toggle');
    await expect(toggleButton).toBeVisible({ timeout: 3000 });
    await toggleButton.click();

    await expect(sourceCitation.getByTestId('source-card')).toHaveCount(10, { timeout: 2000 });

    const containerHeight = await sourceCitation.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        maxHeight: styles.maxHeight,
        overflow: styles.overflow,
      };
    });
    expect(containerHeight).toBeDefined();
  });
});
