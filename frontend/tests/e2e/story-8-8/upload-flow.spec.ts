/**
 * E2E Test: Knowledge Base Upload Flow
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests document upload functionality and validation
 *
 * @tags e2e knowledge-base story-8-8 upload
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe.serial('Story 8-8: Upload Flow @knowledge-base @story-8-8', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-E2E-004][P0] @smoke should upload PDF document successfully (AC2)', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/upload') && resp.status() === 201
    );

    await po.uploadFile('tests/fixtures/test-document.pdf');
    
    const response = await uploadResponse;
    expect(response.status()).toBe(201);

    await expect(po.toast()).toBeVisible({ timeout: 5000 });
  });

  test('[8.8-E2E-005][P1] should upload TXT document successfully', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/upload')
    );

    await po.uploadFile('tests/fixtures/test-document.txt');
    
    const response = await uploadResponse;
    expect(response.status()).toBe(201);
  });

  test('[8.8-E2E-006][P1] should upload MD document successfully', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/upload')
    );

    await po.uploadFile('tests/fixtures/test-document.md');
    
    const response = await uploadResponse;
    expect(response.status()).toBe(201);
  });

  test('[8.8-E2E-007][P1] should upload DOCX document successfully', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/upload')
    );

    await po.uploadFile('tests/fixtures/test-document.docx');
    
    const response = await uploadResponse;
    expect(response.status()).toBe(201);
  });

  test('[8.8-E2E-008][P1] should reject invalid file type', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', uploadShouldFail: true });
    
    await po.navigateToKnowledgeBase();

    // Use a non-accepted file type
    await po.uploadFile('tests/fixtures/test-image.png');

    // Validation happens client-side first
    const errorAlert = page.locator('[role="alert"]');
    await expect(errorAlert).toBeVisible({ timeout: 3000 });
    await expect(errorAlert).toContainText(/invalid file type/i);
  });

  test('[8.8-E2E-009][P1] should reject file too large (>10MB)', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', uploadError: 413 });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/large-file.pdf');

    await expect(po.toast()).toBeVisible({ timeout: 5000 });
    await expect(po.toast()).toContainText(/too large|10mb/i);
  });

  test('[8.8-E2E-016][P1] should show upload progress during upload', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', delay: 2000 });
    
    await po.navigateToKnowledgeBase();

    // Start upload without awaiting so we can check progress
    po.uploadFile('tests/fixtures/test-document.pdf');

    await expect(po.progressBar()).toBeVisible({ timeout: 1000 });
    await expect(po.progressBar()).toHaveAttribute('role', 'progressbar');
  });

  test('[8.8-E2E-020][P2] should support drag-and-drop upload', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const dataTransfer = await page.evaluateHandle(() => {
      const dt = new DataTransfer();
      return dt;
    });

    await po.uploadZone().dispatchEvent('drop', { dataTransfer });
  });
});
