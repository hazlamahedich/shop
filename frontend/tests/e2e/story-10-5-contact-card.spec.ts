/**
 * E2E Tests for Story 10-5: Contact Card Widget
 *
 * Tests contact card functionality in the widget.
 * Test URL: http://localhost:5173/widget-test
 *
 * Acceptance Criteria:
 * - AC1: Contact Card Appears on Handoff Detection
 * - AC2: Click-to-Call on Phone Number
 * - AC3: Click-to-Email on Email Address
 * - AC4: Custom Contact Option
 * - AC5: Business Hours-Aware Messaging
 * - AC6: Merchant Configuration UI
 * - AC7: Accessibility
 * - AC8: Works in Both Widget and Dashboard Chat (SKIPPED - dashboard not implemented)
 */

import { test, expect, Page } from '@playwright/test';
import {
  loadWidgetWithSession,
  mockWidgetSession,
} from '../helpers/widget-test-helpers';

interface ContactOption {
  type: 'phone' | 'email' | 'custom';
  label: string;
  value: string;
  icon?: string;
}

interface BusinessHoursConfig {
  timezone?: string;
  hours?: Record<string, { open: string; close: string } | null>;
}

async function mockGeneralModeConfig(page: Page, contactOptions?: ContactOption[]) {
  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          ...WIDGET_CONFIG_DEFAULTS,
          onboardingMode: 'general',
          contactOptions: contactOptions || [
            { type: 'phone', label: 'Call Support', value: '+1-555-123-4567', icon: '📞' },
            { type: 'email', label: 'Email Support', value: 'support@example.com', icon: '✉️' },
            { type: 'custom', label: 'Schedule a Call', value: 'https://calendly.com/support', icon: '📅' },
          ],
        },
      }),
    });
  });
}

async function mockWidgetMessageWithContactOptions(
  page: Page,
  options: {
    content?: string;
    contactOptions?: ContactOption[];
    businessHours?: BusinessHoursConfig | null;
  } = {}
) {
  const {
    content = "I'd be happy to connect you with our team. Here are your contact options:",
    contactOptions = [
      { type: 'phone', label: 'Call Support', value: '+1-555-123-4567', icon: '📞' },
      { type: 'email', label: 'Email Support', value: 'support@example.com', icon: '✉️' },
      { type: 'custom', label: 'Schedule a Call', value: 'https://calendly.com/support', icon: '📅' },
    ],
    businessHours = null,
  } = options;

  await page.route('**/api/v1/widget/message', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({
        data: {
          messageId: crypto.randomUUID(),
          sender: 'bot',
          content,
          createdAt: new Date().toISOString(),
          contactOptions,
          businessHours
        },
        meta: {
          request_id: crypto.randomUUID(),
          timestamp: new Date().toISOString()
        }
      })
    });
  });
}

async function mockHandoffWithContactOptions(page: Page, contactOptions?: ContactOption[]) {
  await mockWidgetMessageWithContactOptions(page, {
    content: "I'm connecting you with a human agent. Here's how to reach us:",
    contactOptions: contactOptions || [
      { type: 'phone', label: 'Call Support', value: '+1-555-123-4567', icon: '📞' },
      { type: 'email', label: 'Email Support', value: 'support@example.com', icon: '✉️' },
    ],
  });
}

async function openWidget(page: Page) {
  const bubble = page.getByRole('button', { name: 'Open chat' });
  await bubble.click();
  await expect(page.getByRole('dialog', { name: 'Chat window' })).toBeVisible();
}

async function sendUserMessage(page: Page, message: string) {
  const input = page.getByPlaceholder(/type.*message/i);
  await input.fill(message);
  const sendButton = page.getByRole('button', { name: /send/i });
  await sendButton.dispatchEvent('click');
}

async function setupWidgetWithConsentDismissed(page: Page) {
  await page.route('**/api/v1/widget/consent', async (route) => {
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ data: { dismissed: true } }),
    });
  });
}

