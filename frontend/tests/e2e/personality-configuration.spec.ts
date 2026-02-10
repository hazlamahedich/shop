import { test, expect } from '../support/merged-fixtures';

test.describe('Bot Personality Configuration E2E', () => {
  test.beforeEach(async ({ page, interceptNetworkCall, authToken }) => {
    // Setup interception for initial config load
    const configCall = interceptNetworkCall({ url: '**/api/merchant/personality' });

    // Navigate to personality config page
    await page.goto('/personality');
    await configCall;
  });

  test('[P0] should select and save Professional personality', async ({
    page,
    interceptNetworkCall,
  }) => {
    // Setup intercept for save
    const saveCall = interceptNetworkCall({
      method: 'PATCH',
      url: '**/api/merchant/personality',
    });

    // Interact: Select Professional - use the button with the personality name
    await page.getByRole('button', { name: /Professional.*Direct.*helpful/ }).click();

    // Wait for selection to be reflected (check for the pressed state indicator)
    await expect(page.getByRole('button', { name: /Professional.*Direct.*helpful/ })).toHaveAttribute('aria-pressed', 'true');

    // Scroll to the Save button to ensure it's in viewport (important for mobile)
    const saveButton = page.getByRole('button', { name: 'Save Configuration' });
    await saveButton.scrollIntoViewIfNeeded();

    // Wait for button to be stable before clicking
    await page.waitForTimeout(200);

    // Save - use force option to bypass any pointer event issues on mobile
    await saveButton.click({ force: true });

    // Assert API call - check the data inside the envelope
    const { requestJson, status, responseJson } = await saveCall;
    expect(status).toBe(200);
    // The request body is sent directly
    expect(requestJson.personality).toBe('professional');
    // The response is wrapped in MinimalEnvelope with data property
    expect(responseJson.data.personality).toBe('professional');

    // Assert UI feedback - check for the success message text
    await expect(page.getByText(/Personality configuration saved successfully/)).toBeVisible();
  });

  test('[P1] should customize greeting and reset', async ({ page, interceptNetworkCall }) => {
    // First select a personality to show the greeting editor
    await page.getByRole('button', { name: /Professional.*Direct.*helpful/ }).click();

    // Wait for greeting editor to appear - scroll into view for mobile
    const customizeSection = page.getByText('Customize Greeting');
    await customizeSection.scrollIntoViewIfNeeded();
    await expect(customizeSection).toBeVisible();

    // Interact: Customize greeting - use textarea selector
    const customGreeting = 'Welcome to the future of shopping!';
    const greetingTextarea = page.getByRole('textbox', { name: 'Custom Greeting' });
    await greetingTextarea.scrollIntoViewIfNeeded();
    await greetingTextarea.fill(customGreeting);

    // Check character count - the format is "0 / 500" with spaces
    await expect(page.getByText(`${customGreeting.length} / 500`)).toBeVisible();

    // Wait for the reset button to appear and be stable
    const resetButton = page.getByRole('button', { name: 'Reset to Default' });
    await resetButton.scrollIntoViewIfNeeded();
    await expect(resetButton).toBeVisible();
    await page.waitForTimeout(200);

    // Reset - use force option to bypass any pointer event issues on mobile
    await resetButton.click({ force: true });

    // Verify reset - wait a moment for state to update, then check textarea is empty
    await page.waitForTimeout(200); // Increased delay for state update
    await expect(greetingTextarea).toHaveValue('', { timeout: 5000 });
  });

  test('[P2] should display personality cards with correct information', async ({ page }) => {
    // Verify all three personality cards are displayed
    await expect(page.getByRole('button', { name: /Friendly.*Casual.*warm/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Professional.*Direct.*helpful/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Enthusiastic.*High-energy/ })).toBeVisible();
  });
});
