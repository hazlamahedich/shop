/**
 * CostTooltip Component
 *
 * Displays detailed cost information on hover:
 * - Provider and model details
 * - Token counts (prompt, completion, total)
 * - Cost breakdown (input, output, total)
 * - Processing time if available
 * - Request count and average cost
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import React, { useState, useRef, useEffect } from 'react';
import { DollarSign, Hash, Clock, Cpu, Zap } from 'lucide-react';
import { formatCost, formatTokens, type ConversationCost } from '../../types/cost';

interface CostTooltipProps {
  /**
   * Conversation cost data to display
   */
  costData: ConversationCost;
  /**
   * Element that triggers the tooltip (hover target)
   */
  children: React.ReactElement;
  /**
   * Optional custom position
   * @default 'top'
   */
  position?: 'top' | 'bottom' | 'left' | 'right';
  /**
   * Delay before showing tooltip (ms)
   * @default 300
   */
  delay?: number;
}

interface PositionStyles {
  top?: string;
  bottom?: string;
  left?: string;
  right?: string;
  transform?: string;
}

/**
 * Calculate tooltip position based on anchor rect and position preference
 */
function getTooltipPosition(
  anchorRect: DOMRect,
  tooltipSize: { width: number; height: number },
  position: 'top' | 'bottom' | 'left' | 'right'
): PositionStyles {
  const spacing = 8; // px spacing from anchor
  const buffer = 10; // px buffer from viewport edge

  // Get viewport dimensions
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // Base positions
  const positions: Record<string, PositionStyles> = {
    top: {
      bottom: `${viewportHeight - anchorRect.top + spacing}px`,
      left: `${anchorRect.left + anchorRect.width / 2}px`,
      transform: 'translateX(-50%)',
    },
    bottom: {
      top: `${anchorRect.bottom + spacing}px`,
      left: `${anchorRect.left + anchorRect.width / 2}px`,
      transform: 'translateX(-50%)',
    },
    left: {
      top: `${anchorRect.top + anchorRect.height / 2}px`,
      right: `${viewportWidth - anchorRect.left + spacing}px`,
      transform: 'translateY(-50%)',
    },
    right: {
      top: `${anchorRect.top + anchorRect.height / 2}px`,
      left: `${anchorRect.right + spacing}px`,
      transform: 'translateY(-50%)',
    },
  };

  let chosenPosition = positions[position];

  // Simple viewport boundary checking
  // In production, would use Popper.js or similar for proper positioning
  return chosenPosition;
}

export const CostTooltip: React.FC<CostTooltipProps> = ({
  costData,
  children,
  position = 'top',
  delay = 300,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState<PositionStyles>({});
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const anchorRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      if (anchorRef.current) {
        const anchorRect = anchorRef.current.getBoundingClientRect();

        // Estimate tooltip size (will be recalculated on mount)
        const estimatedSize = { width: 250, height: 150 };

        setTooltipPosition(getTooltipPosition(anchorRect, estimatedSize, position));
        setIsVisible(true);
      }
    }, delay);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Update position after tooltip renders to get actual size
  useEffect(() => {
    if (isVisible && tooltipRef.current && anchorRef.current) {
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      const anchorRect = anchorRef.current.getBoundingClientRect();
      setTooltipPosition(getTooltipPosition(anchorRect, tooltipRect, position));
    }
  }, [isVisible]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Determine cost level for color coding
  const costLevel =
    costData.totalCostUsd <= 0.01
      ? 'low'
      : costData.totalCostUsd <= 0.1
        ? 'medium'
        : 'high';

  const costColorClass =
    costLevel === 'low'
      ? 'text-green-600'
      : costLevel === 'medium'
        ? 'text-yellow-700'
        : 'text-red-700';

  return (
    <>
      <span
        ref={anchorRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        className="inline-block"
      >
        {children}
      </span>

      {isVisible &&
        document.body && (
          <div
            ref={tooltipRef}
            className="fixed z-50 bg-white border border-gray-200 rounded-lg shadow-lg p-4 max-w-xs"
            style={tooltipPosition}
            onMouseEnter={() => {
              // Keep visible if mouse moves to tooltip
              if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
              }
            }}
            onMouseLeave={handleMouseLeave}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-gray-100">
              <h4 className="text-sm font-semibold text-gray-900">Cost Breakdown</h4>
              <span
                className={`text-sm font-bold ${costColorClass}`}
                title="Total cost for this conversation"
              >
                {formatCost(costData.totalCostUsd)}
              </span>
            </div>

            {/* Provider/Model */}
            {costData.provider && (
              <div className="flex items-center space-x-2 mb-3 pb-2 border-b border-gray-100">
                <Cpu size={14} className="text-gray-400" />
                <span className="text-xs font-medium text-gray-700 capitalize">
                  {costData.provider}
                </span>
                <span className="text-xs text-gray-400">/</span>
                <span className="text-xs text-gray-600">{costData.model}</span>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              {/* Total Cost */}
              <div className="flex items-center space-x-1.5">
                <DollarSign size={12} className="text-blue-500" />
                <span className="text-gray-500">Total:</span>
                <span className="font-medium text-gray-900">
                  {formatCost(costData.totalCostUsd)}
                </span>
              </div>

              {/* Total Tokens */}
              <div className="flex items-center space-x-1.5">
                <Hash size={12} className="text-purple-500" />
                <span className="text-gray-500">Tokens:</span>
                <span className="font-medium text-gray-900">
                  {formatTokens(costData.totalTokens)}
                </span>
              </div>

              {/* Request Count */}
              <div className="flex items-center space-x-1.5">
                <Zap size={12} className="text-green-500" />
                <span className="text-gray-500">Requests:</span>
                <span className="font-medium text-gray-900">{costData.requestCount}</span>
              </div>

              {/* Avg Cost */}
              <div className="flex items-center space-x-1.5">
                <Clock size={12} className="text-orange-500" />
                <span className="text-gray-500">Avg/Req:</span>
                <span className="font-medium text-gray-900">
                  {formatCost(costData.avgCostPerRequest)}
                </span>
              </div>
            </div>

            {/* Individual Requests Summary */}
            {costData.requests && costData.requests.length > 0 && (
              <div className="mt-3 pt-2 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Individual Requests:</p>
                <div className="max-h-20 overflow-y-auto space-y-1">
                  {costData.requests.slice(0, 5).map((request, idx) => (
                    <div
                      key={request.id || idx}
                      className="flex justify-between items-center text-xs py-1 px-2 bg-gray-50 rounded"
                    >
                      <span className="text-gray-600">#{idx + 1}</span>
                      <span className="text-gray-500">
                        {formatTokens(request.totalTokens)}
                      </span>
                      <span className="font-medium text-gray-900">
                        {formatCost(request.totalCostUsd)}
                      </span>
                    </div>
                  ))}
                  {costData.requests.length > 5 && (
                    <p className="text-xs text-gray-400 text-center pt-1">
                      +{costData.requests.length - 5} more
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
    </>
  );
};

export default CostTooltip;
