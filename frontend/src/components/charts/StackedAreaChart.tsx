import React from 'react';
import { AreaChart as RechartsAreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface StackedAreaDataPoint {
  date: string;
  successful: number;
  failed: number;
  total: number;
}

interface StackedAreaChartProps {
  data: StackedAreaDataPoint[];
  height?: number;
  width?: number | string;
  colors?: {
    success?: string;
    failure?: string;
  };
  showGrid?: boolean;
  showXAxis?: boolean;
  showYAxis?: boolean;
  showTooltip?: boolean;
  className?: string;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  ariaLabel?: string;
}

/**
 * Stacked area chart for showing FAQ success/failure trends
 * Displays successful vs failed FAQ clicks over time
 */
export function StackedAreaChart({
  data,
  height = 150,
  width = '100%',
  colors = {
    success: '#00f5d4',
    failure: '#f87171',
  },
  showGrid = true,
  showXAxis = true,
  showYAxis = false,
  showTooltip = true,
  className = '',
  margin = { top: 10, right: 10, left: 10, bottom: 30 },
  ariaLabel = 'FAQ success/failure trends stacked area chart',
}: StackedAreaChartProps) {
  return (
    <div className={`stacked-area-chart ${className}`} role="img" aria-label={ariaLabel}>
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
              dataKey="date"
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
          {showTooltip && <Tooltip content={<ChartTooltip accentColor={colors.success} />} />}
          <Area
            type="monotone"
            dataKey="successful"
            stackId="1"
            stroke={colors.success}
            strokeWidth={2}
            fill={colors.success}
            fillOpacity={0.6}
          />
          <Area
            type="monotone"
            dataKey="failed"
            stackId="1"
            stroke={colors.failure}
            strokeWidth={2}
            fill={colors.failure}
            fillOpacity={0.6}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Mini success rate trend line
 */
export function SuccessRateTrend({
  data,
  height = 40,
  width = '100%',
}: {
  data: StackedAreaDataPoint[];
  height?: number;
  width?: number | string;
}) {
  const successRateData = data.map(d => ({
    name: d.date,
    value: d.total > 0 ? (d.successful / d.total) * 100 : 0,
  }));

  const latestRate = successRateData[successRateData.length - 1]?.value || 0;
  const color = latestRate >= 70 ? '#00f5d4' : latestRate >= 50 ? '#fb923c' : '#f87171';

  return (
    <div style={{ width, height }}>
      {successRateData.length > 1 && (
        <svg width="100%" height="100%" viewBox="0 0 100 40">
          <polyline
            fill="none"
            stroke={color}
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
            opacity={0.6}
            points={successRateData.map((d, i) => {
              const x = (i / (successRateData.length - 1)) * 100;
              const y = 40 - (d.value / 100) * 40;
              return `${x},${y}`;
            }).join(' ')}
          />
        </svg>
      )}
    </div>
  );
}

export default StackedAreaChart;
