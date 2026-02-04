/** TutorialSkip component.

Skip button with confirmation dialog to prevent accidental skips.
Accessible with keyboard navigation and confirmation.
*/

import * as React from "react";
import { Button } from "../ui/Button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/Dialog";

export interface TutorialSkipProps {
  onSkip: () => void;
  disabled?: boolean;
  className?: string;
}

export function TutorialSkip({ onSkip, disabled = false, className = "" }: TutorialSkipProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  const handleSkip = () => {
    setIsOpen(false);
    onSkip();
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          disabled={disabled}
          className={className}
          aria-label="Skip tutorial"
        >
          Skip Tutorial
        </Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Skip Tutorial?</DialogTitle>
          <DialogDescription>
            Are you sure you want to skip the interactive tutorial? You can always access it later from the Help menu.
          </DialogDescription>
        </DialogHeader>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => setIsOpen(false)}
            aria-label="Cancel skip tutorial"
          >
            Cancel
          </Button>
          <Button
            variant="default"
            onClick={handleSkip}
            className="bg-red-600 hover:bg-red-700"
            aria-label="Confirm skip tutorial"
          >
            Yes, Skip Tutorial
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
