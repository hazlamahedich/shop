import React from 'react';
import { ArrowDown } from 'lucide-react';

interface NarrativeFlowConnectorProps {
  className?: string;
  animated?: boolean;
}

/**
 * Visual connector between narrative sections
 * Guides the user's eye through the story flow
 */
export function NarrativeFlowConnector({
  className = '',
  animated = true,
}: NarrativeFlowConnectorProps) {
  return (
    <div className={`flex items-center justify-center py-6 ${className}`}>
      <div className="flex items-center gap-4 text-white/10">
        {/* Left line */}
        <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/20 to-transparent" />

        {/* Arrow with optional animation */}
        <div
          className={`p-1.5 rounded-full border border-white/10 bg-white/5 ${
            animated ? 'animate-bounce' : ''
          }`}
        >
          <ArrowDown size={16} className="text-white/20" strokeWidth={2.5} />
        </div>

        {/* Right line */}
        <div className="h-px flex-1 bg-gradient-to-l from-transparent via-white/20 to-transparent" />
      </div>
    </div>
  );
}

/**
 * Compact horizontal connector for inline flow indicators
 */
export function FlowConnector({
  direction = 'right',
  className = '',
}: {
  direction?: 'right' | 'left';
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`h-px w-8 bg-gradient-to-r ${
          direction === 'right'
            ? 'from-white/10 to-white/30'
            : 'from-white/30 to-white/10'
        }`}
      />
      <div
        className={`w-1.5 h-1.5 rounded-full ${
          direction === 'right' ? 'bg-white/30' : 'bg-white/10'
        }`}
      />
    </div>
  );
}

export default NarrativeFlowConnector;
