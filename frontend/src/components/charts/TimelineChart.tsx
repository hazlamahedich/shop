import React from 'react';
import { AreaChart as RechartsAreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface TimelineDataPoint {
  time: string;
  value: number;
  label?: string;
  color?: string;
}

interface TimelineChartProps {
  data: TimelineDataPoint[];
  height?: number;
  width?: number | string;
  color?: string;
  showGrid?: boolean;
  showXAxis?: boolean;
  showYAxis?: boolean;
  showTooltip?: boolean;
  className?: string;
  markerSize?: number;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  ariaLabel?: string;
}

/**
 * Timeline chart with markers for events
 * Shows conversation volume over time with event indicators
 */
export function TimelineChart({
  data,
  height = 150,
  width = '100%',
  color = '#00f5d4',
  showGrid = true,
  showXAxis = true,
  showYAxis = false,
  showTooltip = true,
  className = '',
  markerSize = 4,
  margin = { top: 10, right: 10, left: 10, bottom: 30 },
  ariaLabel = 'Timeline chart',
}: TimelineChartProps) {
  return (
    <div className={`timeline-chart ${className}`} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width={width} height={height}>
        <RechartsAreaChart data={data} margin={margin}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.08)"
              horizontal={true}
              vertical={false}
            />
          )}
          {showXAxis && (
            <XAxis
              dataKey="time"
              style={{ fontSize: '10px', fill: 'rgba(255, 255, 255, 0.5)' }}
              stroke="rgba(255, 255, 255, 0.1)"
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
            />
          )}
          {showYAxis && (
            <YAxis
              style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
              stroke="rgba(255, 255, 255, 0.1)"
              tickLine={false}
              axisLine={false}
            />
          )}
          {showTooltip && <Tooltip content={<ChartTooltip accentColor={color} />} />}
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={color}
            fillOpacity={0.3}
          />

          {/* Event markers */}
          {data
            .filter((d) => d.label)
            .map((d, i) => (
              <g key={`marker-${i}`}>
                <circle
                  cx={data.indexOf(d) * (100 / (data.length - 1)) || 0}
                  cy={d.value}
                  r={markerSize}
                  fill={d.color || '#fb923c'}
                  stroke="rgba(255, 255, 255, 0.5)"
                  strokeWidth={1}
                  className="cursor-pointer hover:r-6 transition-all"
                />
              </g>
            ))}
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Peak hours heatmap strip - compact visualization
 */
export function PeakHoursHeatmapStrip({
  data, // Array of 24 hourly values (0-23)
  height = 40,
  onClick,
}: {
  data: number[];
  height?: number;
  onClick?: (hour: number, value: number) => void;
}) {
  const maxValue = Math.max(...data, 1);

  return (
    <div className="flex gap-0.5" style={{ height }}>
      {data.map((value, hour) => {
        const intensity = value / maxValue;
        const color = intensity > 0.7 ? '#00f5d4' :
                      intensity > 0.4 ? '#a78bfa' :
                      intensity > 0.2 ? '#fb923c' :
                      'rgba(255, 255, 255, 0.1)';

        return (
          <div
            key={hour}
            className="flex-1 rounded-sm transition-all hover:opacity-80 cursor-pointer border border-white/5"
            style={{
              backgroundColor: color,
              opacity: 0.3 + intensity * 0.7,
            }}
            onClick={() => onClick?.(hour, value)}
            title={`${hour}:00 - ${value} conversations`}
          />
        );
      })}
    </div>
  );
}

export default TimelineChart;
