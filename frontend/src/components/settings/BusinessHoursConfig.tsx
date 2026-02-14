/**
 * Business Hours Configuration Component
 *
 * Story 3.10: Business Hours Configuration
 *
 * Allows merchants to configure their business hours including:
 * - Day-by-day hours with open/close toggles
 * - Timezone selection
 * - Custom out-of-office message
 */

import { useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Label } from '@/components/ui/Label';
import { Alert } from '@/components/ui/Alert';
import { Select } from '@/components/ui/Select';
import { useBusinessHoursStore } from '@/stores/businessHoursStore';
import { DAYS_OF_WEEK, TIMEZONE_OPTIONS, type DayHours } from '@/types/businessHours';
import { DayHoursRow } from './DayHoursRow';
import { SaveIndicator } from './SaveIndicator';

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
    const existingDays = new Set(config?.hours?.map((h) => h.day) || []);
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
      <Card>
        <CardContent className="p-6">
          <p className="text-center text-slate-500">Loading business hours...</p>
        </CardContent>
      </Card>
    );
  }

  const hours = config?.hours || [];
  const showInitialize = hours.length === 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Business Hours</CardTitle>
            <CardDescription>
              Set your business hours to manage customer expectations for human support.
            </CardDescription>
          </div>
          <SaveIndicator saving={saving} lastSaved={lastSaved} />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {error && (
          <Alert variant="error" title="Error">
            {error}
          </Alert>
        )}

        {showInitialize ? (
          <div className="text-center py-4">
            <p className="text-slate-500 mb-4">No business hours configured yet.</p>
            <button
              onClick={initializeDayHours}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Set Default Hours (Mon-Fri 9 AM - 5 PM)
            </button>
          </div>
        ) : (
          <>
            <div>
              <Label htmlFor="timezone">Timezone</Label>
              <Select
                id="timezone"
                value={config?.timezone || 'America/Los_Angeles'}
                onChange={handleTimezoneChange}
                options={TIMEZONE_OPTIONS}
              />
            </div>

            <div>
              <Label className="mb-3 block">Hours of Operation</Label>
              <div className="space-y-2">
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
            </div>

            <div>
              <Label htmlFor="out-of-office-message">Out of Office Message (optional)</Label>
              <textarea
                id="out-of-office-message"
                value={config?.outOfOfficeMessage || ''}
                onChange={handleMessageChange}
                placeholder="Our team is offline. We'll respond during business hours."
                maxLength={500}
                rows={3}
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
              />
              <p className="text-sm text-slate-500 mt-1">
                {config?.outOfOfficeMessage?.length || 0}/500 characters
              </p>
            </div>

            {config?.formattedHours && (
              <div className="p-3 bg-slate-50 rounded-lg">
                <p className="text-sm text-slate-600">
                  <span className="font-medium">Preview: </span>
                  {config.outOfOfficeMessage || "Our team is offline. We'll respond during business hours."} (
                  {config.formattedHours}).
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
