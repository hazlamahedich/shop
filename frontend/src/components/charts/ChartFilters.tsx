import React from 'react';
import { Calendar, BarChart3 } from 'lucide-react';

export type DateRangePreset = '7d' | '30d' | '90d' | 'custom';
export type Granularity = 'hour' | 'day' | 'week' | 'month';

interface ChartFiltersProps {
  dateRange?: DateRangePreset;
  onDateRangeChange?: (range: DateRangePreset) => void;
  granularity?: Granularity;
  onGranularityChange?: (granularity: Granularity) => void;
  className?: string;
  accentColor?: string;
}

const DATE_RANGE_OPTIONS: { value: DateRangePreset; label: string }[] = [
  { value: '7d', label: '7D' },
  { value: '30d', label: '30D' },
  { value: '90d', label: '90D' },
  { value: 'custom', label: 'Custom' },
];

const GRANULARITY_OPTIONS: { value: Granularity; label: string; icon?: React.ReactNode }[] = [
  { value: 'hour', label: 'Hour' },
  { value: 'day', label: 'Day' },
  { value: 'week', label: 'Week' },
  { value: 'month', label: 'Month' },
];

/**
 * Chart filter controls for date range and time granularity
 * Provides interactive controls that update chart data
 */
export function ChartFilters({
  dateRange = '30d',
  onDateRangeChange,
  granularity = 'day',
  onGranularityChange,
  className = '',
  accentColor = '#00f5d4',
}: ChartFiltersProps) {
  const accentStyle = {
    color: accentColor,
    borderColor: `${accentColor}40`,
    backgroundColor: `${accentColor}10`,
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Date Range Presets */}
      {onDateRangeChange && (
        <div className="flex items-center gap-2">
          <Calendar size={14} className="text-white/30" />
          <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5 border border-white/10">
            {DATE_RANGE_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => onDateRangeChange(option.value)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider transition-all ${
                  dateRange === option.value
                    ? 'text-black shadow-lg'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
                style={
                  dateRange === option.value
                    ? {
                        backgroundColor: accentColor,
                        color: '#000',
                      }
                    : {}
                }
                aria-pressed={dateRange === option.value}
                aria-label={`Show ${option.label} data`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Time Granularity */}
      {onGranularityChange && (
        <div className="flex items-center gap-2">
          <BarChart3 size={14} className="text-white/30" />
          <div className="flex items-center gap-1 bg-white/5 rounded-lg p-0.5 border border-white/10">
            {GRANULARITY_OPTIONS.map((option) => (
              <button
                key={option.value}
                onClick={() => onGranularityChange(option.value)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1 ${
                  granularity === option.value
                    ? 'text-black shadow-lg'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
                style={
                  granularity === option.value
                    ? {
                        backgroundColor: accentColor,
                        color: '#000',
                      }
                    : {}
                }
                aria-pressed={granularity === option.value}
                aria-label={`Group by ${option.label}`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact date range badge for widget headers
 */
export function DateRangeBadge({
  range,
  onChange,
  accentColor = '#00f5d4',
}: {
  range: DateRangePreset;
  onChange?: (range: DateRangePreset) => void;
  accentColor?: string;
}) {
  const label = range === 'custom' ? 'Custom' : `${range}`;

  if (!onChange) {
    return (
      <span
        className="text-[9px] font-bold uppercase tracking-wider px-2 py-1 rounded-md bg-white/5 text-white/40 border border-white/10"
      >
        {label}
      </span>
    );
  }

  return (
    <button
      onClick={() => onChange(range)}
      className="text-[9px] font-bold uppercase tracking-wider px-2 py-1 rounded-md hover:bg-white/10 transition-colors"
      style={{
        backgroundColor: `${accentColor}10`,
        color: accentColor,
        border: `1px solid ${accentColor}30`,
      }}
    >
      {label}
    </button>
  );
}

export default ChartFilters;
