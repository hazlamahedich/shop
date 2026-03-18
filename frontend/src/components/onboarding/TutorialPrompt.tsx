/** TutorialPrompt component.

Subtle banner shown to merchants who haven't completed the tutorial.
Displays on /bot-config and /dashboard when tutorial is incomplete.
Supports "Remind me later" temporary dismissal instead of permanent close.
*/

import * as React from 'react';

import { useTutorialStore } from '../../stores/tutorialStore';
import { Button } from '../ui/Button';
import { X, Clock, Sparkles } from 'lucide-react';

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
  isTutorialSkipped: boolean
): boolean {
  // Show prompt for users who haven't finished or skipped tutorial
  // Note: shouldShowTutorial indicates bot config is complete
  // For first-time users who haven't configured anything, we still want to guide them
  return !isTutorialCompleted && !isTutorialSkipped && !isTutorialStarted;
}

export function TutorialPrompt({ className = '' }: TutorialPromptProps) {
  const { isStarted, isCompleted: isTutorialCompleted, isSkipped: isTutorialSkipped, startTutorial } = useTutorialStore();


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
    isTutorialSkipped
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
      className={`tutorial-prompt relative overflow-hidden bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-6 flex flex-col sm:flex-row items-center sm:items-start gap-4 transition-all duration-300 hover:border-[var(--mantis-glow)]/30 group ${className}`}
      role="alert"
      aria-live="polite"
    >
      <div className="absolute top-0 left-0 p-12 bg-[var(--mantis-glow)]/5 blur-3xl rounded-full -translate-x-1/2 -translate-y-1/2 group-hover:bg-[var(--mantis-glow)]/10 transition-colors" />
      
      <div className="relative flex-1 text-center sm:text-left">
        <p className="text-base font-bold text-white mb-1 flex items-center justify-center sm:justify-start gap-2">
          <Sparkles className="h-4 w-4 text-[var(--mantis-glow)]" />
          Neural Onboarding Pending
        </p>
        <p className="text-sm text-white/50 leading-relaxed max-w-xl">
          Initialize the interactive deployment protocol to finalize your neural assistant configuration. 
          Learn to navigate the dashboard, refine behavior modules, and validate response accuracy.
        </p>
        {isRemindMeLaterActive && (
          <p className="text-[10px] font-bold text-[var(--mantis-glow)]/60 mt-3 flex items-center justify-center sm:justify-start gap-1.5 uppercase tracking-widest">
            <Clock className="h-3 w-3" />
            Re-activation scheduled: T-24:00:00
          </p>
        )}
      </div>

      <div className="relative flex items-center gap-3">
        <Button
          size="sm"
          onClick={handleStart}
          aria-label="Start interactive tutorial"
          className="bg-[var(--mantis-glow)] hover:bg-[var(--mantis-glow)]/80 text-white border-transparent shadow-[0_0_15px_rgba(34,197,94,0.3)] shadow-lg px-6"
        >
          Initialize Protocol
        </Button>

        <button
          type="button"
          onClick={handleRemindMeLater}
          className="text-white/40 hover:text-white font-bold text-xs uppercase tracking-widest px-4 py-2 rounded-xl border border-white/5 hover:bg-white/5 transition-all"
          aria-label="Remind me later"
        >
          Delay Sync
        </button>

        <button
          type="button"
          onClick={handleDismiss}
          className="text-white/20 hover:text-white p-2 rounded-full hover:bg-white/5 transition-all"
          aria-label="Terminate prompt"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
