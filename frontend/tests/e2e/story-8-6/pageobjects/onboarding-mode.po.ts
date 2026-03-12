/**
 * PageObject for Onboarding Mode Selection
 *
 * Story 8-6: Frontend Onboarding Mode Selection
 * Shared selectors and helpers for onboarding mode tests
 */

import { Page, Locator } from '@playwright/test';

export const OnboardingMode = {
  container: '[data-testid="mode-selection"]',
  title: 'h2',

  modeCards: {
    general: '[data-testid="mode-card-general"]',
    ecommerce: '[data-testid="mode-card-ecommerce"]',
  },

  modeLabels: {
    general: 'text=AI Chatbot',
    ecommerce: 'text=E-commerce Assistant',
  },

  continueButton: '[data-testid="mode-continue-button"]',
  backButton: '[data-testid="mode-back-button"]',
  selectedMode: '[data-testid="selected-mode"]',
  modeDescription: 'p.text-sm.text-gray-600',
  errorMessage: '[data-testid="mode-error-message"]',
  retryButton: '[data-testid="mode-retry-button"]',
} as const;

export const OnboardingSteps = {
  stepIndicator: '[data-testid="step-indicator"]',
  currentStep: '[data-testid="current-step"]',
  facebookConnection: '[data-testid="facebook-connection"]',
  shopifyConnection: '[data-testid="shopify-connection"]',
  llmConfiguration: '[data-testid="llm-configuration"]',
} as const;

export interface MockAuthState {
  isAuthenticated: boolean;
  merchant: {
    id: string;
    email: string;
    name: string;
    hasStoreConnected: boolean;
  };
  sessionExpiresAt: string;
  isLoading: boolean;
  error: string | null;
}

export function createMockAuthState(overrides: Partial<MockAuthState> = {}): MockAuthState {
  return {
    isAuthenticated: true,
    merchant: {
      id: 'test-merchant-1',
      email: 'test@test.com',
      name: 'Test Merchant',
      hasStoreConnected: false,
    },
    sessionExpiresAt: new Date(Date.now() + 3600000).toISOString(),
    isLoading: false,
    error: null,
    ...overrides,
  };
}

export async function setupMockAuth(page: Page, authState?: Partial<MockAuthState>): Promise<void> {
  const mockAuthState = createMockAuthState(authState);
  await page.addInitScript((state) => {
    localStorage.setItem('shop_auth_state', JSON.stringify(state));
  }, mockAuthState);
}

export async function selectModeAndContinue(
  page: Page,
  mode: 'general' | 'ecommerce'
): Promise<void> {
  const modeCard = page.locator(
    mode === 'general' ? OnboardingMode.modeCards.general : OnboardingMode.modeCards.ecommerce
  );
  await modeCard.click();
  await page.locator(OnboardingMode.continueButton).click();
}
