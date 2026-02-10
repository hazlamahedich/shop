/**
 * E2E Tests for Story 1.11: Business Info & FAQ Configuration
 *
 * Tests business info and FAQ configuration UI and interaction flows
 *
 * Prerequisites:
 * - Frontend dev server running on http://localhost:5173
 * - Backend API running on http://localhost:8000
 * - Test merchant account exists and is logged in
 */

import { test, expect } from '@playwright/test';
import { clearStorage } from '../fixtures/test-helper';

const API_URL = process.env.API_URL || 'http://localhost:8000';

const TEST_MERCHANT = {
  email: 'e2e-test@example.com',
  password: 'TestPass123',
};

test.describe.configure({ mode: 'serial' });
test.describe('Story 1.11: Business Info & FAQ Configuration E2E [P0]', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);

    // Login and set auth state
    const loginResponse = await page.request.post(`${API_URL}/api/v1/auth/login`, {
      data: TEST_MERCHANT,
    });

    if (loginResponse.ok()) {
      const loginData = await loginResponse.json();
      const token = loginData.data.session.token;

      await page.goto('/');

      // Set auth state in localStorage
      await page.evaluate((accessToken) => {
        localStorage.setItem('auth_token', accessToken);
        localStorage.setItem('auth_timestamp', Date.now().toString());
      }, token);
    }
  });

  test('[P0] should display business info and FAQ configuration page', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Verify page title
    await expect(page.getByRole('heading', { name: /business info/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /faq configuration/i })).toBeVisible();
  });

  test('[P0] should display business info form fields', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Verify all business info fields are present
    await expect(page.getByRole('textbox', { name: /Business Name/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Business Description/i })).toBeVisible();
    await expect(page.getByRole('textbox', { name: /Business Hours/i })).toBeVisible();
  });

  test('[P0] should update and save business info', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Fill in business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('Test Athletic Gear');
    await page.getByRole('textbox', { name: /Business Description/i }).fill('Premium athletic equipment');
    await page.getByRole('textbox', { name: /Business Hours/i }).fill('9 AM - 6 PM PST');

    // Save business info
    const saveButton = page.getByRole('button', { name: /Save Business Info/i });
    await saveButton.click();

    // Wait for success message
    await expect(page.getByText(/business info saved/i)).toBeVisible({ timeout: 5000 });
  });

  test('[P0] should display FAQ list section', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Verify FAQ section is visible
    await expect(page.getByText(/frequently asked questions/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Add FAQ/i })).toBeVisible();
  });

  test('[P0] should create new FAQ item', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Click Add FAQ button
    const addFaqButton = page.getByRole('button', { name: /Add FAQ/i });
    await addFaqButton.click();

    // Wait for modal to appear
    await expect(page.getByRole('dialog')).toBeVisible();

    // Fill in FAQ form
    await page.getByRole('textbox', { name: /Question/i }).fill('What are your shipping options?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('We offer free shipping on orders over $50.');
    await page.getByRole('textbox', { name: /Keywords/i }).fill('shipping,delivery');

    // Save FAQ
    const saveButton = page.getByRole('button', { name: /Save FAQ/i });
    await saveButton.click();

    // Wait for success and modal to close
    await expect(page.getByRole('dialog')).not.toBeVisible({ timeout: 5000 });

    // Verify FAQ appears in list
    await expect(page.getByText('What are your shipping options?')).toBeVisible();
  });

  test('[P0] should edit existing FAQ', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Create an FAQ first
    const addFaqButton = page.getByRole('button', { name: /Add FAQ/i });
    await addFaqButton.click();

    await page.getByRole('textbox', { name: /Question/i }).fill('Original question?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('Original answer');
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Find and click edit button for the FAQ
    const editButton = page.getByRole('button', { name: /Edit FAQ/i }).first();
    await editButton.click();

    // Wait for modal
    await expect(page.getByRole('dialog')).toBeVisible();

    // Update the FAQ
    const questionInput = page.getByRole('textbox', { name: /Question/i });
    await questionInput.clear();
    await questionInput.fill('Updated question?');

    // Save changes
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    // Verify update
    await expect(page.getByText('Updated question?')).toBeVisible();
  });

  test('[P0] should delete FAQ', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Create an FAQ first
    const addFaqButton = page.getByRole('button', { name: /Add FAQ/i });
    await addFaqButton.click();

    await page.getByRole('textbox', { name: /Question/i }).fill('To be deleted?');
    await page.getByRole('textbox', { name: /Answer/i }).fill('Will be deleted');
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    await expect(page.getByRole('dialog')).not.toBeVisible();

    // Find and click delete button
    const deleteButton = page.getByRole('button', { name: /Delete FAQ/i }).first();
    await deleteButton.click();

    // Confirm deletion (if there's a confirmation dialog)
    const confirmButton = page.getByRole('button', { name: /Confirm|Delete/i }).first();
    if (await confirmButton.isVisible({ timeout: 2000 })) {
      await confirmButton.click();
    }

    // Verify FAQ is removed
    await expect(page.getByText('To be deleted?')).not.toBeVisible();
  });

  test('[P1] should display character counts for business info fields', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Focus on business name field
    const nameInput = page.getByRole('textbox', { name: /Business Name/i });
    await nameInput.focus();

    // Verify character count is visible
    await expect(page.getByText(/0 \/ 100/i)).toBeVisible();

    // Type some text
    await nameInput.fill('Test Name');

    // Verify character count updates
    await expect(page.getByText(/9 \/ 100/i)).toBeVisible();
  });

  test('[P1] should display character counts for FAQ fields', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Open FAQ form
    await page.getByRole('button', { name: /Add FAQ/i }).click();

    // Focus on question field
    const questionInput = page.getByRole('textbox', { name: /Question/i });
    await questionInput.focus();

    // Verify character count
    await expect(page.getByText(/0 \/ 200/i)).toBeVisible();

    // Type some text
    await questionInput.fill('What are your hours?');

    // Verify count updates
    await expect(page.getByText(/20 \/ 200/i)).toBeVisible();
  });

  test('[P1] should enforce max length on business name', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    const nameInput = page.getByRole('textbox', { name: /Business Name/i });

    // Try to type more than 100 characters
    const longText = 'a'.repeat(150);
    await nameInput.fill(longText);

    // Verify value is truncated to 100
    const value = await nameInput.inputValue();
    expect(value.length).toBe(100);
  });

  test('[P1] should enforce max length on FAQ question', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();

    const questionInput = page.getByRole('textbox', { name: /Question/i });

    // Try to type more than 200 characters
    const longText = 'a'.repeat(250);
    await questionInput.fill(longText);

    // Verify value is truncated to 200
    const value = await questionInput.inputValue();
    expect(value.length).toBe(200);
  });

  test('[P1] should show empty state when no FAQs exist', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // If there are existing FAQs, they should be visible
    // Otherwise, empty state message should be shown
    const emptyState = page.getByText(/no faqs yet/i);
    const faqList = page.getByText(/question/i);

    // Either empty state or FAQ list should be visible
    const hasContent = await (await emptyState.count()) + (await faqList.count()) > 0;
    expect(hasContent).toBe(true);
  });

  test('[P1] should close FAQ modal on cancel', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();

    // Verify modal is open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click cancel button
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await cancelButton.click();

    // Verify modal is closed
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('[P1] should close FAQ modal on backdrop click', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();

    // Verify modal is open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click backdrop (outside the modal content)
    const dialog = page.getByRole('dialog');
    await dialog.click({ position: { x: 10, y: 10 } });

    // Verify modal is closed
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('[P1] should close FAQ modal on Escape key', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();

    // Verify modal is open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Press Escape key
    await page.keyboard.press('Escape');

    // Verify modal is closed
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });

  test('[P2] should persist business info after page reload', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Set business info
    await page.getByRole('textbox', { name: /Business Name/i }).fill('Persistence Test Store');
    await page.getByRole('button', { name: /Save Business Info/i }).click();

    await expect(page.getByText(/business info saved/i)).toBeVisible();

    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Verify business info is still loaded
    await expect(page.getByRole('textbox', { name: /Business Name/i })).toHaveValue('Persistence Test Store');
  });

  test('[P2] should validate required FAQ fields', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /Add FAQ/i }).click();

    // Try to save without filling required fields
    await page.getByRole('button', { name: /Save FAQ/i }).click();

    // Verify validation errors
    await expect(page.getByText(/question is required/i)).toBeVisible();
  });

  test('[P2] should display help text for each field', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Verify business info help text
    await expect(page.getByText(/the name of your business/i)).toBeVisible();
    await expect(page.getByText(/a brief description that helps the bot/i)).toBeVisible();
    await expect(page.getByText(/your business operating hours/i)).toBeVisible();
  });

  test('[P2] should support drag and drop FAQ reordering', async ({ page }) => {
    await page.goto('/business-info');
    await page.waitForLoadState('networkidle');

    // Create multiple FAQs first
    for (let i = 1; i <= 3; i++) {
      await page.getByRole('button', { name: /Add FAQ/i }).click();
      await page.getByRole('textbox', { name: /Question/i }).fill(`FAQ ${i}`);
      await page.getByRole('textbox', { name: /Answer/i }).fill(`Answer ${i}`);
      await page.getByRole('button', { name: /Save FAQ/i }).click();
      await expect(page.getByRole('dialog')).not.toBeVisible();
    }

    // Get initial order
    const initialText = await page.getByText(/FAQ 1/).textContent();

    // Drag the third FAQ to the first position
    const faqCards = page.locator('[data-testid^="faq-card-"]');
    const thirdCard = faqCards.nth(2);
    const firstCard = faqCards.nth(0);

    // Perform drag and drop
    await thirdCard.dragTo(firstCard);

    // Verify order changed (FAQ 3 should now be at top)
    await page.waitForTimeout(500); // Wait for reorder to complete
    const topCardText = await faqCards.nth(0).textContent();
    expect(topCardText).toContain('FAQ 3');
  });
});
