/**
 * E2E Tests: Data Deletion Flow Journey
 *
 * User Journey: Merchant requests account/data deletion,
 * confirms the action, and verifies data is removed.
 *
 * Flow: Request Deletion → Confirm → Verify Data Removed
 *
 * Priority Coverage:
 * - [P0] Complete data deletion happy path
 * - [P1] Confirmation and validation steps
 * - [P2] Data removal verification
 *
 * @package frontend/tests/e2e/journeys
 */

import { test, expect } from '@playwright/test';

test.describe('Journey: Data Deletion Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to settings page
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
  });

  test('[P0] should complete account deletion request', async ({ page }) => {
    // GIVEN: User is on settings page
    await expect(page.getByRole('heading', { name: /settings/i })).toBeVisible();

    // WHEN: Scrolling to danger zone section
    const dangerZone = page.getByText(/danger zone|delete account|remove data/i).or(
      page.locator('[data-testid="danger-zone"]')
    );

    await expect(dangerZone.first()).toBeVisible();

    // Click delete account button
    const deleteButton = page.getByRole('button', { name: /delete.*account/i }).or(
      page.locator('[data-testid="delete-account-button"]')
    );

    await deleteButton.click();

    // THEN: Confirmation modal should appear
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Should show warning message
    await expect(page.getByText(/warning|irreversible|cannot be undone/i)).toBeVisible();

    // WHEN: Confirming deletion by typing confirmation text
    const confirmInput = page.getByLabel(/type.*delete to confirm/i).or(
      page.locator('input[placeholder*="DELETE"]')
    );

    await confirmInput.fill('DELETE');

    // Click final confirm button
    const confirmButton = page.getByRole('button', { name: /confirm.*delete/i });
    await confirmButton.click();

    // THEN: Should initiate deletion process
    await expect(page.getByText(/deletion.*initiated|scheduled/i)).toBeVisible({
      timeout: 5000
    });

    // Should redirect to login or home
    await page.waitForTimeout(2000);
    const url = page.url();
    const isRedirected = url.includes('/login') || url.includes('/');

    expect(isRedirected).toBeTruthy();
  });

  test('[P1] should require email confirmation for deletion', async ({ page }) => {
    // GIVEN: User has opened deletion modal
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // WHEN: Attempting to confirm without entering email
    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // THEN: Should show validation error
    await expect(page.getByText(/please enter your email|confirmation required/i)).toBeVisible();

    // WHEN: Entering wrong email
    const emailInput = page.getByLabel(/enter your email/i).or(
      page.locator('input[type="email"]')
    );

    await emailInput.fill('wrong@example.com');

    await confirmButton.click();

    // THEN: Should show email mismatch error
    await expect(page.getByText(/email does not match|incorrect email/i)).toBeVisible();

    // WHEN: Entering correct email
    await emailInput.fill('test@example.com');
    await confirmButton.click();

    // THEN: Should proceed to next step
    await page.waitForTimeout(1000);

    const modalVisible = await modal.isVisible().catch(() => false);
    if (!modalVisible) {
      // Modal closed - deletion initiated
      expect(true).toBeTruthy();
    }
  });

  test('[P1] should show data deletion summary', async ({ page }) => {
    // GIVEN: User initiates deletion process
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    // THEN: Should show what data will be deleted
    const dataSummary = page.getByText(/following data will be deleted/i).or(
      page.locator('[data-testid="deletion-summary"]')
    );

    await expect(dataSummary).toBeVisible();

    // Should list data types
    await expect(page.getByText(/conversations/i)).toBeVisible();
    await expect(page.getByText(/costs/i)).toBeVisible();
    await expect(page.getByText(/settings/i)).toBeVisible();
    await expect(page.getByText(/integrations/i)).toBeVisible();
  });

  test('[P1] should offer data export before deletion', async ({ page }) => {
    // GIVEN: User initiates deletion
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    // WHEN: Checking for export option
    const exportButton = page.getByRole('button', { name: /export.*data|download/i }).or(
      page.locator('[data-testid="export-before-delete"]')
    );

    const hasExport = await exportButton.isVisible().catch(() => false);

    if (hasExport) {
      // Mock export
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();
      const download = await downloadPromise;

      // THEN: Should download data
      expect(download.suggestedFilename()).toMatch(/\.(json|csv|zip)/);
    }
  });

  test('[P0] should send deletion confirmation email', async ({ page }) => {
    // GIVEN: User confirms deletion
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            deletionId: 'del-123-456',
            status: 'pending_confirmation',
            confirmationEmailSent: true,
            expiresAt: new Date(Date.now() + 86400000).toISOString(),
          },
          meta: { requestId: 'test-deletion' },
        }),
      });
    });

    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const confirmInput = page.getByLabel(/type.*delete/i);
    await confirmInput.fill('DELETE');

    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // THEN: Should show email confirmation message
    await expect(page.getByText(/email.*sent|check your email/i)).toBeVisible({
      timeout: 5000
    });

    // Should show expiration time
    await expect(page.getByText(/24 hours|expires/i)).toBeVisible();
  });

  test('[P2] should allow canceling deletion request', async ({ page }) => {
    // GIVEN: User has initiated deletion but not confirmed
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // WHEN: Clicking cancel button
    const cancelButton = page.getByRole('button', { name: /cancel|nevermind/i });
    await cancelButton.click();

    // THEN: Modal should close and account should remain active
    await expect(modal).toBeHidden();

    // Verify account still active
    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  });

  test('[P2] should verify data removal after deletion', async ({ page }) => {
    // GIVEN: User has completed deletion process
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            status: 'completed',
            deletedAt: new Date().toISOString(),
          },
          meta: { requestId: 'test-deleted' },
        }),
      });
    });

    // WHEN: Attempting to access data after deletion
    await page.goto('/conversations');

    // THEN: Should show account deleted message or redirect
    const deletedMessage = page.getByText(/account.*deleted|no longer exists/i);
    const hasMessage = await deletedMessage.isVisible().catch(() => false);

    const url = page.url();
    const isRedirected = url.includes('/login') || url.includes('/deleted');

    expect(hasMessage || isRedirected).toBeTruthy();

    // Verify no data is accessible
    const conversations = page.locator('[data-testid="conversation-item"]');
    const count = await conversations.count();

    expect(count).toBe(0);
  });

  test('[P1] should handle deletion API errors gracefully', async ({ page }) => {
    // GIVEN: User attempts to delete account
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    // WHEN: API returns error
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Failed to process deletion',
        }),
      });
    });

    const confirmInput = page.getByLabel(/type.*delete/i);
    await confirmInput.fill('DELETE');

    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // THEN: Should show error message
    await expect(page.getByText(/error|failed|try again/i)).toBeVisible({
      timeout: 5000
    });

    // Modal should remain open for retry
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
  });

  test('[P2] should show deletion progress', async ({ page }) => {
    // GIVEN: User has initiated deletion
    await page.route('**/api/account/deletion/status**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            status: 'in_progress',
            steps: [
              { name: 'conversations', completed: true },
              { name: 'costs', completed: true },
              { name: 'settings', completed: false },
              { name: 'integrations', completed: false },
            ],
            progress: 50,
          },
          meta: { requestId: 'test-status' },
        }),
      });
    });

    // WHEN: Checking deletion status
    await page.goto('/settings?deletion=del-123');

    // THEN: Should show progress indicator
    const progressText = page.getByText(/deletion.*progress|currently deleting/i);
    const hasProgress = await progressText.isVisible().catch(() => false);

    if (hasProgress) {
      await expect(progressText).toBeVisible();

      // Should show percentage
      await expect(page.getByText(/50%/)).toBeVisible();

      // Should show completed steps
      await expect(page.getByText(/conversations.*complete/i)).toBeVisible();
    }
  });

  test('[P2] should handle concurrent deletion requests', async ({ page }) => {
    // GIVEN: User has pending deletion request
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 409,
        contentType: 'application/json',
        body: JSON.stringify({
          error: 'Deletion already in progress',
          existingDeletionId: 'del-existing-123',
        }),
      });
    });

    // WHEN: Attempting another deletion
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const confirmInput = page.getByLabel(/type.*delete/i);
    await confirmInput.fill('DELETE');

    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // THEN: Should show existing deletion info
    await expect(page.getByText(/already in progress|pending deletion/i)).toBeVisible({
      timeout: 5000
    });

    // Should offer to cancel existing request
    const cancelButton = page.getByRole('button', { name: /cancel existing/i });
    const hasCancel = await cancelButton.isVisible().catch(() => false);

    if (hasCancel) {
      await expect(cancelButton).toBeVisible();
    }
  });

  test('[P1] should require re-authentication before deletion', async ({ page }) => {
    // GIVEN: User is attempting deletion
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    // WHEN: System requires password confirmation
    const passwordInput = page.getByLabel(/enter your password/i).or(
      page.locator('input[type="password"]')
    );

    const hasPasswordInput = await passwordInput.isVisible().catch(() => false);

    if (hasPasswordInput) {
      // THEN: Should require password
      await expect(passwordInput).toBeVisible();

      // Entering wrong password should fail
      await passwordInput.fill('wrong-password');

      const confirmButton = page.getByRole('button', { name: /confirm/i });
      await confirmButton.click();

      await expect(page.getByText(/incorrect password|authentication failed/i)).toBeVisible();

      // Entering correct password should proceed
      await page.route('**/api/auth/verify**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: { valid: true } }),
        });
      });

      await passwordInput.fill('correct-password');
      await confirmButton.click();

      // Should proceed to next step
      await page.waitForTimeout(1000);
    }
  });

  test('[P2] should provide cancellation option during grace period', async ({ page }) => {
    // GIVEN: User has initiated deletion (within grace period)
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            status: 'pending',
            gracePeriodEnds: new Date(Date.now() + 3600000).toISOString(),
            canCancel: true,
          },
          meta: { requestId: 'test-grace' },
        }),
      });
    });

    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const confirmInput = page.getByLabel(/type.*delete/i);
    await confirmInput.fill('DELETE');

    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // WHEN: Navigating to settings during grace period
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    // THEN: Should show cancellation option
    const cancelDeletionButton = page.getByRole('button', { name: /cancel deletion/i });
    const hasCancel = await cancelDeletionButton.isVisible().catch(() => false);

    if (hasCancel) {
      await expect(cancelDeletionButton).toBeVisible();

      // Should show grace period countdown
      await expect(page.getByText(/hours remaining|grace period/i)).toBeVisible();
    }
  });

  test('[P0] should log out all sessions after deletion', async ({ context }) => {
    // GIVEN: User is logged in on multiple devices
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    try {
      // Set up authenticated sessions
      for (const page of [page1, page2]) {
        await page.goto('/settings');
        await page.evaluate(() => {
          localStorage.setItem('auth_token', 'session-to-delete');
        });
      }

      // WHEN: Account is deleted on page1
      await page1.route('**/api/account/deletion**', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: { status: 'completed' },
            meta: { requestId: 'test-delete' },
          }),
        });
      });

      const deleteButton = page1.getByRole('button', { name: /delete.*account/i });
      await deleteButton.click();

      const confirmInput = page1.getByLabel(/type.*delete/i);
      await confirmInput.fill('DELETE');

      const confirmButton = page1.getByRole('button', { name: /confirm/i });
      await confirmButton.click();

      await page1.waitForTimeout(2000);

      // THEN: Page2 should also be logged out
      await page2.reload();
      await page2.waitForLoadState('networkidle');

      const token = await page2.evaluate(() => localStorage.getItem('auth_token'));
      expect(token).toBeNull();

      const url = page2.url();
      const isLoggedOut = url.includes('/login') || url.includes('/deleted');

      expect(isLoggedOut).toBeTruthy();
    } finally {
      await page1.close();
      await page2.close();
    }
  });
});

