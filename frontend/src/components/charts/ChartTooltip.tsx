import React from 'react';
import { TooltipProps } from 'recharts';

interface ChartTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
  formatter?: (value: any, name: string, props: any) => React.ReactNode;
  labelFormatter?: (label: string) => React.ReactNode;
  contentStyle?: React.CSSProperties;
  accentColor?: string;
}

/**
 * Custom tooltip component with mantis-themed styling
 * Supports keyboard navigation and screen readers
 */
export function ChartTooltip({
  active,
  payload,
  label,
  formatter,
  labelFormatter,
  contentStyle,
  accentColor = '#00f5d4',
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }

  const defaultContentStyle: React.CSSProperties = {
    backgroundColor: 'rgba(13, 13, 18, 0.95)',
    border: '1px solid rgba(0, 245, 212, 0.2)',
    borderRadius: '8px',
    padding: '12px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
    backdropFilter: 'blur(10px)',
    color: '#fff',
    fontSize: '11px',
    minWidth: '150px',
    ...contentStyle,
  };

  const defaultLabelStyle: React.CSSProperties = {
    fontWeight: 'bold',
    marginBottom: '8px',
    paddingBottom: '8px',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    color: 'rgba(255, 255, 255, 0.7)',
  };

  return (
    <div
      className="chart-tooltip"
      style={defaultContentStyle}
      role="tooltip"
      aria-live="polite"
    >
      {label && (
        <div style={defaultLabelStyle}>
          {labelFormatter ? labelFormatter(label) : label}
        </div>
      )}
      <div className="space-y-1.5">
        {payload.map((entry: any, index: number) => {
          const value = formatter
            ? formatter(entry.value, entry.name, entry)
            : entry.value;

          return (
            <div
              key={`tooltip-${index}`}
              className="flex items-center justify-between gap-4"
              style={{ fontSize: '11px' }}
            >
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: entry.color || accentColor }}
                />
                <span style={{ color: 'rgba(255, 255, 255, 0.7)' }}>
                  {entry.name}
                </span>
              </div>
              <span className="font-bold" style={{ color: entry.color || accentColor }}>
                {typeof value === 'number' ? value.toLocaleString() : value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface SimpleTooltipProps {
  value?: string | number;
  label?: string;
  description?: string;
  color?: string;
}

/**
 * Simple tooltip for single-value displays (e.g., mini charts in cards)
 */
export function SimpleTooltip({
  value,
  label,
  description,
  color = '#00f5d4',
}: SimpleTooltipProps) {
  if (!value) return null;

  return (
    <div
      className="px-3 py-2 rounded-lg shadow-xl backdrop-blur-xl border"
      style={{
        backgroundColor: 'rgba(13, 13, 18, 0.95)',
        borderColor: `${color}20`,
        color: '#fff',
        fontSize: '11px',
      }}
      role="tooltip"
    >
      {label && (
        <div className="text-white/50 text-[10px] font-bold uppercase tracking-wider mb-1">
          {label}
        </div>
      )}
      <div className="font-bold text-lg" style={{ color }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {description && (
        <div className="text-white/40 text-[10px] mt-1">{description}</div>
      )}
    </div>
  );
}

export default ChartTooltip;
