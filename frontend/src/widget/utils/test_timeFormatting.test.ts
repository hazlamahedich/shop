import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { formatRelativeTime, formatAbsoluteTime } from './timeFormatting';

describe('formatRelativeTime', () => {
  let originalDateNow: typeof Date.now;

  beforeEach(() => {
    originalDateNow = Date.now;
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-01-15T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
    Date.now = originalDateNow;
  });

  describe('AC5: Relative Timestamp Time Ranges', () => {
    it('[9.7-UNIT-001] returns "Just now" for <1 minute', () => {
      const thirtySecondsAgo = '2024-01-15T11:59:30Z';
      expect(formatRelativeTime(thirtySecondsAgo)).toBe('Just now');
    });

    it('[9.7-UNIT-002] returns "Xm ago" for <1 hour', () => {
      const fiveMinAgo = '2024-01-15T11:55:00Z';
      expect(formatRelativeTime(fiveMinAgo)).toBe('5m ago');

      const fiftyNineMinAgo = '2024-01-15T11:01:00Z';
      expect(formatRelativeTime(fiftyNineMinAgo)).toBe('59m ago');
    });

    it('[9.7-UNIT-003] returns "Xh ago" for <24 hours', () => {
      const oneHourAgo = '2024-01-15T11:00:00Z';
      expect(formatRelativeTime(oneHourAgo)).toBe('1h ago');

      const twentyThreeHoursAgo = '2024-01-14T13:00:00Z';
      expect(formatRelativeTime(twentyThreeHoursAgo)).toBe('23h ago');
    });

    it('[9.7-UNIT-004] returns "Xd ago" for <7 days', () => {
      const oneDayAgo = '2024-01-14T12:00:00Z';
      expect(formatRelativeTime(oneDayAgo)).toBe('1d ago');

      const sixDaysAgo = '2024-01-09T12:00:00Z';
      expect(formatRelativeTime(sixDaysAgo)).toBe('6d ago');
    });

    it('[9.7-UNIT-005] returns formatted date for >=7 days', () => {
      const sevenDaysAgo = '2024-01-08T12:00:00Z';
      const result = formatRelativeTime(sevenDaysAgo);
      expect(result).toMatch(/Jan/);
      expect(result).toMatch(/8/);
    });

    it('[9.7-UNIT-006] handles future timestamps gracefully', () => {
      const futureDate = '2024-01-15T13:00:00Z';
      expect(formatRelativeTime(futureDate)).toBe('Just now');
    });

    it('[9.7-UNIT-007] handles invalid dates', () => {
      expect(formatRelativeTime('invalid-date')).toBe('Invalid date');
      expect(formatRelativeTime('')).toBe('Invalid date');
    });

    it('[9.7-UNIT-008] handles very old dates (>1 year)', () => {
      const oneYearAgo = '2023-01-15T12:00:00Z';
      const result = formatRelativeTime(oneYearAgo);
      expect(result).toMatch(/2023/);
    });
  });
});

describe('formatAbsoluteTime', () => {
  it('formats time correctly', () => {
    const result = formatAbsoluteTime('2024-01-15T14:30:00Z');
    expect(result).toMatch(/\d{1,2}:\d{2}/);
  });

  it('handles invalid dates', () => {
    expect(formatAbsoluteTime('invalid')).toBe('Invalid time');
  });
});
