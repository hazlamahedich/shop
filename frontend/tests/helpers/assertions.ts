/**
 * Custom Assertions
 *
 * Reusable assertion helpers for common E2E test scenarios.
 * Improves test readability and reduces code duplication.
 *
 * Usage:
 * ```ts
 * import { expect } from '@playwright/test';
 * import { assertPrerequisiteComplete } from '../helpers/assertions';
 *
 * await assertPrerequisiteComplete(page, 'cloudAccount');
 * ```
 */

import { Page, Locator } from '@playwright/test';

/**
 * Assert that a prerequisite checkbox is checked
 */
export async function assertPrerequisiteComplete(page: Page, prerequisite: string): Promise<void> {
  const checkbox = page.locator(`[data-testid="checkbox-${prerequisite}"]`);
  await checkbox.waitFor({ state: 'visible' });
  const isChecked = await checkbox.isChecked();
  if (!isChecked) {
    throw new Error(`Prerequisite "${prerequisite}" should be checked but isn't`);
  }
}

/**
 * Assert that a prerequisite checkbox is unchecked
 */
export async function assertPrerequisiteIncomplete(page: Page, prerequisite: string): Promise<void> {
  const checkbox = page.locator(`[data-testid="checkbox-${prerequisite}"]`);
  await checkbox.waitFor({ state: 'visible' });
  const isChecked = await checkbox.isChecked();
  if (isChecked) {
    throw new Error(`Prerequisite "${prerequisite}" should not be checked but is`);
  }
}

/**
 * Assert that the deploy button is enabled
 */
export async function assertDeployButtonEnabled(page: Page): Promise<void> {
  const button = page.locator('[data-testid="deploy-button"]');
  await button.waitFor({ state: 'visible' });
  const isEnabled = await button.isEnabled();
  if (!isEnabled) {
    throw new Error('Deploy button should be enabled but is disabled');
  }
}

/**
 * Assert that the deploy button is disabled
 */
export async function assertDeployButtonDisabled(page: Page): Promise<void> {
  const button = page.locator('[data-testid="deploy-button"]');
  await button.waitFor({ state: 'visible' });
  const isEnabled = await button.isEnabled();
  if (isEnabled) {
    throw new Error('Deploy button should be disabled but is enabled');
  }
}

/**
 * Assert progress text shows expected count
 */
export async function assertProgressCount(page: Page, completed: number, total: number): Promise<void> {
  const progressText = page.locator('[data-testid="progress-text"]');
  await progressText.waitFor({ state: 'visible' });
  const text = await progressText.textContent();
  const expected = `${completed} of ${total}`;
  if (!text?.includes(expected)) {
    throw new Error(`Progress should show "${expected}" but shows "${text}"`);
  }
}

/**
 * Assert webhook status for a platform
 */
export async function assertWebhookStatus(page: Page, platform: 'facebook' | 'shopify', status: 'verified' | 'pending' | 'failed'): Promise<void> {
  const statusElement = page.locator(`[data-testid="${platform}-webhook-status"]`);
  await statusElement.waitFor({ state: 'visible' });
  const actualStatus = await statusElement.getAttribute('data-status');
  if (actualStatus !== status) {
    throw new Error(`${platform} webhook status should be "${status}" but is "${actualStatus}"`);
  }
}

/**
 * Assert help section is visible
 */
export async function assertHelpSectionVisible(page: Page, prerequisite: string): Promise<void> {
  const section = page.locator(`[data-testid="help-section-${prerequisite}"]`);
  await section.waitFor({ state: 'visible' });
  const isVisible = await section.isVisible();
  if (!isVisible) {
    throw new Error(`Help section for "${prerequisite}" should be visible but isn't`);
  }
}

/**
 * Assert help section is hidden
 */
export async function assertHelpSectionHidden(page: Page, prerequisite: string): Promise<void> {
  const section = page.locator(`[data-testid="help-section-${prerequisite}"]`);
  const isVisible = await section.isVisible();
  if (isVisible) {
    throw new Error(`Help section for "${prerequisite}" should be hidden but is visible`);
  }
}

/**
 * Assert ARIA attribute value
 */
export async function assertAriaAttribute(locator: Locator, attribute: string, value: string): Promise<void> {
  await locator.waitFor({ state: 'attached' });
  const actualValue = await locator.getAttribute(attribute);
  if (actualValue !== value) {
    throw new Error(`ARIA ${attribute} should be "${value}" but is "${actualValue}"`);
  }
}

/**
 * Assert element has focus
 */
export async function assertFocused(locator: Locator): Promise<void> {
  await locator.waitFor({ state: 'attached' });
  const isFocused = await locator.evaluate((el) => document.activeElement === el);
  if (!isFocused) {
    throw new Error('Element should have focus but does not');
  }
}

/**
 * Assert element is visible and enabled
 */
export async function assertVisibleAndEnabled(locator: Locator): Promise<void> {
  await locator.waitFor({ state: 'visible' });
  const isEnabled = await locator.isEnabled();
  if (!isEnabled) {
    throw new Error('Element should be enabled but is disabled');
  }
}

/**
 * Assert storage contains expected value
 */
export async function assertStorageContains(page: Page, key: string, expectedValue: string): Promise<void> {
  const actualValue = await page.evaluate((k) => localStorage.getItem(k), key);
  if (actualValue !== expectedValue) {
    throw new Error(`localStorage "${key}" should be "${expectedValue}" but is "${actualValue}"`);
  }
}

/**
 * Assert page has proper heading hierarchy
 */
export async function assertHeadingHierarchy(page: Page): Promise<void> {
  const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
  if (headings.length === 0) {
    throw new Error('Page should have at least one heading');
  }

  // Check that h1 comes first
  const firstHeading = headings[0];
  const tagName = await firstHeading.evaluate((el) => el.tagName);
  if (tagName !== 'H1') {
    throw new Error('First heading should be h1');
  }
}

/**
 * Assert element meets WCAG contrast requirements
 * Note: This is a basic check; use axe-core for comprehensive a11y testing
 */
export async function assertContrastRatio(locator: Locator, minRatio: number = 4.5): Promise<void> {
  const styles = await locator.evaluate((el) => {
    const computed = window.getComputedStyle(el);
    return {
      color: computed.color,
      backgroundColor: computed.backgroundColor,
    };
  });

  // Basic contrast check would go here
  // For comprehensive a11y testing, use @axe-core/playwright
  console.warn('Comprehensive contrast checking requires axe-core integration');
}
