import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { ChartTooltip } from './ChartTooltip';

interface DonutChartProps {
  data: Array<{ name: string; value: number; color?: string }>;
  width?: number | string;
  height?: number;
  innerRadius?: number | string;
  outerRadius?: number | string;
  accentColor?: string;
  showTooltip?: boolean;
  onClick?: (data: any, index: number) => void;
  className?: string;
  ariaLabel?: string;
}

const DEFAULT_COLORS = ['#00f5d4', '#a78bfa', '#fb923c', '#f87171', '#60a5fa'];

/**
 * Donut/pie chart component for health gauges and distribution displays
 * Supports custom colors, tooltips, and click interactions
 */
export function DonutChart({
  data,
  width = '100%',
  height = 200,
  innerRadius = '60%',
  outerRadius = '80%',
  accentColor = '#00f5d4',
  showTooltip = true,
  onClick,
  className = '',
  ariaLabel = 'Donut chart',
}: DonutChartProps) {
  const getColor = (index: number, customColor?: string) => {
    return customColor || DEFAULT_COLORS[index % DEFAULT_COLORS.length];
  };

  return (
    <div
      className={`donut-chart ${className}`}
      role="img"
      aria-label={ariaLabel}
    >
      <ResponsiveContainer width={width} height={height}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={2}
            dataKey="value"
            onClick={onClick}
            className="cursor-pointer"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={getColor(index, entry.color)}
                stroke="rgba(255, 255, 255, 0.1)"
                strokeWidth={1}
                className="transition-opacity hover:opacity-80"
              />
            ))}
          </Pie>
          {showTooltip && (
            <ChartTooltip
              content={({ active, payload }) => {
                if (!active || !payload || !payload.length) return null;
                const data = payload[0].payload;
                return (
                  <div
                    className="px-3 py-2 rounded-lg shadow-xl backdrop-blur-xl border"
                    style={{
                      backgroundColor: 'rgba(13, 13, 18, 0.95)',
                      borderColor: `${data.color || accentColor}40`,
                    }}
                  >
                    <div className="text-white/50 text-[10px] font-bold uppercase tracking-wider">
                      {data.name}
                    </div>
                    <div
                      className="font-bold text-lg mt-1"
                      style={{ color: data.color || accentColor }}
                    >
                      {data.value.toLocaleString()}
                    </div>
                  </div>
                );
              }}
            />
          )}
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

/**
 * Mini donut gauge for displaying a single percentage value
 * Shows success (green), warning (yellow), or critical (red) zones
 */
export function DonutGauge({
  value,
  maxValue = 100,
  width = 120,
  height = 120,
  accentColor,
  showLabel = true,
  className = '',
}: {
  value: number;
  maxValue?: number;
  width?: number;
  height?: number;
  accentColor?: string;
  showLabel?: boolean;
  className?: string;
}) {
  const percentage = Math.min(100, Math.max(0, (value / maxValue) * 100));

  // Determine color based on value
  const getColor = () => {
    if (accentColor) return accentColor;
    if (percentage >= 80) return '#00f5d4'; // Green
    if (percentage >= 60) return '#fb923c'; // Yellow/Orange
    return '#f87171'; // Red
  };

  const color = getColor();

  const data = [
    { name: 'Value', value: percentage, color },
    { name: 'Remaining', value: 100 - percentage, color: 'rgba(255, 255, 255, 0.05)' },
  ];

  return (
    <div className={`relative ${className}`}>
      <DonutChart
        data={data}
        width={width}
        height={height}
        innerRadius="70%"
        outerRadius="85%"
        showTooltip={false}
        ariaLabel={`Gauge showing ${percentage}%`}
      />
      {showLabel && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-black" style={{ color }}>
              {Math.round(percentage)}%
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DonutChart;
