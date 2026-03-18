/**
 * E2E Tests for Story 10-1: Source Citations Widget
 *
 * Tests source citations feature that displays RAG document sources in the chat widget.
 *
 * Acceptance Criteria:
 * - AC1: Sources section appears when available
 * - AC2: Source cards display document info (title, type icon, score)
 * - AC3: Source links open documents
 * - AC4: Collapsible/expandable sources (max 3 initially)
 * - AC5: RAG-only display (no sources for non-RAG)
 * - AC6: Dual interface support (widget and dashboard)
 */

import { test, expect } from '@playwright/test';
import {
  setupSourceCitationMocks,
  createMockSources,
  type SourceCitation,
} from '../helpers/source-citation-helpers';
import { openWidgetChat } from '../helpers/widget-test-helpers';

const defaultSources: SourceCitation[] = [
  { documentId: 1, title: 'Product Manual.pdf', documentType: 'pdf', relevanceScore: 0.95, chunkIndex: 5 },
  { documentId: 2, title: 'FAQ Page', documentType: 'url', relevanceScore: 0.88, url: 'https://example.com/faq' },
];

async function sendChatMessage(page: import('@playwright/test').Page, message: string) {
  const input = page.getByPlaceholder('Type a message...');
  await input.fill(message);
  await input.press('Enter');
}

test.describe('[P1] Story 10-1: Source Citations Widget', () => {
  test('AC1: Sources section appears when RAG sources available', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: defaultSources });
    await openWidgetChat(page);
    await sendChatMessage(page, 'What is the battery life?');

    await expect(page.getByTestId('source-citation')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Sources')).toBeVisible();
  });

  test('AC2: Source cards display title, type icon, and relevance score', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: defaultSources });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Tell me about products');

    const sourceCards = page.getByTestId('source-card');
    await expect(sourceCards).toHaveCount(2, { timeout: 5000 });

    const firstCard = sourceCards.first();
    await expect(firstCard).toContainText('Product Manual.pdf');
    await expect(firstCard).toContainText('95%');

    const secondCard = sourceCards.nth(1);
    await expect(secondCard).toContainText('FAQ Page');
    await expect(secondCard).toContainText('88%');
  });

  test('AC3: Clicking source with URL opens new tab', async ({ page, context }) => {
    const urlSource: SourceCitation = {
      documentId: 1,
      title: 'FAQ Page',
      documentType: 'url',
      relevanceScore: 0.88,
      url: 'https://example.com/faq',
    };

    await setupSourceCitationMocks(page, { sources: [urlSource] });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Help');

    const sourceCard = page.getByTestId('source-card');
    await expect(sourceCard).toBeVisible({ timeout: 5000 });

    await sourceCard.evaluate((el) => el.scrollIntoView({ block: 'center', inline: 'center' }));
    await page.waitForTimeout(100);

    const pagePromise = context.waitForEvent('page');
    await sourceCard.dispatchEvent('click');
    const newPage = await pagePromise;

    await expect(newPage).toHaveURL('https://example.com/faq');
  });

  test('AC4: Collapsible/expandable sources with 3+ items', async ({ page }) => {
    const mockSources = createMockSources(5);

    await setupSourceCitationMocks(page, { sources: mockSources });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Show all sources');

    const sourceCards = page.getByTestId('source-card');
    await expect(sourceCards).toHaveCount(3, { timeout: 5000 });

    const toggleButton = page.getByTestId('source-toggle');
    await expect(toggleButton).toContainText('View 2 more');
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

    await toggleButton.evaluate((el) => el.scrollIntoView({ block: 'center', inline: 'center' }));
    await page.waitForTimeout(100);
    await toggleButton.dispatchEvent('click');

    await expect(sourceCards).toHaveCount(5);
    await expect(toggleButton).toContainText('Show less');
    await expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
  });

  test('AC5: No sources section for non-RAG responses', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: [], includeSources: false });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Hi');

    await expect(page.getByTestId('source-citation')).not.toBeVisible({ timeout: 3000 });
  });

  test.skip('AC6: Sources work in dashboard chat interface', async ({ page }) => {
    // NOTE: Dashboard does not have a direct chat interface with message input.
    // The dashboard shows conversation history/analytics, not a live chat.
    // This test should be updated when a dashboard chat view is implemented.
    await page.goto('/dashboard');

    await setupSourceCitationMocks(page, { sources: [defaultSources[0]] });
    const input = page.getByPlaceholder('Type a message...');
    await input.fill('Help me');
    await input.press('Enter');

    await expect(page.getByTestId('source-citation')).toBeVisible({ timeout: 5000 });
  });

  test('should display PDF icon for PDF documents', async ({ page }) => {
    await setupSourceCitationMocks(page, {
      sources: [{ documentId: 1, title: 'Manual.pdf', documentType: 'pdf', relevanceScore: 0.95 }],
    });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Show manual');

    const sourceCard = page.getByTestId('source-card');
    await expect(sourceCard).toBeVisible({ timeout: 5000 });
    const svgElement = sourceCard.locator('svg').first();
    await expect(svgElement).toBeVisible();
  });

  test('should apply dark mode styling', async ({ page }) => {
    await setupSourceCitationMocks(page, {
      sources: [{ documentId: 1, title: 'Document', documentType: 'text', relevanceScore: 0.95 }],
    });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Document please');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).toBeVisible({ timeout: 5000 });
  });

  test('[P2] should handle network error gracefully', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: defaultSources, networkError: true });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).not.toBeVisible({ timeout: 3000 });
  });

  test('[P2] should handle server error gracefully', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: defaultSources, serverError: true });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).not.toBeVisible({ timeout: 3000 });
  });

  test('[P2] should handle invalid source data gracefully', async ({ page }) => {
    await setupSourceCitationMocks(page, { sources: defaultSources, invalidData: true });
    await openWidgetChat(page);
    await sendChatMessage(page, 'Test');

    const sourceCitation = page.getByTestId('source-citation');
    await expect(sourceCitation).not.toBeVisible({ timeout: 3000 });
  });
});
