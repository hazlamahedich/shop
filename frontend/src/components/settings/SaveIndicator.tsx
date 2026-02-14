/**
 * SaveIndicator Component
 *
 * Story 3.10: Business Hours Configuration
 *
 * Shows saving/saved status for auto-save
 */

interface SaveIndicatorProps {
  saving: boolean;
  lastSaved: Date | null;
}

export function SaveIndicator({ saving, lastSaved }: SaveIndicatorProps) {
  if (saving) {
    return (
      <div data-testid="save-indicator" className="flex items-center gap-2 text-sm text-slate-500">
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
        <span>Saving...</span>
      </div>
    );
  }

  if (lastSaved) {
    const timeStr = lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return (
      <div data-testid="save-indicator" className="flex items-center gap-2 text-sm text-green-600">
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span>Saved at {timeStr}</span>
      </div>
    );
  }

  return null;
}
