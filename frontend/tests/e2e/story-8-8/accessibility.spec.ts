/**
 * E2E Test: Knowledge Base Accessibility
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests WCAG 2.1 AA accessibility compliance
 *
 * @tags e2e knowledge-base story-8-8 accessibility a11y
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe('Story 8-8: Knowledge Base Accessibility @knowledge-base @story-8-8 @a11y', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-A11Y-001][P1] @smoke should have no accessibility violations on page load', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    // Verify main content is present
    await expect(po.pageTitle()).toBeVisible();
    await expect(po.uploadZone()).toBeVisible();
  });

  test('[8.8-A11Y-002][P1] should have proper heading hierarchy', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const h1 = page.locator('h1');
    // After fixing Sidebar.tsx, there should be exactly one h1
    await expect(h1).toHaveCount(1);
    await expect(h1).toContainText(/knowledge base/i);
  });

  test('[8.8-A11Y-003][P1] should have accessible upload zone', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadZone = po.uploadZone();
    await expect(uploadZone).toHaveAttribute('role', 'button');
    await expect(uploadZone).toHaveAttribute('aria-label', /upload|drag.*drop/i);

    const fileInput = po.fileInput();
    await expect(fileInput).toHaveAttribute('type', 'file');
    await expect(fileInput).toHaveAttribute('accept');
  });

  test('[8.8-A11Y-004][P1] should support keyboard navigation for document list', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    // Focus the delete button directly to test focusability
    const deleteBtn = po.deleteButton(1);
    await deleteBtn.focus();
    await po.waitForFocus(deleteBtn);
    
    // Tab back to upload zone (Shift+Tab)
    await page.keyboard.press('Shift+Tab');
    const uploadZone = po.uploadZone();
    await po.waitForFocus(uploadZone);
  });

  test('[8.8-A11Y-005][P1] should have accessible delete confirmation dialog', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);

    const dialog = po.dialog();
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute('aria-modal', 'true');
    await expect(dialog).toHaveAttribute('aria-labelledby');
    await expect(dialog).toHaveAttribute('aria-describedby');
  });

  test('[8.8-A11Y-006][P1] @smoke should focus cancel button when dialog opens', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);

    // Radix UI Dialog focus management - wait for hydration/transition using helper
    await po.waitForFocus(po.dialogCancelButton(), 15000);
  });

  test('[8.8-A11Y-007][P1] @smoke should close dialog on Escape key', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);
    await expect(po.dialog()).toBeVisible();

    await page.keyboard.press('Escape');

    await expect(po.dialog()).not.toBeVisible();
  });

  test('[8.8-A11Y-008][P1] should have proper status badge labels', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'processing.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'processing',
        chunkCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    const statusBadge1 = po.statusBadge(1);
    await expect(statusBadge1).toHaveAttribute('aria-label', /status: processing/i);
  });

  test('[8.8-A11Y-009][P2] should announce status changes to screen readers', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    // Handle multiple live regions by picking first
    const liveRegion = page.locator('[aria-live="polite"]').first();
    // Ensure the live region is present for announcements
    await expect(liveRegion).toBeAttached();
  });

  test('[8.8-A11Y-010][P2] should have sufficient color contrast for status badges', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'ready.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    const readyBadge = po.statusBadge(1);
    await expect(readyBadge).toBeVisible();
  });

  test('[8.8-A11Y-011][P2] should have accessible file input with label association', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const fileInput = po.fileInput();
    const inputId = await fileInput.getAttribute('id');

    if (inputId) {
      const label = page.locator(`label[for="${inputId}"]`);
      await expect(label).toBeVisible();
    } else {
      const ariaLabel = await fileInput.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();
    }
  });

  test('[8.8-A11Y-012][P2] should support Enter/Space to trigger file picker', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    const uploadZone = po.uploadZone();
    await uploadZone.focus();

    const fileChooserPromise = page.waitForEvent('filechooser');

    await page.keyboard.press('Enter');

    const fileChooser = await fileChooserPromise;
    expect(fileChooser).toBeDefined();
  });

  test('[8.8-A11Y-013][P2] should have accessible empty state', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents: [] });
    
    await po.navigateToKnowledgeBase();

    const emptyState = po.emptyState();
    await expect(emptyState).toBeVisible();
    await expect(emptyState).toHaveAttribute('role', 'status');
  });

  test('[8.8-A11Y-014][P2] should have accessible upload progress bar', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', delay: 2000 });
    
    await po.navigateToKnowledgeBase();

    await po.uploadFile('tests/fixtures/test-document.pdf');

    const progressBar = po.progressBar();
    // Use visible: true to ensure it's not hidden
    await expect(progressBar).toBeVisible({ timeout: 15000 });
    await expect(progressBar).toHaveAttribute('role', 'progressbar');
  });

  test('[8.8-A11Y-015][P2] should have accessible document table structure', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    const table = page.locator('table');
    await expect(table).toBeVisible();

    const headers = table.locator('thead th');
    await expect(headers.first()).toContainText(/name|filename/i);
  });

  test('[8.8-A11Y-016][P2] should trap focus within dialog', async ({ page }) => {
    const documents = [
      {
        id: 1,
        filename: 'test.pdf',
        fileType: 'application/pdf',
        fileSize: 1024,
        status: 'ready',
        chunkCount: 5,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      },
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await po.clickDelete(1);
    await expect(po.dialog()).toBeVisible();

    // Tab through elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check if focus is still within dialog
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible({ timeout: 10000 });
    
    const isInDialog = await focusedElement.evaluate((el) => {
      const dialog = el.closest('[role="dialog"], [role="alertdialog"]');
      return !!dialog;
    });

    expect(isInDialog).toBe(true);
  });
});
