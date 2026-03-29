import React from 'react';
import {
  ResponsiveContainer,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

interface BaseChartProps {
  children: React.ReactNode;
  data?: unknown[];
  width?: string | number;
  height?: number;
  margin?: { top?: number; right?: number; left?: number; bottom?: number };
  className?: string;
  isLoading?: boolean;
  error?: string | null;
  showGrid?: boolean;
  showXAxis?: boolean;
  showYAxis?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  'aria-label'?: string;
}

const LoadingSkeleton = () => (
  <div className="animate-pulse flex items-center justify-center h-full">
    <div className="w-full h-32 bg-white/5 rounded-lg" />
  </div>
);

const ErrorState = ({ message }: { message: string }) => (
  <div className="flex items-center justify-center h-full p-6">
    <div className="text-center">
      <div className="text-rose-400 text-sm font-bold mb-2">Chart Offline</div>
      <div className="text-white/40 text-xs">{message}</div>
    </div>
  </div>
);

/**
 * Base chart wrapper component that provides:
 * - Responsive container
 * - Loading state
 * - Error handling
 * - Accessibility attributes
 * - Consistent styling
 */
export function BaseChart({
  children,
  data,
  width = '100%',
  height = 300,
  margin = { top: 20, right: 30, left: 20, bottom: 20 },
  className = '',
  isLoading = false,
  error = null,
  showGrid = true,
  showXAxis = true,
  showYAxis = true,
  showTooltip = true,
  showLegend = false,
  'aria-label': ariaLabel = 'Chart visualization',
}: BaseChartProps) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div
      className={`chart-container ${className}`}
      role="img"
      aria-label={ariaLabel}
      aria-live="polite"
    >
      <ResponsiveContainer width={width} height={height}>
        {/* Chart wrapper provides grid, axes, and tooltips */}
        <div style={{ width, height }}>
          {React.Children.map(children, (child) => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child as React.ReactElement, {
                data,
                margin,
                ...(showGrid && {
                  children: (
                    <>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="rgba(255, 255, 255, 0.08)"
                        horizontal
                        vertical
                      />
                      {showXAxis && (
                        <XAxis
                          style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
                          stroke="rgba(255, 255, 255, 0.1)"
                          tickLine={false}
                        />
                      )}
                      {showYAxis && (
                        <YAxis
                          style={{ fontSize: '11px', fill: 'rgba(255, 255, 255, 0.5)' }}
                          stroke="rgba(255, 255, 255, 0.1)"
                          tickLine={false}
                        />
                      )}
                      {showTooltip && <Tooltip content={() => <div />} />}
                      {showLegend && (
                        <Legend
                          wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }}
                          iconType="circle"
                        />
                      )}
                    </>
                  ),
                }),
              });
            }
            return child;
          })}
        </div>
      </ResponsiveContainer>
    </div>
  );
}

export default BaseChart;
