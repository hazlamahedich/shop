import React from 'react';

interface BubbleDataPoint {
  id: string;
  name: string;
  x: number; // Ease to fix (0-100)
  y: number; // Impact (0-100)
  size: number; // Frequency/priority
  color?: string;
  category?: 'quick-win' | 'major-project' | 'fill-in' | 'low-priority';
}

interface BubbleChartProps {
  data: BubbleDataPoint[];
  width?: number | string;
  height?: number;
  onClick?: (bubble: BubbleDataPoint) => void;
  onHover?: (bubble: BubbleDataPoint | null) => void;
  className?: string;
  showLabels?: boolean;
  showQuadrants?: boolean;
  quadrantLabels?: {
    topLeft?: string;
    topRight?: string;
    bottomLeft?: string;
    bottomRight?: string;
  };
  xLabel?: string;
  yLabel?: string;
  ariaLabel?: string;
}

/**
 * Bubble chart for opportunity matrix visualization
 * X-axis: Ease to fix (left = hard, right = easy)
 * Y-axis: Impact (bottom = low, top = high)
 * Size: Frequency/priority
 */
export function BubbleChart({
  data,
  width = '100%',
  height = 250,
  onClick,
  onHover,
  className = '',
  showLabels = true,
  showQuadrants = true,
  quadrantLabels = {
    topLeft: 'MAJOR PROJECTS',
    topRight: 'QUICK WINS',
    bottomLeft: 'FILL IN',
    bottomRight: 'LOW PRIORITY',
  },
  xLabel = 'EASY TO FIX →',
  yLabel = '↑ IMPACT',
  ariaLabel = 'Opportunity matrix bubble chart',
}: BubbleChartProps) {
  const [hoveredBubble, setHoveredBubble] = React.useState<BubbleDataPoint | null>(null);

  const maxBubbleSize = Math.max(...data.map(d => d.size));

  // Get category colors
  const getCategoryColor = (bubble: BubbleDataPoint) => {
    if (bubble.color) return bubble.color;
    if (bubble.x >= 50 && bubble.y >= 50) return '#fb923c'; // Top-right: Quick wins (amber)
    if (bubble.x >= 50 && bubble.y < 50) return '#a78bfa'; // Bottom-right: Low priority (purple)
    if (bubble.x < 50 && bubble.y < 50) return '#60a5fa'; // Bottom-left: Fill in (blue)
    return '#f87171'; // Top-left: Major projects (red)
  };

  return (
    <div
      className={`bubble-chart ${className}`}
      style={{ width, height }}
      role="img"
      aria-label={ariaLabel}
      onMouseLeave={() => {
        setHoveredBubble(null);
        onHover?.(null);
      }}
    >
      {/* Quadrant labels */}
      {showQuadrants && (
        <>
          <div className="absolute top-2 left-2 text-[8px] font-black text-white/20 uppercase tracking-wider" style={{ textAlign: 'left' }}>
            {quadrantLabels.topLeft}
          </div>
          <div className="absolute top-2 right-2 text-[8px] font-black text-white/20 uppercase tracking-wider" style={{ textAlign: 'right' }}>
            {quadrantLabels.topRight}
          </div>
          <div className="absolute bottom-2 left-2 text-[8px] font-black text-white/20 uppercase tracking-wider" style={{ textAlign: 'left' }}>
            {quadrantLabels.bottomLeft}
          </div>
          <div className="absolute bottom-2 right-2 text-[8px] font-black text-white/20 uppercase tracking-wider" style={{ textAlign: 'right' }}>
            {quadrantLabels.bottomRight}
          </div>
        </>
      )}

      {/* Axis labels */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full text-[8px] font-bold text-white/20 uppercase tracking-wider" style={{ transformOrigin: 'bottom center' }}>
        {xLabel}
      </div>
      <div className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 text-[8px] font-bold text-white/20 uppercase tracking-wider" style={{ transformOrigin: 'center left' }}>
        {yLabel}
      </div>

      {/* Bubbles */}
      <div className="relative w-full h-full">
        {data.map((bubble, index) => {
          const sizePercent = 30 + (bubble.size / maxBubbleSize) * 50; // 30-80% of container
          const color = getCategoryColor(bubble);
          const isHovered = hoveredBubble?.id === bubble.id;

          return (
            <div
              key={bubble.id}
              className="absolute rounded-full border border-white/20 transition-all cursor-pointer group/bubble"
              style={{
                left: `${bubble.x}%`,
                top: `${100 - bubble.y}%`,
                width: `${sizePercent}%`,
                height: `${sizePercent}%`,
                transform: 'translate(-50%, -50%)',
                backgroundColor: `${color}40`,
                borderColor: color,
                boxShadow: isHovered ? `0 0 20px ${color}80` : 'none',
                zIndex: isHovered ? 10 : 1,
              }}
              onClick={() => onClick?.(bubble)}
              onMouseEnter={() => {
                setHoveredBubble(bubble);
                onHover?.(bubble);
              }}
              title={`${bubble.name}: ${bubble.size} occurrences`}
            >
              {/* Inner highlight */}
              <div
                className="absolute inset-2 rounded-full opacity-30"
                style={{
                  background: `radial-gradient(circle at 30% 30%, ${color}, transparent 70%)`,
                }}
              />

              {/* Label for larger bubbles */}
              {showLabels && sizePercent > 40 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <span
                    className="text-[8px] font-black text-white truncate px-1"
                    style={{
                      textShadow: '0 0 8px rgba(0,0,0,0.9), 0 0 4px rgba(0,0,0,0.8)',
                      fontWeight: 900,
                    }}
                  >
                    {bubble.name}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Mini bubble chart for compact displays
 */
export function MiniBubbleChart({
  data,
  width = 200,
  height = 80,
  maxBubbles = 5,
}: {
  data: BubbleDataPoint[];
  width?: number;
  height?: number;
  maxBubbles?: number;
}) {
  const displayData = data.slice(0, maxBubbles);
  const maxValue = Math.max(...displayData.map(d => d.size));

  return (
    <div className="flex gap-1 flex-wrap" style={{ width, height }}>
      {displayData.map((bubble, idx) => {
        const size = 12 + (bubble.size / maxValue) * 20;
        const color = bubble.x >= 50 && bubble.y >= 50 ? '#fb923c' :
                     bubble.x >= 50 && bubble.y < 50 ? '#a78bfa' :
                     bubble.x < 50 && bubble.y < 50 ? '#60a5fa' :
                     '#f87171';

        return (
          <div
            key={idx}
            className="rounded-full border border-white/20 flex-shrink-0"
            style={{
              width: size,
              height: size,
              backgroundColor: `${color}40`,
              borderColor: color,
            }}
            title={`${bubble.name}: ${bubble.size}`}
          />
        );
      })}
    </div>
  );
}

export default BubbleChart;
