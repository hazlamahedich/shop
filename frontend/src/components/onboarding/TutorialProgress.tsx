/** TutorialProgress component.

Visual progress indicator showing current step and total steps.
Displays "Step X of Y" with a progress bar for accessibility.
*/

import * as React from "react";
import { Progress } from "../ui/Progress";

export interface TutorialProgressProps {
  currentStep: number;
  stepsTotal: number;
  className?: string;
}

export function TutorialProgress({
  currentStep,
  stepsTotal,
  className = "",
}: TutorialProgressProps) {
  const progressPercentage = (currentStep / stepsTotal) * 100;

  return (
    <div className={`tutorial-progress space-y-2 ${className}`}>
      {/* Text indicator for accessibility */}
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700">
          Step {currentStep} of {stepsTotal}
        </span>
        <span className="text-slate-600" aria-live="polite">
          {Math.round(progressPercentage)}% complete
        </span>
      </div>

      {/* Visual progress bar */}
      <Progress
        value={currentStep}
        max={stepsTotal}
        className="h-2"
      />

      {/* Screen reader only detailed progress */}
      <span className="sr-only" aria-live="polite">
        Tutorial progress: {currentStep} out of {stepsTotal} steps completed
      </span>
    </div>
  );
}
