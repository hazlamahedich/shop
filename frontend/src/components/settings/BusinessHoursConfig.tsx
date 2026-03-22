/**
 * Business Hours Configuration Component
 *
 * Story 3.10: Business Hours Configuration
 */

import { useEffect } from 'react';
import { useBusinessHoursStore } from '@/stores/businessHoursStore';
import { DAYS_OF_WEEK, TIMEZONE_OPTIONS, type DayHours } from '@/types/businessHours';
import { DayHoursRow } from './DayHoursRow';
import { SaveIndicator } from './SaveIndicator';
import { AlertCircle } from 'lucide-react';

const DAY_NAMES: Record<string, string> = {
  mon: 'Monday',
  tue: 'Tuesday',
  wed: 'Wednesday',
  thu: 'Thursday',
  fri: 'Friday',
  sat: 'Saturday',
  sun: 'Sunday',
};

export function BusinessHoursConfig() {
  const { config, loading, saving, error, lastSaved, loadConfig, updateConfig, updateDayHours } =
    useBusinessHoursStore();

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleTimezoneChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    updateConfig({ timezone: e.target.value });
  };

  const handleDayToggle = (dayIndex: number, isOpen: boolean) => {
    updateDayHours(dayIndex, { isOpen });
  };

  const handleTimeChange = (dayIndex: number, field: 'openTime' | 'closeTime', value: string) => {
    updateDayHours(dayIndex, { [field]: value });
  };

  const handleMessageChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateConfig({ outOfOfficeMessage: e.target.value });
  };

  const initializeDayHours = () => {
    const newHours: DayHours[] = DAYS_OF_WEEK.map((day) => {
      const existing = config?.hours?.find((h) => h.day === day);
      if (existing) return existing;
      return {
        day,
        isOpen: day !== 'sat' && day !== 'sun',
        openTime: '09:00',
        closeTime: '17:00',
      };
    });
    updateConfig({ hours: newHours });
  };

  if (loading) {
    return (
      <div className="bg-[#1f1f25]/80 backdrop-blur-md border border-[#3a4a46]/20 shadow-[0_0_20px_rgba(0,0,0,0.3)] rounded-2xl p-6 relative overflow-hidden group/hours mt-6 flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#00f5d4] mb-4 shadow-[0_0_15px_rgba(0,245,212,0.3)]" />
      </div>
    );
  }

  const hours = config?.hours || [];
  const showInitialize = hours.length === 0;

  return (
    <div className="bg-[#1f1f25]/80 backdrop-blur-md border border-[#3a4a46]/20 shadow-[0_0_20px_rgba(0,0,0,0.3)] rounded-2xl p-6 relative overflow-hidden group/hours mt-6">
      {/* Decorative hud lines */}
      <div className="absolute top-0 right-0 w-32 h-[1px] bg-gradient-to-r from-transparent via-[#00f5d4]/50 to-transparent" />
      <div className="absolute top-0 left-0 w-[1px] h-32 bg-gradient-to-b from-[#00f5d4]/50 via-[#00f5d4]/10 to-transparent" />

      <div className="flex items-start justify-between mb-8 relative z-10">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="text-sm font-bold text-[#00f5d4] uppercase tracking-[0.2em] font-['Space_Grotesk']">
              Business Hours Configuration
            </h2>
            <div className="h-4 w-4 rounded bg-[#00f5d4]/10 flex items-center justify-center border border-[#00f5d4]/20 hidden sm:flex">
              <div className="h-1.5 w-1.5 bg-[#00f5d4] rounded-full animate-pulse shadow-[0_0_8px_#00f5d4]" />
            </div>
          </div>
          <p className="text-xs text-[#b9cac4]/60 font-medium">
            Set your business hours to manage customer expectations for human support.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <SaveIndicator saving={saving} lastSaved={lastSaved} />
        </div>
      </div>

      <div className="space-y-8 relative z-10">
        {error && (
          <div role="alert" className="p-4 bg-[#ffb4ab]/5 border border-[#ffb4ab]/20 rounded-lg flex items-start gap-3 backdrop-blur-md">
            <AlertCircle size={20} className="text-[#ffb4ab] flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-bold text-[#ffb4ab]">Error</p>
              <p className="text-xs text-[#ffb4ab]/80 mt-1">{error}</p>
            </div>
          </div>
        )}

        {showInitialize ? (
          <div className="text-center py-12 px-6 bg-[#1b1b20]/50 rounded-2xl border-2 border-dashed border-[#3a4a46]/40 hover:border-[#00f5d4]/30 hover:bg-[#1b1b20]/80 transition-all group">
            <p className="text-sm text-[#b9cac4]/60 mb-6 max-w-md mx-auto leading-relaxed">No business hours configured yet.</p>
            <button
              onClick={initializeDayHours}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold text-[#00f5d4] bg-[#00f5d4]/10 border border-[#00f5d4]/20 rounded-lg hover:bg-[#00f5d4]/20 hover:shadow-[0_0_15px_rgba(0,245,212,0.15)] transition-all"
            >
              Set Default Hours (Mon-Fri 9 AM - 5 PM)
            </button>
          </div>
        ) : (
          <>
            <div>
              <label htmlFor="timezone" className="block text-xs font-bold text-[#b9cac4] uppercase tracking-widest font-['Space_Grotesk'] mb-2">Timezone</label>
              <select
                id="timezone"
                value={config?.timezone || 'America/Los_Angeles'}
                onChange={handleTimezoneChange}
                className="w-full bg-[#1b1b20]/60 border-0 border-b-2 border-[#3a4a46] focus:border-[#00f5d4] focus:ring-0 text-sm py-3 px-4 text-[#e4e1e9] transition-all outline-none rounded-t-lg"
              >
                {TIMEZONE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value} className="bg-[#1f1f25] text-[#e4e1e9]">
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="bg-[#1b1b20]/40 rounded-xl border border-[#3a4a46]/20 overflow-hidden divide-y divide-[#3a4a46]/20">
              {hours.map((dayHours, index) => (
                <DayHoursRow
                  key={dayHours.day}
                  dayName={DAY_NAMES[dayHours.day] || dayHours.day}
                  hours={dayHours}
                  onToggle={(isOpen) => handleDayToggle(index, isOpen)}
                  onTimeChange={(field, value) => handleTimeChange(index, field, value)}
                />
              ))}
            </div>

            <div className="relative group">
              <label htmlFor="out-of-office-message" className="block text-[10px] text-[#b9cac4] uppercase tracking-widest font-['Inter'] mb-2">Out of Office Message <span className="text-[#b9cac4]/50 normal-case tracking-normal">(optional)</span></label>
              <textarea
                id="out-of-office-message"
                value={config?.outOfOfficeMessage || ''}
                onChange={handleMessageChange}
                placeholder="Our team is offline. We'll respond during business hours."
                maxLength={500}
                rows={3}
                className="w-full bg-[#1b1b20]/60 border border-[#3a4a46] focus:border-[#00f5d4] focus:ring-0 text-sm py-3 px-4 text-[#e4e1e9] transition-all outline-none resize-none rounded-lg placeholder-[#b9cac4]/30"
              />
              <div className="absolute right-2 bottom-3">
                <p className="text-[10px] font-mono font-bold text-[#b9cac4]/50 bg-[#1b1b20] px-2 space-y-2 rounded">
                  {config?.outOfOfficeMessage?.length || 0}/500
                </p>
              </div>
            </div>

            {config?.formattedHours && (
              <div className="p-4 bg-[#00bbf9]/5 border border-[#00bbf9]/20 rounded-lg backdrop-blur-sm mt-4">
                <p className="text-xs text-[#82d3ff] tracking-wide leading-relaxed">
                  <strong className="text-[#00bbf9]">Preview: </strong>
                  {config?.outOfOfficeMessage || "Our team is offline. We'll respond during business hours."} (
                  {config?.formattedHours}).
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

