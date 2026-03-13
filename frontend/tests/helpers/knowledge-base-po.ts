
import { Page, expect } from '@playwright/test';

export class KnowledgeBasePO {
  constructor(private page: Page) {}

  readonly uploadZone = () => this.page.locator('[data-testid="upload-zone"]');
  readonly fileInput = () => this.page.locator('input[type="file"]');
  readonly documentList = () => this.page.locator('[data-testid="document-list"]');
  readonly deleteButton = (id: number) => this.page.locator(`[data-testid="delete-document-${id}"]`);
  
  async clickDelete(id: number) {
    // Story 8-8: Use force click to avoid interception by table cell paddings/divs
    await this.deleteButton(id).click({ force: true });
  }

  async deleteDocument(id: number) {
    await this.clickDelete(id);
    await expect(this.dialog()).toBeVisible();
    await this.dialogDeleteButton().click({ force: true });
  }
  readonly retryButton = (id: number) => this.page.locator(`[data-testid="retry-document-${id}"]`);
  
  async clickRetry(id: number) {
    await this.retryButton(id).click({ force: true });
  }
  readonly documentRow = (id: number) => this.page.locator(`[data-testid="document-row-${id}"]`);
  readonly statusBadge = (id: number) => this.page.locator(`[data-testid="status-badge-${id}"]`);
  readonly spinner = (id: number) => this.page.locator(`[data-testid="spinner-${id}"]`);
  readonly toast = () => this.page.locator('[role="alert"]');
  readonly progressBar = () => this.page.locator('[role="progressbar"]');
  readonly dialog = () => this.page.locator('[role="dialog"], [role="alertdialog"]');
  readonly dialogCancelButton = () => this.dialog().getByRole('button', { name: /cancel/i });
  readonly dialogDeleteButton = () => this.dialog().getByRole('button', { name: /delete/i });
  readonly emptyState = () => this.page.locator('[data-testid="empty-state"]');
  readonly pageTitle = () => this.page.getByRole('heading', { level: 1, name: /^Knowledge Base$/ });

  async navigateToKnowledgeBase() {
    await this.page.goto('/knowledge-base', { timeout: 60000 });
    // Ensure we wait for the page to be ready and hydrated
    await expect(this.pageTitle()).toBeVisible({ timeout: 10000 });
  }

  async uploadFile(filePath: string) {
    await this.fileInput().setInputFiles(filePath);
  }

  async waitForFocus(locator: any, timeout = 15000) {
    // Story 8-8: Robust focus waiter using page context evaluation
    await expect(async () => {
      // Check if focused using Playwright's built-in check
      const isFocused = await locator.evaluate((el: HTMLElement) => document.activeElement === el);
      expect(isFocused).toBe(true);
    }).toPass({ timeout });
  }
}
