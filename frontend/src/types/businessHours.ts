/**
 * Business Hours Types
 *
 * Story 3.10: Business Hours Configuration
 */

export interface DayHours {
  day: string;
  isOpen: boolean;
  openTime?: string;
  closeTime?: string;
}

export interface BusinessHoursConfig {
  timezone: string;
  hours: DayHours[];
  outOfOfficeMessage?: string;
  formattedHours?: string;
}

export const DAYS_OF_WEEK: string[] = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

export const TIMEZONE_OPTIONS: { value: string; label: string }[] = [
  { value: 'America/Los_Angeles', label: 'Pacific Time (US)' },
  { value: 'America/Denver', label: 'Mountain Time (US)' },
  { value: 'America/Chicago', label: 'Central Time (US)' },
  { value: 'America/New_York', label: 'Eastern Time (US)' },
  { value: 'Europe/London', label: 'London (UK)' },
  { value: 'Europe/Paris', label: 'Paris (EU)' },
  { value: 'Europe/Berlin', label: 'Berlin (EU)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (Japan)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (China)' },
  { value: 'Asia/Singapore', label: 'Singapore' },
  { value: 'Australia/Sydney', label: 'Sydney (Australia)' },
  { value: 'Pacific/Auckland', label: 'Auckland (NZ)' },
];

export const DEFAULT_CONFIG: BusinessHoursConfig = {
  timezone: 'America/Los_Angeles',
  hours: [],
  outOfOfficeMessage: 'Our team is offline. We\'ll respond during business hours.',
};
