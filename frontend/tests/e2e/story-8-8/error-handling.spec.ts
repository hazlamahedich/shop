/**
 * E2E Test: Knowledge Base Error Handling
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests comprehensive error scenarios
 *
 * @tags e2e knowledge-base story-8-8 error-handling
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks, createMockDocument } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe('Story 8-8: Knowledge Base Error Handling @knowledge-base @story-8-8 @errors', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-ERR-001][P1] should handle network error during document list fetch', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', networkError: true });
    
    await po.navigateToKnowledgeBase();

    // Use a locator that specifically targets the toast message to avoid ambiguity
    const toast = page.locator('[role="alert"]').filter({ hasText: /error|failed|network/i }).first();
    await expect(toast).toBeVisible({ timeout: 15000 });
  });

  test('[8.8-ERR-002][P1] should handle 500 server error during list fetch', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', serverError: true });
    
    await po.navigateToKnowledgeBase();

    const toast = page.locator('[role="alert"]').filter({ hasText: /error|failed/i }).first();
    await expect(toast).toBeVisible({ timeout: 15000 });
  });

  test('[8.8-ERR-003][P1] should handle 400 upload error', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', uploadError: 400 });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const toast = page.locator('[role="alert"]').filter({ hasText: /invalid|failed/i }).first();
    await expect(toast).toBeVisible({ timeout: 10000 });
  });

  test('[8.8-ERR-004][P1] should handle 413 file too large error', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', uploadError: 413 });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const toast = page.locator('[role="alert"]').filter({ hasText: /too large|10mb/i }).first();
    await expect(toast).toBeVisible({ timeout: 10000 });
  });

  test('[8.8-ERR-005][P1] should handle 500 upload error', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', uploadError: 500 });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const toast = page.locator('[role="alert"]').filter({ hasText: /error|failed|try again/i }).first();
    await expect(toast).toBeVisible({ timeout: 10000 });
  });

  test('[8.8-ERR-006][P1] should handle 404 delete error', async ({ page }) => {
    const documents = [createMockDocument({ id: 1, filename: 'test.pdf' })];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents, deleteError: 404 });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);
    await po.dialogDeleteButton().click({ force: true });

    const toast = page.locator('[role="alert"]').filter({ hasText: /404|not found/i }).first();
    await expect(toast).toBeVisible({ timeout: 10000 });
  });

  test('[8.8-ERR-007][P1] should handle 500 delete error', async ({ page }) => {
    const documents = [createMockDocument({ id: 1, filename: 'test.pdf' })];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents, deleteError: 500 });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);
    await po.dialogDeleteButton().click({ force: true });

    const toast = page.locator('[role="alert"]').filter({ hasText: /error|failed/i }).first();
    await expect(toast).toBeVisible({ timeout: 10000 });
  });

  test('[8.8-ERR-008][P2] should show document with error status and retry option', async ({ page }) => {
    const documents = [
      createMockDocument({
        id: 1,
        filename: 'failed.pdf',
        status: 'error',
        errorMessage: 'Processing failed: Invalid PDF format',
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await expect(po.statusBadge(1)).toContainText(/error/i);
    await expect(po.documentRow(1)).toContainText(/invalid pdf format/i);
    await expect(po.retryButton(1)).toBeVisible();
  });

  test('[8.8-ERR-009][P2] should allow retry after failed processing', async ({ page }) => {
    const documents = [
      createMockDocument({
        id: 1,
        filename: 'failed.pdf',
        status: 'error',
        errorMessage: 'Processing failed',
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    const retryResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/1/reprocess')
    );

    await po.clickRetry(1);

    const response = await retryResponse;
    expect(response.status()).toBe(200);
  });

  test('[8.8-ERR-010][P2] should preserve document list on upload error', async ({ page }) => {
    const documents = [createMockDocument({ id: 1, filename: 'existing.pdf' })];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents, uploadError: 400 });
    
    await po.navigateToKnowledgeBase();

    await expect(po.documentRow(1)).toBeVisible();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const toast = page.locator('[role="alert"]').first();
    await expect(toast).toBeVisible({ timeout: 10000 });
    await expect(po.documentRow(1)).toBeVisible();
  });

  test('[8.8-ERR-011][P2] should handle malformed API response gracefully', async ({ page }) => {
    // Setup mocks first
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    // Override the GET documents route specifically
    await page.route('**/api/knowledge-base', async (route) => {
      if (route.request().method() === 'GET' && !route.request().url().includes('/status')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: 'invalid-json-response',
        });
      } else {
        await route.continue();
      }
    }, { times: 1 }); // Only override the first call

    await po.navigateToKnowledgeBase();

    // Any error during fetch should trigger a toast
    const toast = page.locator('[role="alert"]').first();
    await expect(toast).toBeVisible({ timeout: 15000 });
  });

  test('[8.8-ERR-012][P2] should handle timeout during upload', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    // Specifically override upload to timeout
    await page.route('**/api/knowledge-base/upload', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 35000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: {} }),
      });
    });

    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const toast = page.locator('[role="alert"]').first();
    await expect(toast).toBeVisible({ timeout: 45000 });
  });
});
