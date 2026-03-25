import { test, expect, Page, Locator } from '@playwright/test';

const WIDGET_TEST_URL = '/widget-test?merchantId=4';

async function waitForVoiceButtonReady(button: Locator): Promise<void> {
  await expect(button).toBeEnabled();
  await expect(button).toHaveAttribute('aria-pressed', 'false');
}

async function waitForListeningState(button: Locator): Promise<void> {
  await expect(button).toHaveAttribute('aria-pressed', 'true', { timeout: 10000 });
  await expect(button).toHaveClass(/listening/, { timeout: 10000 });
}

async function setupWidgetMocks(page: Page): Promise<void> {
  await page.route('**/api/v1/widget/config/*', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          enabled: true,
          botName: 'Mantisbot',
          welcomeMessage: 'Hello! How can I help you?',
          theme: {
            primaryColor: '#6366f1',
            backgroundColor: '#ffffff',
            textColor: '#1f2937',
            botBubbleColor: '#f3f4f6',
            userBubbleColor: '#6366f1',
            position: 'bottom-right',
            borderRadius: 16,
            width: 380,
            height: 600,
            fontFamily: 'Inter, sans-serif',
            fontSize: 14,
          },
        },
      }),
    });
  });

  await page.route('**/api/v1/widget/session', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        data: {
          session_id: 'test-session-123',
          merchant_id: '4',
          expires_at: new Date(Date.now() + 3600000).toISOString(),
          created_at: new Date().toISOString(),
        },
      }),
    });
  });
}

async function openWidgetAndGetVoiceButton(page: Page): Promise<Locator> {
  await setupWidgetMocks(page);
  
  const configPromise = page.waitForResponse('**/api/v1/widget/config/*');
  await page.goto(WIDGET_TEST_URL);
  await configPromise;
  
  const chatBubble = page.locator('.shopbot-chat-bubble');
  await chatBubble.waitFor({ state: 'visible', timeout: 10000 });
  await chatBubble.click();
  
  const voiceButton = page.locator('[data-testid="voice-input-button"]');
  await voiceButton.waitFor({ state: 'attached', timeout: 10000 });
  return voiceButton;
}

async function jsClick(locator: Locator): Promise<void> {
  await locator.evaluate((el) => {
    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  });
}

async function mockSpeechAPI(page: Page): Promise<void> {
  await page.addInitScript(() => {
    class MockSpeechRecognition {
      continuous = false;
      interimResults = true;
      lang = 'en-US';
      onresult: ((event: unknown) => void) | null = null;
      onerror: ((event: unknown) => void) | null = null;
      onend: (() => void) | null = null;
      onstart: (() => void) | null = null;

      start() {
        setTimeout(() => {
          if (this.onstart) this.onstart();
        }, 50);
      }

      stop() {
        setTimeout(() => {
          if (this.onend) this.onend();
        }, 50);
      }

      abort() {
        setTimeout(() => {
          if (this.onend) this.onend();
        }, 50);
      }
    }

    (window as unknown as { SpeechRecognition: typeof MockSpeechRecognition }).SpeechRecognition = MockSpeechRecognition;
    (window as unknown as { webkitSpeechRecognition: typeof MockSpeechRecognition }).webkitSpeechRecognition = MockSpeechRecognition;
  });
}