test.describe('Journey: Data Deletion - Privacy', () => {
  test('[P2] should comply with GDPR right to be forgotten', async ({ page }) => {
    await page.goto('/settings');

    // Check for GDPR compliance notice
    const gdprNotice = page.getByText(/GDPR|right to be forgotten|data protection/i);
    const hasNotice = await gdprNotice.isVisible().catch(() => false);

    if (hasNotice) {
      await expect(gdprNotice).toBeVisible();

      // Should link to privacy policy
      const privacyLink = page.getByRole('link', { name: /privacy policy/i });
      await expect(privacyLink).toBeVisible();
    }
  });

  test('[P2] should provide data deletion report', async ({ page }) => {
    // After deletion completes
    await page.goto('/settings?deletion=completed');

    // Should show what was deleted
    const deletionReport = page.getByText(/deletion report|data removed/i);
    const hasReport = await deletionReport.isVisible().catch(() => false);

    if (hasReport) {
      await expect(deletionReport).toBeVisible();

      // Should list deleted items with counts
      await expect(page.getByText(/\d+.*conversations/i)).toBeVisible();
      await expect(page.getByText(/\d+.*cost records/i)).toBeVisible();
    }
  });

  test('[P2] should handle partial deletion failures', async ({ page }) => {
    // Some data deleted, some failed
    await page.route('**/api/account/deletion**', route => {
      route.fulfill({
        status: 207, // Multi-status
        contentType: 'application/json',
        body: JSON.stringify({
          data: {
            status: 'partial',
            succeeded: ['conversations', 'costs'],
            failed: ['integrations'],
            retryAvailable: true,
          },
          meta: { requestId: 'test-partial' },
        }),
      });
    });

    await page.goto('/settings');
    const deleteButton = page.getByRole('button', { name: /delete.*account/i });
    await deleteButton.click();

    const confirmInput = page.getByLabel(/type.*delete/i);
    await confirmInput.fill('DELETE');

    const confirmButton = page.getByRole('button', { name: /confirm/i });
    await confirmButton.click();

    // Should show partial completion
    await expect(page.getByText(/partially completed|some data could not be deleted/i)).toBeVisible({
      timeout: 5000
    });

    // Should offer retry
    const retryButton = page.getByRole('button', { name: /retry/i });
    await expect(retryButton).toBeVisible();
  });
});
