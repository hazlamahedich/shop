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
    <div className="flex items-center gap-4 py-3 px-4 hover:bg-[#1f1f25] transition-colors group/row">
      <label className="flex items-center gap-3 min-w-[140px] cursor-pointer">
        <div className="relative flex items-center justify-center">
          <input
            type="checkbox"
            checked={hours.isOpen}
            onChange={(e) => onToggle(e.target.checked)}
            data-testid={`day-toggle-${dayKey}`}
            className="peer sr-only"
            aria-label={`${dayName} is open`}
          />
          <div className="w-4 h-4 rounded border-2 border-[#3a4a46] peer-checked:bg-[#00f5d4] peer-checked:border-[#00f5d4] transition-all" />
          <svg className="absolute w-3 h-3 text-[#1f1f25] pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <span className={`text-sm ${hours.isOpen ? 'text-[#e4e1e9] font-bold' : 'text-[#b9cac4]/60 font-medium'}`}>
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
              className="px-3 py-1.5 border border-[#3a4a46]/40 rounded-lg text-sm bg-[#1b1b20] text-[#e4e1e9] focus:ring-1 focus:ring-[#00f5d4] focus:border-[#00f5d4] transition-all"
              aria-label={`${dayName} opening time`}
            />
            <span className="text-[#b9cac4]/40 text-xs font-bold uppercase tracking-widest px-1">to</span>
            <input
              type="time"
              value={formatTimeForDisplay(hours.closeTime)}
              onChange={(e) => onTimeChange('closeTime', e.target.value)}
              data-testid={`close-time-${dayKey}`}
              className="px-3 py-1.5 border border-[#3a4a46]/40 rounded-lg text-sm bg-[#1b1b20] text-[#e4e1e9] focus:ring-1 focus:ring-[#00f5d4] focus:border-[#00f5d4] transition-all"
              aria-label={`${dayName} closing time`}
            />
          </>
        ) : (
          <span className="text-[#ffb4ab]/80 text-[10px] font-bold uppercase tracking-widest bg-[#ffb4ab]/10 px-2 py-1 rounded">Closed</span>
        )}
      </div>
    </div>
  );
}
