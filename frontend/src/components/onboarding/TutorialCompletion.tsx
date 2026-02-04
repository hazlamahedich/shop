/** TutorialCompletion component.

Celebration modal shown when tutorial is completed.
Displays completion message and optional next steps.
*/

import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";

export interface TutorialCompletionProps {
  isOpen: boolean;
  onClose: () => void;
  onNextStep?: () => void;
  nextStepLabel?: string;
  completedSteps: string[];
  className?: string;
}

export function TutorialCompletion({
  isOpen,
  onClose,
  onNextStep,
  nextStepLabel = "Go to Dashboard",
  completedSteps,
  className = "",
}: TutorialCompletionProps) {
  // Announce completion to screen readers
  React.useEffect(() => {
    if (isOpen) {
      // Announcement will be handled by the dialog's aria-live region
    }
  }, [isOpen]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className="sm:max-w-md"
        aria-describedby="tutorial-completion-description"
      >
        <DialogHeader>
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <svg
              className="h-10 w-10 text-green-600"
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
          </div>
          <DialogTitle className="text-center text-xl">
            Tutorial Complete!
          </DialogTitle>
          <DialogDescription
            id="tutorial-completion-description"
            className="text-center"
          >
            Congratulations! You've completed all {completedSteps.length} tutorial steps.
            Your bot is now ready to help customers shop.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Completion summary */}
          <Card className="bg-slate-50">
            <div className="p-4">
              <h3 className="mb-2 font-semibold text-slate-900">What you've learned:</h3>
              <ul className="space-y-1 text-sm text-slate-700">
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Dashboard navigation and conversation list
                </li>
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Cost tracking and budget configuration
                </li>
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  LLM provider switching
                </li>
                <li className="flex items-center gap-2">
                  <svg
                    className="h-4 w-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Bot testing with preview pane
                </li>
              </ul>
            </div>
          </Card>
        </div>

        <DialogFooter className="flex-col sm:flex-col">
          {onNextStep && (
            <Button
              onClick={onNextStep}
              className="w-full sm:w-full"
              size="lg"
              aria-label={nextStepLabel}
            >
              {nextStepLabel}
            </Button>
          )}
          <Button
            variant="ghost"
            onClick={onClose}
            className="w-full sm:w-full"
            aria-label="Close completion dialog"
          >
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
