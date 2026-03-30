/**
 * Mode Selection Component - Choose Your Assistant Type
 *
 * Features:
 * - Plain language (no sci-fi jargon)
 * - Live preview panel showing interactive demo
 * - Clear time estimates
 * - Accessible keyboard navigation
 * - Smooth hover animations
 * - Context for each option
 */

import * as React from "react";
import { motion } from "framer-motion";
import { Bot, ShoppingCart, Check, Cpu, Zap, ArrowRight, Clock, Info } from "lucide-react";
import { OnboardingMode } from "../../types/onboarding";
import { LivePreviewPanel } from "./LivePreviewPanel";

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
  icon: React.ElementType;
  title: string;
  description: string;
  subtitle?: string;
  features: string[];
  timeEstimate?: string;
}

const MODES: ModeCardData[] = [
  {
    mode: "general",
    icon: Bot,
    title: "Customer Chat Assistant",
    description: "Answer customer questions automatically 24/7.",
    subtitle: "Best for: Customer support, FAQs, knowledge base",
    features: ["Answer common questions", "Provide product info", "Handle customer inquiries"],
    timeEstimate: "~25 minutes",
  },
  {
    mode: "ecommerce",
    icon: ShoppingCart,
    title: "Store Assistant with Shopping",
    description: "Let customers browse and buy products directly in chat.",
    subtitle: "Best for: E-commerce stores, product catalogs",
    features: ["Shopify product sync", "Cart in Messenger", "Real-time inventory"],
    timeEstimate: "~35 minutes",
  },
];

const DEBOUNCE_MS = 150;

export function ModeSelection({
  selectedMode,
  onModeSelect,
  onContinue,
  isLoading = false,
  error = null,
  onRetry,
}: ModeSelectionProps): React.ReactElement {
  const debounceRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleModeSelect = React.useCallback((mode: OnboardingMode) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      onModeSelect(mode);
    }, DEBOUNCE_MS);
  }, [onModeSelect]);

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
      className="w-full max-w-6xl mx-auto space-y-8"
      data-testid="mode-selection"
    >
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-xs font-bold uppercase tracking-wider text-emerald-400">
          Step 1 of 4 • Choose Your Assistant Type
        </div>
        <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">
          What do you need help with?
        </h2>
        <p className="text-white/70 text-sm md:text-base max-w-2xl mx-auto leading-relaxed">
          Choose the type of assistant that fits your business. You can always change this later.
        </p>
      </div>

      {/* Main Content: Cards + Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Mode Cards */}
        <div className="space-y-6">
          {MODES.map((modeData) => {
            const isSelected = selectedMode === modeData.mode;
            const Icon = modeData.icon;

            return (
              <motion.div
                key={modeData.mode}
                whileHover={{ y: -4, scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                transition={{ duration: 0.2 }}
              >
                <div
                  role="button"
                  tabIndex={0}
                  aria-pressed={isSelected}
                  onKeyDown={(e) => handleKeyDown(e, modeData.mode)}
                  onClick={() => handleModeSelect(modeData.mode)}
                  className={`
                    relative p-6 rounded-2xl border-2 cursor-pointer transition-all duration-300
                    ${isSelected
                      ? "border-emerald-500 bg-emerald-500/10 shadow-[0_0_30px_rgba(16,185,129,0.2)]"
                      : "border-white/10 bg-white/5 hover:border-emerald-500/30 hover:bg-white/10"
                    }
                    outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-background
                  `}
                  data-testid={`mode-card-${modeData.mode}`}
                >
                  {/* Selection Badge */}
                  {isSelected && (
                    <div className="absolute top-4 right-4 flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500 text-black">
                      <Check size={14} strokeWidth={4} />
                    </div>
                  )}

                  <div className="flex gap-4">
                    {/* Icon */}
                    <div className={`
                      w-16 h-16 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-300
                      ${isSelected
                        ? "bg-emerald-500 text-black"
                        : "bg-white/10 text-white/40"
                      }
                    `}>
                      <Icon size={28} strokeWidth={2} />
                    </div>

                    {/* Content */}
                    <div className="flex-1 space-y-2">
                      <div>
                        <h3 className={`text-lg font-black tracking-tight transition-colors ${isSelected ? "text-white" : "text-white/70"}`}>
                          {modeData.title}
                        </h3>
                        {modeData.subtitle && (
                          <p className="text-xs text-white/50 mt-1">{modeData.subtitle}</p>
                        )}
                      </div>

                      <p className={`text-sm leading-relaxed transition-colors ${isSelected ? "text-white/80" : "text-white/50"}`}>
                        {modeData.description}
                      </p>

                      {/* Features */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        {modeData.features.map((feature, idx) => (
                          <span
                            key={idx}
                            className={`
                              inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold
                              ${isSelected
                                ? "bg-emerald-500/20 text-emerald-300"
                                : "bg-white/5 text-white/40"
                              }
                            `}
                          >
                            <Check size={12} />
                            {feature}
                          </span>
                        ))}
                      </div>

                      {/* Time Estimate */}
                      {modeData.timeEstimate && (
                        <div className="flex items-center gap-1.5 text-xs text-white/40 pt-2">
                          <Clock size={14} />
                          <span>Setup time: {modeData.timeEstimate}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Live Preview Panel */}
        <div className="lg:sticky lg:top-8">
          <LivePreviewPanel mode={selectedMode} />
        </div>
      </div>

      {/* Continue Button */}
      <div className="flex flex-col items-center gap-4 pt-8">
        <button
          onClick={onContinue}
          disabled={selectedMode === null || isLoading}
          className={`
            h-14 px-12 rounded-xl font-bold text-sm uppercase tracking-wide transition-all duration-300 relative overflow-hidden group
            ${selectedMode !== null && !isLoading
              ? "bg-emerald-500 text-black shadow-lg hover:bg-emerald-400 hover:shadow-xl hover:-translate-y-0.5"
              : "bg-white/5 border border-white/10 text-white/30 cursor-not-allowed"
            }
            flex items-center gap-2
          `}
        >
          <span className="relative z-10 flex items-center gap-2">
            {isLoading ? (
              <>
                <Zap size={16} className="animate-spin" />
                Setting up your assistant...
              </>
            ) : (
              <>
                Continue
                <ArrowRight size={16} />
              </>
            )}
          </span>
        </button>

        {/* Help Text */}
        {selectedMode === null && !isLoading && (
          <div className="flex items-center gap-2 text-xs text-white/40">
            <Info size={14} />
            <span>Select an option above to continue</span>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div
            className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-4 max-w-lg"
            role="alert"
          >
            <div className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center text-red-400 flex-shrink-0">
              <Cpu size={16} />
            </div>
            <div className="flex-1">
              <p className="text-sm font-bold text-red-400">Connection failed</p>
              <p className="text-xs text-red-300/80">{error}</p>
            </div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="px-4 py-2 rounded-lg bg-red-500/20 border border-red-500/30 text-red-400 font-bold text-xs uppercase hover:bg-red-500 hover:text-white transition-all"
              >
                Try again
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
