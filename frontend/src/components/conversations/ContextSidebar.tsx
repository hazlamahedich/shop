/**
 * ContextSidebar Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Displays customer info, urgency config, handoff context, and bot state.
 */

import { Activity, Zap, UserCheck, Cpu } from 'lucide-react';
import type { ConversationContext, HandoffContext, CustomerInfo } from '../../types/conversation';

const URGENCY_CONFIG = {
  high: { color: '#FF8800', bgColor: '#FF880020', borderColor: '#FF880040', label: 'HIGH' },
  medium: { color: '#FF8800', bgColor: '#FF880010', borderColor: '#FF880020', label: 'MEDIUM' },
  low: { color: '#8a8a8a', bgColor: 'transparent', borderColor: '#2f2f2f', label: 'LOW' },
};

const HANDOFF_REASON_LABELS: Record<string, string> = {
  keyword: 'Customer requested human assistance via keyword trigger',
  low_confidence: 'Bot confidence threshold exceeded - escalation required',
  clarification_loop: 'Multiple clarification attempts detected - loop prevention',
};

function formatWaitTime(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) {
    return `${hours}h`;
  }
  return `${hours}h ${remainingMinutes}m`;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
}

interface ContextSidebarProps {
  customer: CustomerInfo;
  handoff: HandoffContext;
  context: ConversationContext;
}

