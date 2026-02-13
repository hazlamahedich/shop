/** TutorialPrompt component.

Subtle banner shown to merchants who haven't completed the tutorial.
Displays on /bot-config and /dashboard when tutorial is incomplete.
Supports "Remind me later" temporary dismissal instead of permanent close.
*/

import * as React from 'react';
import { useOnboardingPhaseStore } from '../../stores/onboardingPhaseStore';
import { useTutorialStore } from '../../stores/tutorialStore';
import { Button } from '../ui/Button';
import { X, Clock } from 'lucide-react';

export interface TutorialPromptProps {
  className?: string;
}

/**
 * Check if tutorial prompt should be shown.
 *
 * Shows if:
 * - Tutorial hasn't been completed
 * - Tutorial hasn't been skipped
 * - Tutorial hasn't started yet
 */
function shouldShowPrompt(
  isTutorialStarted: boolean,
  isTutorialCompleted: boolean,
  isTutorialSkipped: boolean,
  shouldShowTutorial: boolean
): boolean {
  // Show prompt for users who haven't finished or skipped tutorial
  // Note: shouldShowTutorial indicates bot config is complete
  // For first-time users who haven't configured anything, we still want to guide them
  return !isTutorialCompleted && !isTutorialSkipped && !isTutorialStarted;
}

export function TutorialPrompt({ className = '' }: TutorialPromptProps) {
  const { isStarted, isCompleted: isTutorialCompleted, isSkipped: isTutorialSkipped, startTutorial } = useTutorialStore();
  const { checkOnboardingStatus } = useOnboardingPhaseStore();
  const onboardingStatus = checkOnboardingStatus();

  const [isDismissed, setIsDismissed] = React.useState(false);
  const [dismissalTime, setDismissalTime] = React.useState<Date | null>(null);

  // Check dismissal state on mount - MUST be before any early returns (React hooks rule)
  React.useEffect(() => {
    // Check for temporary dismissal (has 24 hour timeout?)
    const dismissedData = localStorage.getItem('shop_tutorial_prompt_dismissed');
    if (dismissedData) {
      const { dismissed, dismissedAt } = JSON.parse(dismissedData);
      if (dismissed && dismissedAt) {
        const now = new Date();
        const dismissedAtDate = new Date(dismissedAt);
        const hoursSinceDismissal = (now.getTime() - dismissedAtDate.getTime()) / (1000 * 60 * 60);

        // If less than 24 hours, keep dismissed
        if (hoursSinceDismissal < 24) {
          setIsDismissed(true);

          // Set timeout to show again
          const remainingTime = 24 - hoursSinceDismissal;
          setTimeout(() => {
            setIsDismissed(false);
            setDismissalTime(null);
            localStorage.removeItem('shop_tutorial_prompt_dismissed');
          }, remainingTime * 60 * 60 * 1000);
        } else {
          // More than 24 hours passed, clear and show
          setIsDismissed(false);
          setDismissalTime(null);
          localStorage.removeItem('shop_tutorial_prompt_dismissed');
        }
      }
    }

    // Check for session dismissal
    const sessionDismissed = sessionStorage.getItem('shop_tutorial_prompt_dismissed_session');
    if (sessionDismissed === 'true') {
      setIsDismissed(true);
    }
  }, []);

  // Don't show if dismissed or tutorial already started
  if (isDismissed || isStarted) {
    return null;
  }

  // Check if we should show the prompt
  const showPrompt = shouldShowPrompt(
    isStarted,
    isTutorialCompleted,
    isTutorialSkipped,
    onboardingStatus.shouldShowTutorial
  );

  if (!showPrompt) {
    return null;
  }

  const handleStart = () => {
    startTutorial();
  };

  /**
   * Handle temporary dismissal (Remind me later).
   * Sets a timeout to show the prompt again after 24 hours.
   */
  const handleRemindMeLater = () => {
    const now = new Date();
    setDismissalTime(now);

    // Store dismissal with timestamp in localStorage
    localStorage.setItem('shop_tutorial_prompt_dismissed', JSON.stringify({
      dismissed: true,
      dismissedAt: now.toISOString(),
    }));

    setIsDismissed(true);

    // Set timeout to show prompt again after 24 hours
    const reminderTime = new Date(now.getTime() + 24 * 60 * 60 * 1000); // 24 hours
    setTimeout(() => {
      setIsDismissed(false);
      setDismissalTime(null);
      localStorage.removeItem('shop_tutorial_prompt_dismissed');
    }, 24 * 60 * 60 * 1000);
  };

  /**
   * Handle permanent dismissal.
   * User explicitly chose to dismiss - don't show again this session.
   */
  const handleDismiss = () => {
    const now = new Date();
    setDismissalTime(now);

    // Store permanent dismissal for current session
    sessionStorage.setItem('shop_tutorial_prompt_dismissed_session', 'true');

    setIsDismissed(true);
  };

  // Determine if remind me later is active (has a timeout set)
  const isRemindMeLaterActive = dismissalTime !== null;

  return (
    <div
      className={`tutorial-prompt bg-blue-50 border-blue-200 border rounded-lg p-4 flex items-start gap-3 ${className}`}
      role="alert"
      aria-live="polite"
    >
      <div className="flex-1">
        <p className="text-sm font-medium text-blue-900 mb-1">
          Complete the interactive tutorial to finish setting up your bot
        </p>
        <p className="text-xs text-blue-700">
          Learn how to use the dashboard, configure your bot personality, and test responses.
        </p>
        {isRemindMeLaterActive && (
          <p className="text-xs text-blue-600 mt-1 flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Showing again in 24 hours
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={handleStart}
          aria-label="Start interactive tutorial"
        >
          Start Tutorial
        </Button>

        <button
          type="button"
          onClick={handleRemindMeLater}
          className="text-blue-600 hover:text-blue-700 font-medium text-sm px-3 py-1 rounded transition-colors"
          aria-label="Remind me later"
        >
          Remind me later
        </button>

        <button
          type="button"
          onClick={handleDismiss}
          className="text-slate-400 hover:text-slate-600 ml-2 p-1"
          aria-label="Dismiss tutorial prompt"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
