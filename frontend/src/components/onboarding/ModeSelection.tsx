/** ModeSelection Component (Story 8.6).

Displays onboarding mode selection screen with two options:
- General Chatbot (knowledge base, FAQ, customer support)
- E-commerce (Shopify, products, cart, checkout)

Features:
- WCAG AA accessibility compliance
- Keyboard navigation support
- Screen reader announcements
- High contrast mode support
- Debounced mode selection to prevent rapid API calls
*/

import * as React from "react";
import { Bot, ShoppingCart, Check } from "lucide-react";
import { Card } from "../ui/Card";
import { Button } from "../ui/Button";
import { OnboardingMode } from "../../types/onboarding";

export interface ModeSelectionProps {
  selectedMode: OnboardingMode | null;
  onModeSelect: (mode: OnboardingMode) => void;
  onContinue: () => void;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

interface ModeCardData {
  mode: OnboardingMode;
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
  iconColor: string;
  borderColor: string;
}

const MODES: ModeCardData[] = [
  {
    mode: "general",
    icon: <Bot className="w-12 h-12" />,
    title: "AI Chatbot",
    description: "Customer support, FAQ, knowledge base Q&A",
    features: ["No store required", "Quick setup", "Embed anywhere"],
    iconColor: "text-blue-500",
    borderColor: "border-blue-500",
  },
  {
    mode: "ecommerce",
    icon: <ShoppingCart className="w-12 h-12" />,
    title: "E-commerce Assistant",
    description: "Product search, cart, checkout, order tracking",
    features: ["Shopify integration", "Facebook Messenger", "Full shopping experience"],
    iconColor: "text-emerald-500",
    borderColor: "border-emerald-500",
  },
];

// Debounce timeout in milliseconds
const DEBOUNCE_MS = 150;

export function ModeSelection({
  selectedMode,
  onModeSelect,
  onContinue,
  isLoading = false,
  error = null,
  onRetry,
}: ModeSelectionProps): React.ReactElement {
  // Debounce timer ref to prevent rapid mode selection
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Debounced mode selection handler
  const handleModeSelect = React.useCallback((mode: OnboardingMode) => {
    // Clear any pending debounce timer
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Debounce the mode selection to prevent rapid API calls
    debounceRef.current = setTimeout(() => {
      onModeSelect(mode);
    }, DEBOUNCE_MS);
  }, [onModeSelect]);

  // Cleanup debounce timer on unmount
  React.useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent, mode: OnboardingMode) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleModeSelect(mode);
    }
  };

  return (
    <div
      className="w-full max-w-3xl mx-auto p-4"
      data-theme="onboarding"
      data-testid="mode-selection"
    >
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">Choose Your Setup</h2>
        <p className="text-gray-500 mt-2">
          Select how you want to use your AI assistant. You can change this later.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {MODES.map((modeData) => {
          const isSelected = selectedMode === modeData.mode;
          return (
            <Card
              key={modeData.mode}
              role="button"
              tabIndex={0}
              aria-pressed={isSelected}
              aria-label={`Select ${modeData.title} mode`}
              onKeyDown={(e) => handleKeyDown(e, modeData.mode)}
              onClick={() => handleModeSelect(modeData.mode)}
              className={`cursor-pointer transition-all duration-200 p-6 relative ${
                isSelected
                  ? `ring-2 ring-offset-2 ${modeData.borderColor} ring-opacity-100 shadow-lg scale-[1.02]`
                  : "hover:shadow-md hover:scale-[1.01]"
              }`}
              data-testid={`mode-card-${modeData.mode}`}
            >
              {isSelected && (
                <div
                  className={`absolute top-3 right-3 w-6 h-6 rounded-full ${modeData.borderColor} bg-current flex items-center justify-center`}
                  style={{ backgroundColor: modeData.mode === "general" ? "#3b82f6" : "#10b981" }}
                  aria-hidden="true"
                >
                  <Check className="w-4 h-4 text-white" />
                </div>
              )}

              <div className="flex flex-col items-center text-center space-y-4">
                <div className={`${modeData.iconColor}`}>{modeData.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900">{modeData.title}</h3>
                <p className="text-sm text-gray-600">{modeData.description}</p>

                <ul className="text-sm text-gray-700 space-y-2 w-full">
                  {modeData.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center justify-center gap-2">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0" aria-hidden="true" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </Card>
          );
        })}
      </div>

      <div className="flex justify-center">
        <Button
          onClick={onContinue}
          disabled={selectedMode === null || isLoading}
          size="lg"
          className="px-12"
          dataTestId="mode-continue-button"
          aria-disabled={selectedMode === null || isLoading}
        >
          {isLoading ? "Saving..." : "Continue"}
        </Button>
      </div>

      {error && (
        <div
          className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg"
          role="alert"
          aria-live="assertive"
          data-testid="mode-error-message"
        >
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">
                {error}
              </p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-2 text-sm font-medium text-red-600 hover:text-red-500 underline"
                  data-testid="mode-retry-button"
                >
                  Try again
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {selectedMode === null && !isLoading && (
        <p className="text-center text-sm text-gray-500 mt-4" role="status">
          Please select a mode to continue
        </p>
      )}
    </div>
  );
}
