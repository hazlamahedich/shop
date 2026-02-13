/** InteractiveTutorial component.

Main tutorial container that orchestrates tutorial flow across multiple pages.
Manages step navigation, progress tracking, and completion.
*/

import * as React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTutorialStore } from "../../stores/tutorialStore";
import { useOnboardingPhaseStore } from "../../stores/onboardingPhaseStore";
import { useHasStoreConnected } from "../../stores/authStore";
import { TutorialProgress } from "./TutorialProgress";
import { TutorialStep } from "./TutorialStep";
import { TutorialCompletion } from "./TutorialCompletion";
import { Card } from "../ui/Card";
import { BotPreview } from "./BotPreview";
import { X, ArrowRight } from "lucide-react";

export interface InteractiveTutorialProps {
  onComplete?: () => void;
  className?: string;
}

// Route mapping for tutorial steps
const STEP_ROUTES: Record<number, string> = {
  1: "/dashboard",
  2: "/dashboard",
  3: "/dashboard",
  4: "/dashboard",
  5: "/personality",      // Bot Personality Selection
  6: "/business-info-faq",  // Business Info & FAQ
  7: "/bot-config",         // Bot Naming
  8: "/bot-config",         // Greetings & Pins
};

// Tutorial step definitions with route navigation
const TUTORIAL_STEPS = [
  {
    step: 1,
    title: "Dashboard Overview",
    description: "Learn how to navigate the dashboard and view customer conversations.",
    actionLabel: null,
    route: "/dashboard",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Your dashboard displays all customer conversations in one place. You can search, filter, and respond to messages directly.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Key Features:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• View all customer conversations</li>
            <li>• Search by customer name or message content</li>
            <li>• Filter by date or status</li>
            <li>• Real-time message updates</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 2,
    title: "Cost Tracking",
    description: "Understand your LLM costs in real-time and set budget caps.",
    actionLabel: null,
    route: "/dashboard",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Monitor your LLM usage and costs in real-time. Set budget caps to avoid surprise bills.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Cost Features:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Real-time token usage tracking</li>
            <li>• Cost estimation per conversation</li>
            <li>• Budget cap configuration</li>
            <li>• Usage alerts and notifications</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 3,
    title: "LLM Provider Switching",
    description: "Learn how to switch between LLM providers (Ollama, OpenAI, etc.).",
    actionLabel: "Go to Provider Settings",
    route: "/settings/provider",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          You can switch between different LLM providers at any time. Choose one that best fits your needs and budget.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Supported Providers:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• <strong>Ollama:</strong> Free, local LLM hosting</li>
            <li>• <strong>OpenAI:</strong> GPT models with excellent quality</li>
            <li>• <strong>Anthropic:</strong> Claude models for nuanced responses</li>
            <li>• <strong>Gemini:</strong> Google's powerful AI models</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 4,
    title: "Test Your Bot",
    description: "Send a test message to your bot and see how it responds.",
    actionLabel: null,
    route: "/dashboard",
    content: <BotPreview />,
  },
  {
    step: 5,
    title: "Bot Personality Selection",
    description: "Choose how your bot should interact with customers (Friendly, Professional, or Enthusiastic).",
    actionLabel: "Configure Personality →",
    route: "/personality",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Choose a personality that best fits your brand. Your bot will use this tone in all responses.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Available Personalities:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• <strong>Friendly:</strong> Casual and warm tone</li>
            <li>• <strong>Professional:</strong> Formal and direct tone</li>
            <li>• <strong>Enthusiastic:</strong> Excited and energetic tone</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 6,
    title: "Business Info & FAQ Configuration",
    description: "Add your business information and create frequently asked questions (FAQ).",
    actionLabel: "Configure Business Info & FAQ →",
    route: "/business-info-faq",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Add your business name, description, and operating hours. Also create FAQ entries for common customer questions.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Business Info Fields:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Business Name</li>
            <li>• Business Description</li>
            <li>• Business Hours</li>
          </ul>
          <h4 className="mt-4 mb-2 font-semibold text-slate-900">FAQ Management:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Add question-answer pairs</li>
            <li>• Edit or delete existing FAQs</li>
            <li>• Reorder FAQ display order</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 7,
    title: "Bot Naming",
    description: "Give your bot a custom name that customers will see.",
    actionLabel: "Configure Bot Name →",
    route: "/bot-config",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Give your bot a custom name. This name will appear in messages and helps customers identify your business.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Tips:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Keep it short (under 30 characters)</li>
            <li>• Make it memorable and relevant to your business</li>
            <li>• Preview how it looks in messages</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    step: 8,
    title: "Smart Greetings & Product Pins",
    description: "Configure personalized greeting templates and highlight products for customers.",
    actionLabel: "Configure Greetings & Pins →",
    route: "/bot-config",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          Set up personalized greeting templates based on your bot personality. Also pin important products that will be highlighted to customers.
        </p>
        <div className="rounded-md bg-slate-100 p-4">
          <h4 className="mb-2 font-semibold text-slate-900">Greeting Features:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Personality-based templates</li>
            <li>• Custom greeting messages</li>
            <li>• Time-sensitive greetings</li>
          </ul>
          <h4 className="mt-4 mb-2 font-semibold text-slate-900">Product Pins:</h4>
          <ul className="space-y-1 text-sm text-slate-700">
            <li>• Highlight up to 8 products</li>
            <li>• Set pin order/priority</li>
            <li>• Show pinned products first</li>
          </ul>
        </div>
      </div>
    ),
  },
];