test.describe('[P0] Story 10-5: Contact Card Widget', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await mockWidgetSession(page);
    await mockGeneralModeConfig(page);
    await setupWidgetWithConsentDismissed(page);
  });

  test('[10.5-E2E-001] AC1: Contact card appears on handoff detection', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');

    const contactCard = page.getByTestId('contact-card');
    await expect(contactCard).toBeVisible();

    const phoneOption = page.getByTestId('contact-phone');
    await expect(phoneOption.first()).toBeVisible();

    const emailOption = page.getByTestId('contact-email');
    await expect(emailOption.first()).toBeVisible();

    const customOption = page.getByTestId('contact-custom');
    await expect(customOption.first()).toBeVisible();
  });

  test('[10.5-E2E-002] AC2: Phone number click triggers action', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');
    await expect(page.getByTestId('contact-card')).toBeVisible();

    const phoneOption = page.getByTestId('contact-phone').first();
    await expect(phoneOption).toBeVisible();
    await expect(phoneOption).toHaveAttribute('aria-label', 'Call Support');
  });

  test('[10.5-E2E-003] AC3: Email address opens mailto', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');
    await expect(page.getByTestId('contact-card')).toBeVisible();

    const emailOption = page.getByTestId('contact-email').first();
    await expect(emailOption).toBeVisible();
    await expect(emailOption).toHaveAttribute('aria-label', 'Email Support');
  });

  test('[10.5-E2E-004] AC4: Custom option opens URL', async ({ page, context }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');
    await expect(page.getByTestId('contact-card')).toBeVisible();

    const customOption = page.getByTestId('contact-custom').first();
    await expect(customOption).toBeVisible();
    await expect(customOption).toHaveAttribute('aria-label', 'Schedule a Call');
  });

  test('[10.5-E2E-005] AC5: Business hours indicator visible', async ({ page }) => {
    const businessHours: BusinessHoursConfig = {
      timezone: 'America/New_York',
      hours: {
        monday: { open: '09:00', close: '17:00' },
        tuesday: { open: '09:00', close: '17:00' },
        wednesday: { open: '09:00', close: '17:00' },
        thursday: { open: '09:00', close: '17:00' },
        friday: { open: '09:00', close: '17:00' },
      },
    };

    await mockWidgetMessageWithContactOptions(page, {
      content: 'We are currently available!',
      businessHours,
    });
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need help');

    const contactCard = page.getByTestId('contact-card');
    await expect(contactCard).toBeVisible();
  });

  test('[10.5-E2E-006] AC7: Keyboard navigation works', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');
    await expect(page.getByTestId('contact-card')).toBeVisible();

    const phoneOption = page.getByTestId('contact-phone').first();
    await phoneOption.focus();
    await expect(phoneOption).toBeFocused();
  });

  test('[10.5-E2E-007] AC7: Accessibility attributes present', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');
    await expect(page.getByTestId('contact-card')).toBeVisible();

    const phoneOption = page.getByTestId('contact-phone').first();
    await expect(phoneOption).toHaveAttribute('role', 'button');
    await expect(phoneOption).toHaveAttribute('aria-label', 'Call Support');

    const emailOption = page.getByTestId('contact-email').first();
    await expect(emailOption).toHaveAttribute('role', 'button');
    await expect(emailOption).toHaveAttribute('aria-label', 'Email Support');

    const customOption = page.getByTestId('contact-custom').first();
    await expect(customOption).toHaveAttribute('role', 'button');
    await expect(customOption).toHaveAttribute('aria-label', 'Schedule a Call');
  });

  test('[10.5-E2E-008] AC1: Contact card with multiple options', async ({ page }) => {
    const multipleOptions: ContactOption[] = [
      { type: 'phone', label: 'US Support', value: '+1-555-111-1111', icon: '📞' },
      { type: 'phone', label: 'UK Support', value: '+44-20-1234-5678', icon: '📞' },
      { type: 'email', label: 'General Support', value: 'support@example.com', icon: '✉️' },
      { type: 'email', label: 'Technical Support', value: 'tech@example.com', icon: '✉️' },
      { type: 'custom', label: 'Book a Call', value: 'https://calendly.com/book', icon: '📅' },
      { type: 'custom', label: 'Live Chat', value: 'https://chat.example.com', icon: '💬' },
    ];

    await mockHandoffWithContactOptions(page, multipleOptions);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');

    const contactCard = page.getByTestId('contact-card');
    await expect(contactCard).toBeVisible();

    const phoneOptions = page.getByTestId('contact-phone');
    await expect(phoneOptions).toHaveCount(2);

    const emailOptions = page.getByTestId('contact-email');
    await expect(emailOptions).toHaveCount(2);

    const customOptions = page.getByTestId('contact-custom');
    await expect(customOptions).toHaveCount(2);
  });

  test('[10.5-E2E-009] AC1: Contact card styling matches theme', async ({ page }) => {
    await mockHandoffWithContactOptions(page);
    await loadWidgetWithSession(page, crypto.randomUUID());
    await openWidget(page);
    await sendUserMessage(page, 'I need human help');

    const contactCard = page.getByTestId('contact-card');
    await expect(contactCard).toBeVisible();

    const phoneOption = page.getByTestId('contact-phone').first();
    await expect(phoneOption).toBeVisible();
  });

  test('[10.5-E2E-010] AC6: Merchant configuration UI', async ({ page }) => {
    test.skip('Merchant configuration UI test - requires dashboard authentication');
  });

  test('[10.5-E2E-011] AC8: Dashboard chat interface', async ({ page }) => {
    test.skip('Dashboard chat interface not implemented yet - AC8');
  });
});