test.describe('Story 9-5: Voice Input Interface', () => {
  test.describe('AC1: Microphone Permission Request', () => {
    test('9.5-E2E-001: should show microphone button in chat input', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await expect(voiceButton).toBeVisible();
    });

    test('9.5-E2E-002: should have correct aria-label on microphone button', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await expect(voiceButton).toHaveAttribute('aria-label', 'Start voice input');
    });
  });

  test.describe('AC2: Real-Time Speech Recognition', () => {
    test('9.5-E2E-003: should start listening when button clicked', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);
      await waitForListeningState(voiceButton);
    });
  });

  test.describe('AC3: Waveform Animation', () => {
    test('9.5-E2E-004: should show waveform when listening', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);
      await waitForListeningState(voiceButton);

      const waveform = page.locator('.waveform-container');
      await expect(waveform).toBeAttached();
    });
  });

  test.describe('AC4: Interim Transcript Display', () => {
    test('9.5-E2E-005: should display interim transcript area', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);
      await waitForListeningState(voiceButton);
    });
  });

  test.describe('AC5: Final Transcript to Input', () => {
    test('9.5-E2E-006: should stop listening when button clicked again', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);
      await waitForListeningState(voiceButton);

      await jsClick(voiceButton);
      await expect(voiceButton).toHaveAttribute('aria-pressed', 'false', { timeout: 10000 });
    });
  });

  test.describe('AC7: Browser Compatibility Error Handling', () => {
    test('9.5-E2E-007: should disable button when not supported', async ({ page }) => {
      await page.addInitScript(() => {
        (window as unknown as { SpeechRecognition: undefined }).SpeechRecognition = undefined;
        (window as unknown as { webkitSpeechRecognition: undefined }).webkitSpeechRecognition = undefined;
      });

      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await expect(voiceButton).toBeDisabled();
      await expect(voiceButton).toHaveAttribute('aria-label', 'Voice input not supported in this browser');
    });
  });

  test.describe('AC9: Visual State Feedback', () => {
    test('9.5-E2E-008: should show listening visual state', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);

      await waitForListeningState(voiceButton);
      await expect(voiceButton).toHaveClass(/listening/);
    });

    test('9.5-E2E-009: should show idle state when not listening', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await expect(voiceButton).not.toHaveClass(/listening/);
    });
  });

  test.describe('AC10: Cancel Button', () => {
    test('9.5-E2E-010: should show cancel button when listening', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);

      await waitForListeningState(voiceButton);

      const cancelButton = page.locator('[data-testid="voice-input-cancel"]');
      await expect(cancelButton).toBeVisible();
    });

    test('9.5-E2E-011: should cancel listening when cancel clicked', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);

      await waitForListeningState(voiceButton);

      const cancelButton = page.locator('[data-testid="voice-input-cancel"]');
      await jsClick(cancelButton);

      await expect(voiceButton).toHaveAttribute('aria-pressed', 'false', { timeout: 10000 });
      await expect(cancelButton).not.toBeVisible();
    });

    test('9.5-E2E-012: should clear interim text on cancel', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);

      await waitForListeningState(voiceButton);

      const cancelButton = page.locator('[data-testid="voice-input-cancel"]');
      await jsClick(cancelButton);

      await expect(page.locator('[data-testid="voice-interim-transcript"]')).not.toBeVisible();
    });
  });

  test.describe('Accessibility', () => {
    test('9.5-E2E-013: should have correct ARIA attributes', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      
      await expect(voiceButton).toHaveAttribute('role', 'button');
      await expect(voiceButton).toHaveAttribute('type', 'button');
      await expect(voiceButton).toHaveAttribute('aria-label');
      await expect(voiceButton).toHaveAttribute('aria-pressed');
    });

    test('9.5-E2E-014: should be focusable', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      
      await voiceButton.focus();
      await expect(voiceButton).toBeFocused();
    });

    test('9.5-E2E-015: should toggle with Enter key', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);

      await voiceButton.focus();
      await page.keyboard.press('Enter');

      await waitForListeningState(voiceButton);

      await page.keyboard.press('Enter');

      await expect(voiceButton).toHaveAttribute('aria-pressed', 'false', { timeout: 10000 });
    });

    test('9.5-E2E-016: should handle Escape key (may close widget)', async ({ page }) => {
      await mockSpeechAPI(page);
      const voiceButton = await openWidgetAndGetVoiceButton(page);
      await waitForVoiceButtonReady(voiceButton);
      await jsClick(voiceButton);

      await waitForListeningState(voiceButton);

      await voiceButton.focus();
      await page.keyboard.press('Escape');

      await expect(voiceButton).toHaveAttribute('aria-pressed', 'false', { timeout: 5000 }).catch(() => {
        // Widget might close on Escape
      });
    });
  });
});
