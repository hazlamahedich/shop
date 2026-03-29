import React from 'react';

interface BoxPlotData {
  min: number;
  q1: number; // 25th percentile
  median: number; // 50th percentile
  q3: number; // 75th percentile
  max: number;
  outliers?: number[];
  mean?: number;
}

interface BoxPlotProps {
  data: BoxPlotData;
  width?: number | string;
  height?: number;
  color?: string;
  showOutliers?: boolean;
  showLabels?: boolean;
  className?: string;
  ariaLabel?: string;
}

/**
 * Box plot visualization for latency distribution
 * Shows min, Q1, median, Q3, max with outliers
 */
export function BoxPlot({
  data,
  width = '100%',
  height = 120,
  color = '#00f5d4',
  showOutliers = true,
  showLabels = true,
  className = '',
  ariaLabel = 'Response time distribution box plot',
}: BoxPlotProps) {
  const range = data.max - data.min;
  const scale = range > 0 ? 100 / range : 1;

  const toPercent = (value: number) => ((value - data.min) * scale);

  const getColorZone = (value: number) => {
    const pct = toPercent(value);
    if (pct > 80) return '#f87171'; // Red - slow
    if (pct > 50) return '#fb923c'; // Yellow - warning
    return '#00f5d4'; // Green - fast
  };

  return (
    <div
      className={`box-plot ${className}`}
      style={{ width, height }}
      role="img"
      aria-label={ariaLabel}
    >
      <div className="relative w-full h-full flex items-end px-4">
        {/* Y-axis line */}
        <div className="absolute left-0 right-0 bottom-0 h-px bg-white/10" />

        {/* Min whisker */}
        <div
          className="absolute bg-white/40"
          style={{
            left: '0%',
            width: `${toPercent(data.min)}%`,
            bottom: '50%',
            height: '2px',
          }}
        />

        {/* Left box whisker */}
        <div
          className="absolute bg-white/40"
          style={{
            left: `${toPercent(data.min)}%`,
            width: `${toPercent(data.q1) - toPercent(data.min)}%`,
            bottom: '50%',
            height: '2px',
          }}
        />

        {/* Box (Q1 to Q3) */}
        <div
          className="absolute rounded border-2 transition-all hover:opacity-80"
          style={{
            left: `${toPercent(data.q1)}%`,
            width: `${toPercent(data.q3) - toPercent(data.q1)}%`,
            bottom: '10%',
            height: '80%',
            backgroundColor: `${color}30`,
            borderColor: color,
            opacity: 0.8,
          }}
        >
          {/* Median line */}
          <div
            className="absolute bg-white"
            style={{
              left: '50%',
              width: '2px',
              height: '100%',
              transform: 'translateX(-50%)',
            }}
          />
        </div>

        {/* Right box whisker */}
        <div
          className="absolute bg-white/40"
          style={{
            left: `${toPercent(data.q3)}%`,
            width: `${toPercent(data.max) - toPercent(data.q3)}%`,
            bottom: '50%',
            height: '2px',
          }}
        />

        {/* Max whisker */}
        <div
          className="absolute bg-white/40"
          style={{
            left: `${toPercent(data.max)}%`,
            width: `${100 - toPercent(data.max)}%`,
            bottom: '50%',
            height: '2px',
          }}
        />

        {/* Outliers */}
        {showOutliers && data.outliers && data.outliers.map((outlier, idx) => (
          <div
            key={idx}
            className="absolute w-1.5 h-1.5 rounded-full"
            style={{
              left: `${toPercent(outlier)}%`,
              bottom: 'calc(50% - 3px)',
              backgroundColor: getColorZone(outlier),
            }}
            title={`Outlier: ${outlier}ms`}
          />
        ))}

        {/* X-axis labels */}
        {showLabels && (
          <div className="absolute -bottom-6 left-0 right-0 flex justify-between px-0">
            <span className="text-[7px] text-white/30 font-black uppercase">{(data.min / 1000).toFixed(1)}s</span>
            <span className="text-[7px] text-white/30 font-black uppercase">{(data.q1 / 1000).toFixed(1)}s</span>
            <span className="text-[7px] text-white/50 font-black uppercase">{(data.median / 1000).toFixed(1)}s</span>
            <span className="text-[7px] text-white/30 font-black uppercase">{(data.q3 / 1000).toFixed(1)}s</span>
            <span className="text-[7px] text-white/30 font-black uppercase">{(data.max / 1000).toFixed(1)}s</span>
          </div>
        )}
      </div>

      {/* Percentile badges */}
      {showLabels && (
        <div className="flex items-center justify-around mt-8">
          <div className="text-center">
            <div className="text-[7px] text-white/30 font-black uppercase">P50</div>
            <div className="text-[10px] font-bold text-white">{(data.median / 1000).toFixed(2)}s</div>
          </div>
          <div className="text-center">
            <div className="text-[7px] text-white/30 font-black uppercase">P95</div>
            <div className="text-[10px] font-bold text-white">{(data.q3 / 1000).toFixed(2)}s</div>
          </div>
          <div className="text-center">
            <div className="text-[7px] text-white/30 font-black uppercase">P99</div>
            <div className="text-[10px] font-bold text-white">{(data.max / 1000).toFixed(2)}s</div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Percentile comparison chart
 */
export function PercentileComparison({
  current,
  previous,
  labels = ['P50', 'P95', 'P99'],
  height = 80,
  width = '100%',
}: {
  current: { p50: number; p95: number; p99: number };
  previous?: { p50: number; p95: number; p99: number };
  labels?: string[];
  height?: number;
  width?: string;
}) {
  const maxValue = Math.max(
    current.p50,
    current.p95,
    current.p99,
    previous?.p50 ?? 0,
    previous?.p95 ?? 0,
    previous?.p99 ?? 0
  );

  return (
    <div className="percentile-comparison" style={{ width }}>
      <div className="flex items-end gap-2" style={{ height }}>
        {labels.map((label, idx) => {
          const currentValue = label === 'P50' ? current.p50 : label === 'P95' ? current.p95 : current.p99;
          const previousValue = previous?.[label.toLowerCase() as keyof typeof previous];
          const hasPrevious = previousValue !== undefined;

          return (
            <div key={label} className="flex-1 flex flex-col items-center gap-1">
              <div className="text-[8px] font-black text-white/30 uppercase">{label}</div>
              <div className="w-full bg-white/5 rounded-lg overflow-hidden flex-1 relative" style={{ height: '60%' }}>
                {hasPrevious && (
                  <div
                    className="absolute bottom-0 w-full bg-white/20"
                    style={{ height: `${(previousValue / maxValue) * 100}%` }}
                  />
                )}
                <div
                  className="w-full relative z-10 transition-all"
                  style={{
                    height: `${(currentValue / maxValue) * 100}%`,
                    backgroundColor: currentValue < 3000 ? '#00f5d4' : currentValue < 5000 ? '#fb923c' : '#f87171',
                  }}
                />
              </div>
              <div className="text-[9px] font-bold text-white">
                {(currentValue / 1000).toFixed(2)}s
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default BoxPlot;