export default function ContextSidebar({ customer, handoff, context }: ContextSidebarProps) {
  const urgencyConfig = URGENCY_CONFIG[handoff.urgencyLevel] || URGENCY_CONFIG.low;
  const hasCartItems = context.cartState?.items && context.cartState.items.length > 0;
  const hasConstraints = context.extractedConstraints && (
    context.extractedConstraints.budget ||
    context.extractedConstraints.size ||
    context.extractedConstraints.category
  );

  return (
    <div
      data-testid="context-sidebar"
      className="w-80 flex flex-col overflow-hidden"
      style={{ backgroundColor: '#080808', borderLeft: '1px solid #2f2f2f' }}
    >
      {/* Header */}
      <div 
        className="flex items-center gap-3 px-6 py-5"
        style={{ backgroundColor: '#0A0A0A', borderBottom: '1px solid #2f2f2f' }}
      >
        <Activity size={16} style={{ color: '#00FF88' }} />
        <span 
          className="text-[11px] font-bold uppercase tracking-[0.2em]"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FFFFFF' }}
        >
          Context Array
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Customer Section */}
        <div 
          className="px-6 py-5 space-y-4"
          style={{ backgroundColor: '#080808', borderBottom: '1px solid #2f2f2f' }}
        >
          <span 
            className="text-[9px] font-bold uppercase tracking-[0.1em]"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
          >
            // CUSTOMER_ID
          </span>
          <div className="space-y-3">
            <span 
              className="text-[13px] font-semibold block"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FFFFFF' }}
            >
              {customer.maskedId}
            </span>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                  ORDERS:
                </span>
                <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                  {customer.orderCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Urgency Config Section */}
        <div 
          className="px-6 py-5 space-y-4"
          style={{ backgroundColor: '#080808', borderBottom: '1px solid #2f2f2f' }}
        >
          <div className="flex items-center gap-3">
            <Zap size={14} style={{ color: '#FF8800' }} />
            <span 
              className="text-[10px] font-bold uppercase tracking-[0.1em]"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FF8800' }}
            >
              URGENCY_CONFIG
            </span>
          </div>

          <div 
            className="flex justify-between items-center px-4 py-3"
            style={{ backgroundColor: urgencyConfig.bgColor, border: `1px solid ${urgencyConfig.borderColor}` }}
          >
            <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
              LEVEL:
            </span>
            <span 
              className="text-[12px] font-bold"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: urgencyConfig.color }}
            >
              {urgencyConfig.label}
            </span>
          </div>

          <div className="space-y-2">
            <span className="text-[9px] font-bold block" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
              TRIGGER:
            </span>
            <p 
              className="text-[10px] font-medium leading-relaxed"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
            >
              {HANDOFF_REASON_LABELS[handoff.triggerReason] || handoff.triggerReason}
            </p>
          </div>
        </div>

        {/* Handoff Context Section */}
        <div 
          className="px-6 py-5 space-y-4"
          style={{ backgroundColor: '#080808', borderBottom: '1px solid #2f2f2f' }}
        >
          <div className="flex items-center gap-3">
            <UserCheck size={14} style={{ color: '#00FF88' }} />
            <span 
              className="text-[10px] font-bold uppercase tracking-[0.1em]"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}
            >
              HANDOFF_CONTEXT
            </span>
          </div>

          <div 
            className="flex justify-between items-center px-4 py-3"
            style={{ backgroundColor: '#00FF8810', border: '1px solid #00FF8840' }}
          >
            <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
              STATUS:
            </span>
            <span 
              className="text-[12px] font-bold"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}
            >
              REQUESTED
            </span>
          </div>

          <div className="space-y-2">
            <span className="text-[9px] font-bold block" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
              QUEUE_TIME:
            </span>
            <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
              {formatWaitTime(handoff.waitTimeSeconds)}
            </span>
          </div>

          {handoff.triggeredAt && (
            <div className="space-y-2">
              <span className="text-[9px] font-bold block" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                TRIGGERED_AT:
              </span>
              <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                {formatTimestamp(handoff.triggeredAt)}
              </span>
            </div>
          )}
        </div>

        {/* Bot State Section */}
        <div 
          className="px-6 py-5 space-y-4"
          style={{ backgroundColor: '#080808' }}
        >
          <div className="flex items-center gap-3">
            <Cpu size={14} style={{ color: '#8a8a8a' }} />
            <span 
              className="text-[10px] font-bold uppercase tracking-[0.1em]"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
            >
              BOT_STATE
            </span>
          </div>

          <div 
            className="flex justify-between items-center px-4 py-3"
            style={{ backgroundColor: '#0A0A0A', border: '1px solid #2f2f2f' }}
          >
            <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
              MODE:
            </span>
            <span 
              className="text-[12px] font-bold"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
            >
              ASSISTANT
            </span>
          </div>

          {/* Cart State */}
          {hasCartItems && (
            <div className="space-y-3 pt-3" style={{ borderTop: '1px solid #2f2f2f' }}>
              <span className="text-[9px] font-bold block uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                CART_ITEMS:
              </span>
              <div className="space-y-1">
                {context.cartState?.items.map((item, index) => (
                  <div 
                    key={index} 
                    className="flex justify-between items-center px-3 py-2"
                    style={{ backgroundColor: '#0A0A0A', border: '1px solid #2f2f2f' }}
                  >
                    <span className="text-[10px] font-medium truncate mr-2" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                      {item.name}
                    </span>
                    <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                      x{item.quantity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted Constraints */}
          {hasConstraints && (
            <div className="space-y-3 pt-3" style={{ borderTop: '1px solid #2f2f2f' }}>
              <span className="text-[9px] font-bold block uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                CONSTRAINTS:
              </span>
              <div className="space-y-2">
                {context.extractedConstraints?.budget && (
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] font-bold uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                      BUDGET
                    </span>
                    <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                      {context.extractedConstraints.budget}
                    </span>
                  </div>
                )}
                {context.extractedConstraints?.size && (
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] font-bold uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                      SIZE
                    </span>
                    <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                      {context.extractedConstraints.size}
                    </span>
                  </div>
                )}
                {context.extractedConstraints?.category && (
                  <div className="flex justify-between items-center">
                    <span className="text-[9px] font-bold uppercase" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                      CATEGORY
                    </span>
                    <span className="text-[10px] font-medium" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                      {context.extractedConstraints.category}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
