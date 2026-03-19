/**
 * DayHoursRow Component
 *
 * Story 3.10: Business Hours Configuration
 *
 * Renders a single day row with toggle and time inputs
 */

import type { DayHours } from '@/types/businessHours';

interface DayHoursRowProps {
  dayName: string;
  hours: DayHours;
  onToggle: (isOpen: boolean) => void;
  onTimeChange: (field: 'openTime' | 'closeTime', value: string) => void;
}

export function DayHoursRow({ dayName, hours, onToggle, onTimeChange }: DayHoursRowProps) {
  const dayKey = dayName.toLowerCase().slice(0, 3);

  const formatTimeForDisplay = (time?: string): string => {
    if (!time) return '';
    return time;
  };

  return (
    <div className="flex items-center gap-4 py-2 px-3 rounded-lg hover:bg-white/[0.03] transition-colors">
      <label className="flex items-center gap-3 min-w-[140px]">
        <input
          type="checkbox"
          checked={hours.isOpen}
          onChange={(e) => onToggle(e.target.checked)}
          data-testid={`day-toggle-${dayKey}`}
          className="w-4 h-4 rounded border-white/20 text-emerald-500 focus:ring-emerald-500/50 bg-white/[0.03]"
          aria-label={`${dayName} is open`}
        />
        <span className={`font-medium ${hours.isOpen ? 'text-white/80' : 'text-white/40'}`}>
          {dayName}
        </span>
      </label>

      <div className="flex items-center gap-2 flex-1">
        {hours.isOpen ? (
          <>
            <input
              type="time"
              value={formatTimeForDisplay(hours.openTime)}
              onChange={(e) => onTimeChange('openTime', e.target.value)}
              data-testid={`open-time-${dayKey}`}
              className="px-2 py-1 border border-white/10 rounded text-sm bg-white/[0.03] text-white focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
              aria-label={`${dayName} opening time`}
            />
            <span className="text-white/50">to</span>
            <input
              type="time"
              value={formatTimeForDisplay(hours.closeTime)}
              onChange={(e) => onTimeChange('closeTime', e.target.value)}
              data-testid={`close-time-${dayKey}`}
              className="px-2 py-1 border border-white/10 rounded text-sm bg-white/[0.03] text-white focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
              aria-label={`${dayName} closing time`}
            />
          </>
        ) : (
          <span className="text-white/40 text-sm italic">Closed</span>
        )}
      </div>
    </div>
  );
}
