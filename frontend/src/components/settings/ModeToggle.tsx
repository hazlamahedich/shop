/**
 * Mode Toggle Component
 *
 * Story 8.7: Frontend - Settings Mode Toggle
 *
 * Displays onboarding mode selection with descriptions and feature lists.
 * Supports switching between "General Chatbot" and "E-commerce Assistant" modes.
 */

import React from 'react';
import { Bot, ShoppingBag, Check } from 'lucide-react';
import type { OnboardingMode } from '../../types/onboarding';
import { cn } from '../../lib/utils';

export interface ModeToggleProps {
  currentMode: OnboardingMode;
  onModeChange: (mode: OnboardingMode) => void;
  disabled?: boolean;
  loading?: boolean;
  fetching?: boolean;
}

interface ModeOption {
  value: OnboardingMode;
  label: string;
  icon: React.ReactNode;
  description: string;
  features: string[];
}

const MODE_OPTIONS: ModeOption[] = [
  {
    value: 'general',
    label: 'General Chatbot',
    icon: <Bot className="w-5 h-5" />,
    description: 'Customer support, FAQ, knowledge base Q&A',
    features: [
      'Knowledge base integration',
      'FAQ and support questions',
      'Custom document uploads',
      'General Q&A assistance',
    ],
  },
  {
    value: 'ecommerce',
    label: 'E-commerce Assistant',
    icon: <ShoppingBag className="w-5 h-5" />,
    description: 'Product search, cart, checkout, order tracking',
    features: [
      'Product search and recommendations',
      'Shopping cart management',
      'Shopify checkout integration',
      'Order tracking and updates',
    ],
  },
];

export function ModeToggle({
  currentMode,
  onModeChange,
  disabled = false,
  loading = false,
  fetching = false,
}: ModeToggleProps) {
  return (
    <div className="space-y-4">
      {fetching && (
        <div className="flex items-center justify-center py-4">
          <span className="animate-spin mr-2">⏳</span>
           <span className="text-sm text-white/60">Loading mode settings...</span>
        </div>
      )}
      <div className={`grid grid-cols-1 md:grid-cols-2 gap-4 ${fetching ? 'opacity-50' : ''}`}>
        {MODE_OPTIONS.map((option) => {
          const isSelected = currentMode === option.value;
          const isDisabled = disabled || loading;

          return (
            <button
              key={option.value}
              type="button"
              onClick={() => !isSelected && onModeChange(option.value)}
              disabled={isDisabled || isSelected}
              className={cn(
                'relative p-4 rounded-lg border-2 text-left transition-all',
                'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
                isSelected
                  ? 'border-emerald-500/50 bg-emerald-500/10'
                  : 'border-white/10 bg-white/[0.03] hover:border-white/20 hover:bg-white/[0.05]',
                isDisabled && 'opacity-50 cursor-not-allowed'
              )}
              aria-pressed={isSelected}
              aria-label={`${option.label} mode${isSelected ? ' (currently selected)' : ''}`}
            >
              {/* Selected indicator */}
              {isSelected && (
                <div className="absolute top-3 right-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center">
                    <Check className="w-4 h-4 text-white" />
                  </div>
                </div>
              )}

              {/* Header */}
              <div className="flex items-start gap-3 mb-3">
                <div
                  className={cn(
                    'p-2 rounded-lg',
                    isSelected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-white/[0.03] text-white/60'
                  )}
                >
                  {option.icon}
                </div>
                <div className="flex-1">
                  <h3
                    className={cn(
                      'font-medium text-sm',
                      isSelected ? 'text-emerald-400' : 'text-white/80'
                    )}
                  >
                    {option.label}
                  </h3>
                  <p className="text-xs text-white/50 mt-0.5">{option.description}</p>
                </div>
              </div>

              {/* Features */}
              <ul className="space-y-1.5">
                {option.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-2 text-xs text-white/50">
                    <span className={cn(
                      'mt-0.5',
                      isSelected ? 'text-emerald-400' : 'text-white/40'
                    )}>•</span>
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
            </button>
          );
        })}
      </div>

      {/* Current mode indicator */}
      <div className="flex items-center justify-center pt-2">
         <p className="text-sm text-white/60">
           Current mode: <span className="font-medium text-white/80">
             {currentMode === 'general' ? 'General Chatbot' : 'E-commerce Assistant'}
           </span>
         </p>
      </div>
    </div>
  );
}
