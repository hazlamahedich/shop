/**
 * E2E Test: Knowledge Base Delete Flow
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests document deletion functionality
 *
 * @tags e2e knowledge-base story-8-8 delete
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks, createMockDocument } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe.serial('Story 8-8: Delete Flow @knowledge-base @story-8-8', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-E2E-010][P0] @smoke should delete document with confirmation (AC3)', async ({ page }) => {
    const documents = [createMockDocument({ id: 1, filename: 'test.pdf' })];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);

    await expect(po.dialog()).toBeVisible({ timeout: 5000 });

    const deleteResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/knowledge-base/1') && resp.request().method() === 'DELETE'
    );

    await po.dialogDeleteButton().click();

    const response = await deleteResponse;
    expect(response.status()).toBe(200);

    await expect(po.toast()).toContainText(/deleted|removed|success/i);
  });

  test('[8.8-E2E-011][P1] should cancel delete operation', async ({ page }) => {
    const documents = [createMockDocument({ id: 1, filename: 'test.pdf' })];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);
    await expect(po.dialog()).toBeVisible();

    await po.dialogCancelButton().click();

    await expect(po.dialog()).not.toBeVisible();
    await expect(po.documentRow(1)).toBeVisible();
  });
});
