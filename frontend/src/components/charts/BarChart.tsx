import React from 'react';
import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface BarChartProps {
  data: Array<Record<string, any>>;
  dataKey: string;
  width?: number | string;
  height?: number;
  color?: string;
  horizontal?: boolean;
  showGrid?: boolean;
  showXAxis?: boolean;
  showYAxis?: boolean;
  showTooltip?: boolean;
  xAxisKey?: string;
  onClick?: (data: any, index: number) => void;
  className?: string;
  ariaLabel?: string;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  layout?: 'vertical' | 'horizontal';
  barSize?: number;
}

/**
 * Bar chart component for displaying rankings and comparisons
 * Perfect for top topics, FAQ usage, product rankings
 */
export function BarChart({
  data,
  dataKey,
  width = '100%',
  height = 300,
  color = '#00f5d4',
  horizontal = false,
  showGrid = true,
  showXAxis = true,
  showYAxis = true,
  showTooltip = true,
  xAxisKey = 'name',
  onClick,
  className = '',
  ariaLabel = 'Bar chart',
  margin = { top: 20, right: 30, left: 20, bottom: 60 },
  layout = horizontal ? 'vertical' : 'horizontal',
  barSize,
}: BarChartProps) {
  return (
    <div className={`bar-chart ${className}`} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width={width} height={height}>
        <RechartsBarChart
          data={data}
          layout={layout}
          margin={margin}
        >
          {showGrid && (
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.08)"
              horizontal={!horizontal}
              vertical={horizontal}
            />
          )}
          <XAxis
            hide={!showXAxis}
            type={horizontal ? 'number' : 'category'}
            dataKey={horizontal ? undefined : xAxisKey}
            style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
            stroke="rgba(255, 255, 255, 0.1)"
            tickLine={false}
            axisLine={false}
            angle={horizontal ? 0 : -45}
            textAnchor="end"
            height={horizontal ? undefined : 60}
          />
          <YAxis
            hide={!showYAxis}
            type={horizontal ? 'category' : 'number'}
            dataKey={horizontal ? xAxisKey : undefined}
            style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
            stroke="rgba(255, 255, 255, 0.1)"
            tickLine={false}
            axisLine={false}
            width={horizontal ? 60 : undefined}
          />
          {showTooltip && <Tooltip content={<ChartTooltip accentColor={color} />} />}
          <Bar
            dataKey={dataKey}
            fill={color}
            radius={[4, 4, 0, 0]}
            onClick={onClick}
            barSize={barSize}
            className="cursor-pointer"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.color || color}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Mini horizontal bar chart for compact displays
 */
export function MiniBarChart({
  data,
  dataKey,
  width = 200,
  height = 150,
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
    <BarChart
      data={data}
      dataKey={dataKey}
      width={width}
      height={height}
      color={color}
      horizontal
      showGrid={false}
      showXAxis={false}
      showYAxis={false}
      showTooltip={showTooltip}
      margin={{ top: 0, right: 0, left: 0, bottom: 0 }}
      barSize={12}
      className={className}
      ariaLabel="Mini bar chart"
    />
  );
}

export default BarChart;
