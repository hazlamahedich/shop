/** InteractiveTutorial component.

Main tutorial container that orchestrates the tutorial flow.
Manages step navigation, progress tracking, and completion.
*/

import * as React from "react";
import { useTutorialStore } from "../../stores/tutorialStore";
import { TutorialProgress } from "./TutorialProgress";
import { TutorialStep } from "./TutorialStep";
import { TutorialCompletion } from "./TutorialCompletion";
import { Card } from "../ui/Card";
import { BotPreview } from "./BotPreview";

export interface InteractiveTutorialProps {
  onComplete?: () => void;
  className?: string;
}

// Tutorial step definitions
const TUTORIAL_STEPS = [
  {
    step: 1,
    title: "Dashboard Overview",
    description: "Learn how to navigate the dashboard and view customer conversations",
    actionLabel: "View Conversation List",
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
    description: "Understand your LLM costs in real-time and set budget caps",
    actionLabel: "View Cost Tracking Panel",
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
    description: "Learn how to switch between LLM providers (Ollama, OpenAI, etc.)",
    actionLabel: "View Provider Settings",
    content: (
      <div className="space-y-4">
        <p className="text-slate-700">
          You can switch between different LLM providers at any time. Choose the one that best fits your needs and budget.
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
    description: "Send a test message to your bot and see how it responds",
    actionLabel: "Test Bot with Preview Pane",
    content: <BotPreview />,
  },
];

export function InteractiveTutorial({ onComplete, className = "" }: InteractiveTutorialProps) {
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
  } = useTutorialStore();

  const [isCompleteModalOpen, setIsCompleteModalOpen] = React.useState(false);

  // Auto-start tutorial if not started
  React.useEffect(() => {
    if (!isStarted) {
      startTutorial();
    }
  }, [isStarted, startTutorial]);

  // Auto-open modal when tutorial is completed
  React.useEffect(() => {
    if (isCompleted && !isCompleteModalOpen) {
      setIsCompleteModalOpen(true);
    }
  }, [isCompleted, isCompleteModalOpen]);

  // Handle completion
  const handleComplete = React.useCallback(async () => {
    await completeTutorial();
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

  const currentStepData = TUTORIAL_STEPS[currentStep - 1];
  const isStepCompleted = completedSteps.includes(`step-${currentStep}`);

  if (!isStarted) {
    return null;
  }

  return (
    <div className={`interactive-tutorial ${className}`}>
      {/* Tutorial header */}
      <div className="mb-6 space-y-4">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Interactive Tutorial</h2>
          <p className="text-slate-600">
            Follow these steps to learn how to use your shopping bot dashboard.
          </p>
        </div>

        <TutorialProgress
          currentStep={currentStep}
          stepsTotal={stepsTotal}
        />

        {/* Step navigation dots */}
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
      </div>

      {/* Current step content */}
      {currentStepData && (
        <TutorialStep
          step={{
            ...currentStepData,
            onAction: () => handleJumpToStep(currentStep),
          }}
          isCurrentStep={true}
          isCompleted={isStepCompleted}
          onNext={handleNext}
          onPrevious={handlePrevious}
          onSkip={skipTutorial}
          hasNextStep={currentStep < stepsTotal}
          hasPreviousStep={currentStep > 1}
        />
      )}

      {/* Completion modal */}
      {isCompleted && (
        <TutorialCompletion
          isOpen={isCompleteModalOpen}
          onClose={() => setIsCompleteModalOpen(false)}
          completedSteps={completedSteps}
          onNextStep={onComplete}
          nextStepLabel="Go to Dashboard"
        />
      )}
    </div>
  );
}
