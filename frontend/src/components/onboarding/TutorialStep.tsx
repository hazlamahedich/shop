/** TutorialStep component.

Individual step component with title, description, interactive element, and navigation.
Accessible with keyboard navigation and screen reader support.
*/

import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import { Button } from "../ui/Button";
import { ArrowRight } from "lucide-react";

export interface TutorialStepData {
  step: number;
  title: string;
  description: string;
  content?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  route?: string; // New: route for navigation
}

export interface TutorialStepProps {
  step: TutorialStepData;
  isCurrentStep: boolean;
  isCompleted: boolean;
  onNext?: () => void;
  onPrevious?: () => void;
  onSkip?: () => void;
  hasNextStep: boolean;
  hasPreviousStep: boolean;
  canGoNext?: boolean;
  className?: string;
}

export function TutorialStep({
  step,
  isCurrentStep,
  isCompleted,
  onNext,
  onPrevious,
  onSkip,
  hasNextStep,
  hasPreviousStep,
  canGoNext,
  className = "",
}: TutorialStepProps) {
  const stepRef = React.useRef<HTMLDivElement>(null);

  // Announce step changes to screen readers
  React.useEffect(() => {
    if (isCurrentStep && stepRef.current) {
      stepRef.current.focus();
    }
  }, [isCurrentStep]);

  if (!isCurrentStep) {
    return null;
  }

  return (
    <div
      ref={stepRef}
      className={`tutorial-step ${className}`}
      tabIndex={-1}
      aria-label={`Tutorial step ${step.step}: ${step.title}`}
    >
      <Card className="border-2 border-blue-200 bg-blue-50/30">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-xl">{step.title}</CardTitle>
              <p className="text-sm text-slate-600">{step.description}</p>
            </div>
            <div
              className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white"
              aria-hidden="true"
            >
              {step.step}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Interactive content */}
          {step.content && (
            <div className="min-h-[200px] rounded-md border border-slate-200 bg-white p-4">
              {step.content}
            </div>
          )}

          {/* Step action button with navigation */}
          {step.onAction && step.actionLabel && step.route && (
            <Button
              onClick={step.onAction}
              variant="outline"
              className="w-full group"
            >
              <span className="flex items-center justify-center gap-2">
                {step.actionLabel}
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </span>
            </Button>
          )}

          {/* Navigation buttons */}
          <div className="flex items-center justify-between pt-4">
            <div className="flex gap-2">
              {hasPreviousStep && (
                <Button
                  onClick={onPrevious}
                  variant="ghost"
                  size="sm"
                  aria-label="Go to previous step"
                >
                  Previous
                </Button>
              )}
            </div>

            <div className="flex gap-2">
              {onSkip && (
                <Button
                  onClick={onSkip}
                  variant="ghost"
                  size="sm"
                  className="text-slate-600"
                  aria-label="Skip tutorial"
                >
                  Skip Tutorial
                </Button>
              )}

              {hasNextStep ? (
                <Button
                  onClick={onNext}
                  size="sm"
                  disabled={!canGoNext}
                  aria-label="Go to next step"
                >
                  Next
                </Button>
              ) : (
                <Button
                  onClick={onNext}
                  size="sm"
                  variant="default"
                  className="bg-green-600 hover:bg-green-700"
                  aria-label="Complete tutorial"
                >
                  Complete
                </Button>
              )}
            </div>
          </div>

          {/* Step completion indicator */}
          {isCompleted && (
            <div
              className="flex items-center gap-2 text-sm text-green-600"
              role="status"
              aria-live="polite"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
              <span>Step completed</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
