/** Shared types for onboarding mode selection (Story 8.6).
 *
 * This file defines the OnboardingMode type used across:
 * - onboardingStore.ts
 * - services/onboarding.ts
 * - services/auth.ts
 * - components/onboarding/PrerequisiteChecklist.tsx
 * - components/onboarding/ModeSelection.tsx
 */

/** Merchant onboarding mode determining feature availability.
 *
 * - general: General chatbot mode (no Shopify, knowledge base Q&A)
 * - ecommerce: E-commerce mode (Shopify integration, product search, orders)
 */
export type OnboardingMode = "general" | "ecommerce";

/** Default onboarding mode for backward compatibility. */
export const DEFAULT_ONBOARDING_MODE: OnboardingMode = "ecommerce";

/** Type guard to validate onboarding mode values. */
export function isValidOnboardingMode(value: unknown): value is OnboardingMode {
  return value === "general" || value === "ecommerce";
}
