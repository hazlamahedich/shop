import React from 'react';

interface TreemapNode {
  name: string;
  value: number;
  color?: string;
  children?: TreemapNode[];
}

interface TreemapChartProps {
  data: TreemapNode[];
  width?: number | string;
  height?: number;
  onClick?: (node: TreemapNode) => void;
  className?: string;
  showLabels?: boolean;
  ariaLabel?: string;
}

/**
 * Custom treemap visualization using CSS Grid
 * Shows document distribution by size/importance with color-coded effectiveness
 */
export function TreemapChart({
  data,
  width = '100%',
  height = 200,
  onClick,
  className = '',
  showLabels = true,
  ariaLabel = 'Treemap chart showing document distribution',
}: TreemapChartProps) {
  const totalValue = data.reduce((sum, node) => sum + node.value, 0);

  // Calculate sizes for flexible grid layout
  const gridLayout = data.map((node) => {
    const percentage = (node.value / totalValue) * 100;
    // Minimum 20% width, maximum 100%
    const gridSpan = Math.max(20, Math.min(100, Math.ceil(percentage / 10) * 10));
    return {
      ...node,
      percentage,
      gridSpan,
    };
  });

  return (
    <div
      className={`treemap-chart ${className}`}
      style={{ width, height }}
      role="img"
      aria-label={ariaLabel}
    >
      <div
        className="grid gap-1 h-full"
        style={{
          gridTemplateColumns: `repeat(auto-fit, minmax(60px, 1fr))`,
          gridAutoRows: '1fr',
        }}
      >
        {gridLayout.map((node, index) => (
          <div
            key={`${node.name}-${index}`}
            onClick={() => onClick?.(node)}
            className="relative group cursor-pointer rounded-lg border-2 border-white/40 transition-all hover:scale-105 hover:border-white hover:z-20 shadow-lg"
            style={{
              backgroundColor: node.color ? `${node.color}FF` : 'rgb(167, 139, 250)',
              gridColumn: `span ${Math.ceil(node.gridSpan / 20)}`,
              minHeight: '50px',
              opacity: 0.9,
            }}
          >
            {/* Background glow effect */}
            <div
              className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none rounded-lg"
              style={{
                background: `radial-gradient(circle at center, ${node.color || '#a78bfa'}60, transparent 70%)`,
              }}
            />

            {/* Content with Improved Text Contrast */}
            <div className="relative z-10 p-2 flex flex-col items-center justify-center h-full pointer-events-none">
              {showLabels && node.percentage > 3 && (
                <div className="bg-black/50 backdrop-blur-md px-2 py-1 rounded-md shadow-sm flex flex-col items-center border border-white/10">
                  <div className="text-[9px] font-black text-white uppercase tracking-tighter text-center leading-tight truncate w-full">
                    {node.name}
                  </div>
                  <div className="text-[10px] font-bold text-white/90 mt-0.5">
                    {node.percentage.toFixed(0)}%
                  </div>
                </div>
              )}
            </div>

            {/* Size indicator */}
            <div
              className="absolute inset-0 opacity-10 pointer-events-none rounded-lg"
              style={{
                background: `linear-gradient(135deg, ${node.color || '#a78bfa'}40 0%, transparent 100%)`,
              }}
            />

            {/* Custom Floating Tooltip */}
            <div className="absolute opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-50 bg-gray-900/95 backdrop-blur-md text-white px-3 py-2 rounded-lg shadow-xl border border-white/20 whitespace-nowrap bottom-[calc(100%+8px)] left-1/2 -translate-x-1/2 flex flex-col items-center">
              <span className="text-[11px] font-black uppercase tracking-wider" style={{ color: node.color || '#00f5d4' }}>
                {node.name}
              </span>
              <span className="text-[10px] font-medium text-white/80 mt-0.5">
                {node.value} Documents ({node.percentage.toFixed(1)}%)
              </span>
              {/* Caret pointing down */}
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-white/20" />
              <div className="absolute top-full left-1/2 -translate-x-1/2 border-[5px] border-transparent border-t-gray-900/95 -mt-[1px]" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Mini treemap for compact displays (e.g., in StatCards)
 */
export function MiniTreemap({
  data,
  width = '100%',
  height = 120,
  color = '#a78bfa',
}: {
  data: Array<{ name: string; value: number; color?: string }>;
  width?: number | string;
  height?: number | string;
  color?: string;
}) {
  return (
    <div
      className="p-1.5 rounded-lg"
      style={{ width, height, background: 'rgba(255, 255, 255, 0.05)', border: '1px solid rgba(255, 255, 255, 0.1)' }}
      role="img"
      aria-label="Mini treemap showing data distribution"
    >
      <TreemapChart 
        data={data.map(d => ({ ...d, color: d.color || color }))} 
        width="100%" 
        height={Number(height) - 16 || 104} 
        showLabels={true} 
      />
    </div>
  );
}

export default TreemapChart;
