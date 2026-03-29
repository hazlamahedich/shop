import React from 'react';

interface CircularProgressProps {
  value: number; // 0-100
  size?: number;
  strokeWidth?: number;
  color?: string;
  backgroundColor?: string;
  showValue?: boolean;
  label?: string;
  subLabel?: string;
  pulse?: boolean;
  className?: string;
  ariaLabel?: string;
}

/**
 * Circular progress indicator for queue monitoring
 * Shows progress as a percentage with optional pulse animation
 */
export function CircularProgress({
  value,
  size = 120,
  strokeWidth = 8,
  color = '#00f5d4',
  backgroundColor = 'rgba(255, 255, 255, 0.1)',
  showValue = true,
  label,
  subLabel,
  pulse = false,
  className = '',
  ariaLabel = 'Circular progress indicator',
}: CircularProgressProps) {
  const normalizedValue = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedValue / 100) * circumference;

  // Determine color based on value
  const getColor = () => {
    if (color !== '#00f5d4') return color;
    if (normalizedValue >= 80) return '#00f5d4'; // Green - healthy
    if (normalizedValue >= 50) return '#fb923c'; // Yellow - warning
    return '#f87171'; // Red - critical
  };

  const progressColor = getColor();

  return (
    <div
      className={`circular-progress ${className} ${pulse && normalizedValue < 50 ? 'animate-pulse' : ''}`}
      style={{ width: size, height: size }}
      role="progressbar"
      aria-label={ariaLabel}
      aria-valuenow={normalizedValue}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={backgroundColor}
          strokeWidth={strokeWidth}
        />

        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={progressColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500 ease-out"
          style={{
            filter: `drop-shadow(0 0 8px ${progressColor}40)`,
          }}
        />
      </svg>

      {/* Center content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {showValue && (
          <>
            <span
              className="text-2xl font-black"
              style={{
                color: progressColor,
                textShadow: `0 0 10px ${progressColor}40`,
              }}
            >
              {normalizedValue.toFixed(0)}
            </span>
            {label && (
              <span className="text-[8px] font-bold text-white/30 uppercase tracking-widest mt-1">
                {label}
              </span>
            )}
            {subLabel && (
              <span className="text-[8px] font-bold text-white/20 uppercase tracking-wider mt-0.5">
                {subLabel}
              </span>
            )}
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Mini circular progress for compact displays
 */
export function MiniCircularProgress({
  value,
  size = 40,
  color = '#00f5d4',
}: {
  value: number;
  size?: number;
  color?: string;
}) {
  return (
    <CircularProgress
      value={value}
      size={size}
      strokeWidth={3}
      color={color}
      showValue={false}
      ariaLabel="Mini circular progress"
    />
  );
}

export default CircularProgress;
