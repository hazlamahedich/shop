/**
 * E2E Test: Knowledge Base Status Indicators
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests document status display and retry functionality
 *
 * @tags e2e knowledge-base story-8-8 status
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks, createMockDocument } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe.serial('Story 8-8: Status Indicators @knowledge-base @story-8-8', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-E2E-012][P0] @smoke should show spinner for processing documents (AC4)', async ({ page }) => {
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'processing.pdf', 
        status: 'processing',
        chunkCount: 0,
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await expect(po.spinner(1)).toBeVisible({ timeout: 5000 });
    await expect(po.statusBadge(1)).toContainText(/processing/i);
  });

  test('[8.8-E2E-013][P0] @smoke should show error message with retry option (AC5)', async ({ page }) => {
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'error.pdf', 
        status: 'error',
        errorMessage: 'Failed to process document: Invalid PDF format',
        chunkCount: 0,
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await expect(po.statusBadge(1)).toContainText(/error/i);
    await expect(po.retryButton(1)).toBeVisible();
    
    await expect(po.documentRow(1)).toContainText(/invalid pdf format/i);
  });

  test('[8.8-E2E-014][P1] should retry failed document', async ({ page }) => {
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'error.pdf', 
        status: 'error',
        errorMessage: 'Processing failed',
        chunkCount: 0,
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    const reprocessResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/1/reprocess')
    );

    await po.retryButton(1).click();

    const response = await reprocessResponse;
    expect(response.status()).toBe(200);
  });
});
