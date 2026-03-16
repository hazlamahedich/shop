/**
 * E2E Test: Knowledge Base Navigation and Display
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests navigation, mode visibility, and document list display
 *
 * @tags e2e knowledge-base story-8-8 general-mode
 */

import { test, expect } from '@playwright/test';
import { setupKnowledgeBaseMocks, createMockDocument } from '../../helpers/knowledge-base-mocks';
import { KnowledgeBasePO } from '../../helpers/knowledge-base-po';

test.describe.serial('Story 8-8: Navigation and Display @knowledge-base @story-8-8', () => {
  let po: KnowledgeBasePO;

  test.beforeEach(async ({ page }) => {
    po = new KnowledgeBasePO(page);
  });

  test('[8.8-E2E-001][P0] @smoke should display Knowledge Base page in General mode', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general' });
    
    await po.navigateToKnowledgeBase();

    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible({ timeout: 5000 });
    await expect(po.uploadZone()).toBeVisible();
  });

  test('[8.8-E2E-002][P1] should NOT display Knowledge Base in E-commerce mode', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'ecommerce' });
    
    // We expect 404 or redirection or component not rendering
    await page.goto('/knowledge-base');
    
    // Check if the page title h1 contains "Knowledge Base"
    // Use exact match or h1 to avoid matching "Knowledge Base Unavailable" h2
    await expect(page.getByRole('heading', { level: 1, name: /^Knowledge Base$/ })).not.toBeVisible({ timeout: 5000 });
  });

  test('[8.8-E2E-003][P0] @smoke should display documents list with status (AC1)', async ({ page }) => {
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'product-catalog.pdf', 
        fileSize: 2048000, 
        status: 'ready',
        chunkCount: 15,
      }),
      createMockDocument({ 
        id: 2, 
        filename: 'faq.txt', 
        fileType: 'text/plain',
        fileSize: 51200, 
        status: 'processing',
        chunkCount: 0,
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await expect(po.documentList()).toBeVisible();
    await expect(po.documentRow(1)).toBeVisible();
    await expect(po.documentRow(2)).toBeVisible();
    
    await expect(po.statusBadge(1)).toContainText(/ready/i);
    await expect(po.statusBadge(2)).toContainText(/processing/i);
  });

  test('[8.8-E2E-015][P2] should show empty state when no documents', async ({ page }) => {
    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents: [] });
    
    await po.navigateToKnowledgeBase();

    await expect(po.emptyState()).toBeVisible({ timeout: 5000 });
    await expect(po.emptyState()).toContainText(/no documents/i);
  });

  test('[8.8-E2E-018][P1] should format file sizes correctly', async ({ page }) => {
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'small.txt', 
        fileType: 'text/plain',
        fileSize: 512, 
      }),
      createMockDocument({ 
        id: 2, 
        filename: 'medium.pdf', 
        fileSize: 1536000,
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    // Use flexible regex for whitespace
    await expect(po.documentRow(1)).toContainText(/512\s*B/i);
    await expect(po.documentRow(2)).toContainText(/1\.5\s*MB/i);
  });

  test('[8.8-E2E-019][P2] should show relative time for upload date', async ({ page }) => {
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000);
    const documents = [
      createMockDocument({ 
        id: 1, 
        filename: 'recent.pdf', 
        createdAt: twoHoursAgo.toISOString(),
        updatedAt: twoHoursAgo.toISOString(),
      }),
    ];

    await setupKnowledgeBaseMocks(page, { onboardingMode: 'general', documents });
    
    await po.navigateToKnowledgeBase();

    await expect(po.documentRow(1)).toContainText(/2 hours ago/i);
  });
});