export function InteractiveTutorial({ onComplete, className = "" }: InteractiveTutorialProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    currentStep,
    completedSteps,
    isStarted,
    isCompleted,
    stepsTotal,
    startTutorial,
    nextStep,
    previousStep,
    jumpToStep,
    completeStep,
    skipTutorial,
    completeTutorial,
    acknowledgeCompletion,
  } = useTutorialStore();

  // Track onboarding phases to detect when user completes actual configuration
  const {
    personalityConfigured,
    businessInfoConfigured,
    botNamed,
    greetingsConfigured,
    pinsConfigured,
  } = useOnboardingPhaseStore();

  // Check if store is connected (pins only required with store)
  const hasStoreConnected = useHasStoreConnected();

  const [isCompleteModalOpen, setIsCompleteModalOpen] = React.useState(false);
  const [isMinimized, setIsMinimized] = React.useState(false);
  const [hasShownCompletion, setHasShownCompletion] = React.useState(false);

  // Auto-start tutorial if not started
  React.useEffect(() => {
    console.log('[InteractiveTutorial] isStarted:', isStarted);
    if (!isStarted && startTutorial) {
      console.log('[InteractiveTutorial] Auto-starting tutorial...');
      startTutorial().catch(err => {
        console.error('[InteractiveTutorial] Failed to auto-start:', err);
      });
    }
  }, [isStarted]);

  // Auto-open modal when tutorial is completed (only once)
  React.useEffect(() => {
    if (isCompleted && !isCompleteModalOpen && !hasShownCompletion) {
      setIsCompleteModalOpen(true);
      setHasShownCompletion(true);
    }
  }, [isCompleted, isCompleteModalOpen, hasShownCompletion]);

  // Auto-navigate to the correct route when step changes
  React.useEffect(() => {
    // Don't auto-navigate if tutorial is completed or modal is open
    if (!isStarted || isCompleted || isCompleteModalOpen) return;

    const targetRoute = STEP_ROUTES[currentStep];
    if (targetRoute && location.pathname !== targetRoute) {
      console.log(`[InteractiveTutorial] Navigating to step ${currentStep}: ${targetRoute}`);
      navigate(targetRoute, { replace: true });
    }
  }, [currentStep, isStarted, isCompleted, isCompleteModalOpen]);

  // Check if current step's onboarding is complete
  // Note: We allow proceeding even if configuration isn't complete
  // The hint below will guide users, but won't block them
  const isStepOnboardingComplete = React.useMemo(() => {
    switch (currentStep) {
      case 5: // Personality
        return !!personalityConfigured;
      case 6: // Business Info
        return !!businessInfoConfigured;
      case 7: // Bot Name
        return !!botNamed;
      case 8: // Greetings & Pins
        if (hasStoreConnected) {
          return !!(greetingsConfigured && pinsConfigured);
        }
        return !!greetingsConfigured;
      default:
        return true;
    }
  }, [currentStep, personalityConfigured, businessInfoConfigured, botNamed, greetingsConfigured, pinsConfigured, hasStoreConnected]);

  // Handle completion
  const handleComplete = React.useCallback(async () => {
    try {
      await completeTutorial();
    } catch (error) {
      console.error('[InteractiveTutorial] Failed to complete tutorial:', error);
    }
    setHasShownCompletion(true);
    setIsCompleteModalOpen(true);
    onComplete?.();
  }, [completeTutorial, onComplete]);

  // Handle next step
  const handleNext = React.useCallback(() => {
    const currentStepData = TUTORIAL_STEPS[currentStep - 1];
    if (currentStepData) {
      completeStep(currentStepData.step);
    }

    if (currentStep < stepsTotal) {
      nextStep();
    } else {
      handleComplete();
    }
  }, [currentStep, stepsTotal, completeStep, nextStep, handleComplete]);

  // Handle action button click (for steps with external navigation)
  const handleAction = React.useCallback(() => {
    const currentStepData = TUTORIAL_STEPS[currentStep - 1];
    if (currentStepData?.route) {
      completeStep(currentStepData.step);
      // Navigate to the route for this step
      navigate(currentStepData.route);
    }
  }, [currentStep, navigate, completeStep]);

  // Handle previous step
  const handlePrevious = React.useCallback(() => {
    previousStep();
  }, [previousStep]);

  // Handle step jump
  const handleJumpToStep = React.useCallback(
    (step: number) => {
      jumpToStep(step);
    },
    [jumpToStep]
  );

  // Keyboard navigation: Arrow keys, Enter, Escape
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          if (currentStep > 1) {
            previousStep();
          }
          break;
        case 'ArrowRight':
        case 'Enter':
          e.preventDefault();
          if (currentStep < stepsTotal) {
            const stepData = TUTORIAL_STEPS[currentStep - 1];
            if (stepData) {
              completeStep(stepData.step);
            }
            nextStep();
          }
          break;
        case 'Escape':
          e.preventDefault();
          // Show skip confirmation
          const confirmed = window.confirm(
            'Are you sure you want to skip the tutorial? You can restart it anytime from the Help menu.'
          );
          if (confirmed) {
            skipTutorial();
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, stepsTotal, previousStep, nextStep, completeStep, skipTutorial]);

  // Screen reader announcement for step changes
  React.useEffect(() => {
    const announcement = `Tutorial Step ${currentStep} of ${stepsTotal}: ${TUTORIAL_STEPS[currentStep - 1]?.title || 'Loading'}`;

    let liveRegion = document.getElementById('tutorial-announcer');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'tutorial-announcer';
      liveRegion.setAttribute('aria-live', 'polite');
      liveRegion.setAttribute('aria-atomic', 'true');
      liveRegion.className = 'sr-only';
      document.body.appendChild(liveRegion);
    }
    liveRegion.textContent = announcement;
  }, [currentStep, stepsTotal]);

  // Responsive content width (applied to inner content, not overlay)
  const contentWidth = React.useMemo(() => {
    if (typeof window === 'undefined') return 'max-w-3xl';
    const width = window.innerWidth;
    if (width < 768) return 'w-[95vw] max-w-lg';
    if (width < 1024) return 'w-[85vw] max-w-2xl';
    return 'w-[75vw] max-w-3xl';
  }, []);

  const currentStepData = TUTORIAL_STEPS[currentStep - 1];
  const isStepCompleted = completedSteps.includes(`step-${currentStep}`);

  if (!isStarted) {
    return null;
  }

  return (
    <div className="interactive-tutorial">
      {/* Inner content container with proper width */}
      <div className={`interactive-tutorial-content ${contentWidth} ${className}`}>
        {/* Tutorial header with minimize button */}
        <div className="mb-6 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h2 className="text-2xl font-semibold text-slate-900">Interactive Tutorial</h2>
              <p className="text-slate-600">
                Follow these steps to learn how to use your shopping bot dashboard.
              </p>
            </div>
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              aria-label={isMinimized ? "Expand tutorial" : "Minimize tutorial"}
            >
              <ArrowRight className={`w-5 h-5 transition-transform ${isMinimized ? 'rotate-90deg' : '-rotate-90deg'}`} />
            </button>
          </div>

          {/* Tutorial Progress - always visible */}
          <TutorialProgress
            currentStep={currentStep}
            stepsTotal={stepsTotal}
          />

          {/* Step navigation dots - hide when minimized */}
          {!isMinimized && (
            <div className="flex justify-center gap-2" role="tablist" aria-label="Tutorial steps">
              {TUTORIAL_STEPS.map((step) => {
                const isCompleted = completedSteps.includes(`step-${step.step}`);
                const isCurrent = step.step === currentStep;

                return (
                  <button
                    key={step.step}
                    onClick={() => handleJumpToStep(step.step)}
                    className={`h-3 w-3 rounded-full transition-all ${
                      isCurrent
                        ? "h-4 w-4 bg-blue-600"
                        : isCompleted
                        ? "bg-green-500"
                        : "bg-slate-300"
                    }`}
                    aria-label={`Go to step ${step.step}: ${step.title}`}
                    aria-selected={isCurrent}
                    role="tab"
                    type="button"
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Current step content */}
        {isMinimized || !currentStepData ? (
          <div className="bg-white rounded-lg p-6 text-center">
            <p className="text-slate-600">Loading step...</p>
          </div>
        ) : (
          <TutorialStep
            step={{
              ...currentStepData,
              onAction: currentStepData.actionLabel ? handleAction : undefined,
            }}
            isCurrentStep={true}
            isCompleted={isStepCompleted}
            onNext={handleNext}
            onPrevious={handlePrevious}
            onSkip={skipTutorial}
            hasNextStep={currentStep < stepsTotal}
            hasPreviousStep={currentStep > 1}
            canGoNext={true}
          />
        )}

        {/* Onboarding completion hint for steps 5-8 */}
        {!isMinimized && currentStep >= 5 && currentStep <= 8 && !isStepOnboardingComplete && (
          <div className="tutorial-onboarding-hint mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Recommended:</strong>{' '}
              {currentStep === 5 && 'Select and save a personality to customize your bot\'s tone.'}
              {currentStep === 6 && 'Add your business info to help the bot answer customer questions.'}
              {currentStep === 7 && 'Give your bot a name to personalize customer interactions.'}
              {currentStep === 8 && (
                <>
                  Configure your greeting template
                  {hasStoreConnected && ' and pin featured products'}
                  .
                </>
              )}
              {' '}You can configure this later from the Settings menu.
            </p>
          </div>
        )}

        {/* Completion modal - render regardless of isCompleted for error recovery */}
        {(isCompleted || isCompleteModalOpen) && (
          <TutorialCompletion
            isOpen={isCompleteModalOpen}
            onClose={() => {
              setIsCompleteModalOpen(false);
              setHasShownCompletion(true);
              acknowledgeCompletion();
              navigate('/dashboard', { replace: true });
            }}
            completedSteps={completedSteps}
            onNextStep={() => {
              setIsCompleteModalOpen(false);
              setHasShownCompletion(true);
              acknowledgeCompletion();
              onComplete?.();
              navigate('/dashboard', { replace: true });
            }}
            nextStepLabel="Go to Dashboard"
          />
        )}
      </div>
    </div>
  );
}
