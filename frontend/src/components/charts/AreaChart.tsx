import React from 'react';
import { AreaChart as RechartsAreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface AreaChartProps {
  data: Array<Record<string, any>>;
  dataKey: string;
  width?: number | string;
  height?: number;
  color?: string;
  gradient?: boolean;
  showGrid?: boolean;
  showXAxis?: boolean;
  showYAxis?: boolean;
  showTooltip?: boolean;
  xAxisKey?: string;
  className?: string;
  ariaLabel?: string;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
}

/**
 * Area chart component for displaying trends over time
 * Perfect for cost trends, volume changes, sentiment flow
 */
export function AreaChart({
  data,
  dataKey,
  width = '100%',
  height = 300,
  color = '#00f5d4',
  gradient = true,
  showGrid = true,
  showXAxis = true,
  showYAxis = true,
  showTooltip = true,
  xAxisKey = 'name',
  className = '',
  ariaLabel = 'Area chart showing trends',
  margin = { top: 20, right: 30, left: 20, bottom: 20 },
}: AreaChartProps) {
  const gradientId = `area-gradient-${color.replace('#', '')}`;

  return (
    <div className={`area-chart ${className}`} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width={width} height={height}>
        <RechartsAreaChart data={data} margin={margin}>
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.08)"
              horizontal
              vertical={false}
            />
          )}
          {showXAxis && (
            <XAxis
              dataKey={xAxisKey}
              style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
              stroke="rgba(255, 255, 255, 0.1)"
              tickLine={false}
              axisLine={false}
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
            dataKey={dataKey}
            stroke={color}
            strokeWidth={2}
            fill={color}
            fillOpacity={gradient ? 0.3 : 0.2}
          />
        </RechartsAreaChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Mini sparkline area chart for compact displays
 */
export function MiniAreaChart({
  data,
  dataKey,
  width = 120,
  height = 40,
  color = '#00f5d4',
  showTooltip = false,
  className = '',
}: {
  data: Array<Record<string, any>>;
  dataKey: string;
  width?: number;
  height?: number;
  color?: string;
  showTooltip?: boolean;
  className?: string;
}) {
  return (
    <AreaChart
      data={data}
      dataKey={dataKey}
      width={width}
      height={height}
      color={color}
      gradient
      showGrid={false}
      showXAxis={false}
      showYAxis={false}
      showTooltip={showTooltip}
      margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
      className={className}
      ariaLabel="Mini trend chart"
    />
  );
}

export default AreaChart;
