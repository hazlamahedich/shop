import React from 'react';

interface RadarDataPoint {
  axis: string;
  value: number; // 0-100
  fullMark?: number;
}

interface RadarChartProps {
  data: RadarDataPoint[];
  width?: number | string;
  height?: number;
  color?: string;
  fillOpacity?: number;
  showAxes?: boolean;
  showLabels?: boolean;
  showValues?: boolean;
  className?: string;
  ariaLabel?: string;
  onAxisClick?: (axis: string) => void;
}

/**
 * Radar/spider chart for multi-dimensional metrics
 * Shows performance across multiple axes (e.g., Accuracy, Speed, Resolution, Fallback, Satisfaction)
 */
export function RadarChart({
  data,
  width = '100%',
  height = 200,
  color = '#00f5d4',
  fillOpacity = 0.2,
  showAxes = true,
  showLabels = true,
  showValues = true,
  className = '',
  ariaLabel = 'Radar chart showing performance metrics',
  onAxisClick,
}: RadarChartProps) {
  const fullMark = data[0]?.fullMark ?? 100;
  const numAxes = data.length;
  const angleStep = (2 * Math.PI) / numAxes;

  // Calculate polygon points
  const centerX = 50;
  const centerY = 50;
  const radius = 40; // Max radius as percentage

  const getPointCoordinates = (value: number, index: number) => {
    const angle = index * angleStep - Math.PI / 2; // Start from top
    const normalizedValue = value / fullMark;
    const x = centerX + normalizedValue * radius * Math.cos(angle);
    const y = centerY + normalizedValue * radius * Math.sin(angle);
    return { x, y };
  };

  const polygonPoints = data.map((d, i) => {
    const coords = getPointCoordinates(d.value, i);
    return `${coords.x},${coords.y}`;
  }).join(' ');

  // Background grid (concentric polygons)
  const gridLevels = [0.25, 0.5, 0.75, 1];
  const gridPolygons = gridLevels.map((level, levelIdx) => {
    const levelPoints = data.map((_, i) => {
      const coords = getPointCoordinates(fullMark * level, i);
      return `${coords.x},${coords.y}`;
    }).join(' ');
    return { level, points: levelPoints, levelIdx };
  });

  // Axis lines and labels
  const axesElements = data.map((d, i) => {
    const outerCoords = getPointCoordinates(fullMark, i);
    const labelCoords = getPointCoordinates(fullMark * 1.15, i);
    const valueCoords = getPointCoordinates(d.value * 0.7, i);

    return (
      <g key={d.axis}>
        {/* Axis line */}
        {showAxes && (
          <line
            x1={centerX}
            y1={centerY}
            x2={outerCoords.x}
            y2={outerCoords.y}
            stroke="rgba(255, 255, 255, 0.1)"
            strokeWidth={1}
          />
        )}

        {/* Axis label */}
        {showLabels && (
          <text
            x={labelCoords.x}
            y={labelCoords.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className={`text-[7px] font-black uppercase fill-white/30 ${onAxisClick ? 'cursor-pointer hover:fill-white/60' : ''}`}
            onClick={() => onAxisClick?.(d.axis)}
            style={{ pointerEvents: onAxisClick ? 'auto' : 'none' }}
          >
            {d.axis}
          </text>
        )}

        {/* Value label */}
        {showValues && (
          <text
            x={valueCoords.x}
            y={valueCoords.y}
            textAnchor="middle"
            dominantBaseline="middle"
            className="text-[8px] font-bold fill-white/80"
          >
            {d.value}
          </text>
        )}
      </g>
    );
  });

  // Get color based on overall performance
  const getOverallColor = () => {
    const avgValue = data.reduce((sum, d) => sum + d.value, 0) / data.length;
    if (avgValue >= 80) return '#00f5d4'; // Green - excellent
    if (avgValue >= 60) return '#fb923c'; // Yellow - good
    return '#f87171'; // Red - needs improvement
  };

  const performanceColor = getOverallColor();

  return (
    <div
      className={`radar-chart ${className}`}
      style={{ width, height }}
      role="img"
      aria-label={ariaLabel}
    >
      <svg
        viewBox="0 0 100 100"
        className="w-full h-full"
        style={{ overflow: 'visible' }}
      >
        {/* Background grid */}
        {gridPolygons.map(({ level, points, levelIdx }) => (
          <polygon
            key={levelIdx}
            points={points}
            fill="none"
            stroke="rgba(255, 255, 255, 0.05)"
            strokeWidth={0.5}
          />
        ))}

        {/* Axis lines and labels */}
        {axesElements}

        {/* Data polygon */}
        <polygon
          points={polygonPoints}
          fill={performanceColor}
          fillOpacity={fillOpacity}
          stroke={performanceColor}
          strokeWidth={2}
          strokeLinejoin="round"
          className="hover:fill-opacity-30 transition-all"
        />

        {/* Data points */}
        {data.map((d, i) => {
          const coords = getPointCoordinates(d.value, i);
          return (
            <circle
              key={d.axis}
              cx={coords.x}
              cy={coords.y}
              r={1.5}
              fill={performanceColor}
              className="hover:r-2 transition-all cursor-pointer"
              onClick={() => onAxisClick?.(d.axis)}
            >
              <title>{d.axis}: {d.value}</title>
            </circle>
          );
        })}
      </svg>
    </div>
  );
}

/**
 * Mini radar chart for compact displays
 */
export function MiniRadarChart({
  data,
  width = 100,
  height = 100,
}: {
  data: RadarDataPoint[];
  width?: number;
  height?: number;
}) {
  const avgValue = data.reduce((sum, d) => sum + d.value, 0) / data.length;
  const color = avgValue >= 80 ? '#00f5d4' : avgValue >= 60 ? '#fb923c' : '#f87171';

  return (
    <div style={{ width, height }}>
      <RadarChart
        data={data}
        height={height}
        width={width}
        color={color}
        fillOpacity={0.3}
        showLabels={false}
        showValues={false}
        showAxes={true}
        ariaLabel="Mini radar chart"
      />
    </div>
  );
}

export default RadarChart;
