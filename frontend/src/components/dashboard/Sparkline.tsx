import React from 'react';

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function Sparkline({ 
  data, 
  width = 120, 
  height = 40, 
  color = '#6366f1', 
  className = '' 
}: SparklineProps) {
  if (!data || data.length === 0) {
    return <div className={className} style={{ width, height }} />;
  }

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min;
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;    <svg
      key={index}
      className={className}
      style={{ width, height }}
    >
      <polyline
        fill={color}
        strokeWidth={2.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
        filter(Boolean => points) // Remove NaN
        .join(' ')}
      />
    </svg>
  );
}
