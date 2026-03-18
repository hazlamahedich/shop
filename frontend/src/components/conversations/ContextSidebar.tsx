/**
 * ContextSidebar Component - Story 4-8: Conversation History View
 *
 * Displays customer info, handoff context, and bot internal state.
 */

import React from 'react';
import { User, Clock, ShoppingCart, Tag } from 'lucide-react';
import type { ConversationContext, HandoffContext, CustomerInfo } from '../../types/conversation';

const URGENCY_CONFIG = {
  high: { emoji: '🔴', label: 'High', color: 'text-red-600', bg: 'bg-red-50' },
  medium: { emoji: '🟡', label: 'Medium', color: 'text-yellow-600', bg: 'bg-yellow-50' },
  low: { emoji: '🟢', label: 'Low', color: 'text-green-600', bg: 'bg-green-50' },
};

const HANDOFF_REASON_LABELS: Record<string, string> = {
  keyword: 'Customer requested human help',
  low_confidence: 'Bot needed assistance',
  clarification_loop: 'Multiple clarification attempts',
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
      className="w-85 bg-[#0a0a0a]/60 backdrop-blur-2xl border-l border-emerald-500/10 p-6 overflow-y-auto custom-scrollbar relative z-20"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/[0.02] to-transparent pointer-events-none"></div>

      {/* Customer Info Section */}
      <section data-testid="customer-info-section" className="mb-10 relative">
        <h3 className="flex items-center gap-2.5 text-[10px] font-bold text-emerald-500 uppercase tracking-[0.2em] mb-4">
          <User size={14} className="text-emerald-500/80" />
          Customer Protocol
        </h3>
        <div className="bg-white/5 rounded-2xl p-5 border border-white/5 backdrop-blur-md shadow-2xl">
          <div className="space-y-4">
            <div className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Identification</span>
              <span className="font-mono text-sm text-slate-100 bg-black/40 px-2.5 py-1.5 rounded-lg border border-white/5">{customer.maskedId}</span>
            </div>
            <div className="flex items-center justify-between pt-2 border-t border-white/5">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Experience Level</span>
              <span className="text-sm font-bold text-emerald-400">
                {customer.orderCount} Order{customer.orderCount !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Handoff Context Section */}
      <section data-testid="handoff-context-section" className="mb-10 relative">
        <h3 className="flex items-center gap-2.5 text-[10px] font-bold text-emerald-500 uppercase tracking-[0.2em] mb-4">
          <Clock size={14} className="text-emerald-500/80" />
          Handoff Matrix
        </h3>
        <div className="bg-white/5 rounded-2xl p-5 border border-white/5 backdrop-blur-md shadow-2xl space-y-4">
          {/* Wait Time */}
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">Queue Time</span>
            <span className="text-sm font-black text-slate-100">
              {formatWaitTime(handoff.waitTimeSeconds)}
            </span>
          </div>

          {/* Urgency Badge */}
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">Threat Level</span>
            <div
              data-testid="urgency-badge"
              className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest border transition-all duration-300 shadow-[0_4px_12px_rgba(0,0,0,0.5)]`}
              style={{ 
                backgroundColor: handoff.urgencyLevel === 'high' ? 'rgba(239, 68, 68, 0.15)' : handoff.urgencyLevel === 'medium' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                borderColor: handoff.urgencyLevel === 'high' ? 'rgba(239, 68, 68, 0.3)' : handoff.urgencyLevel === 'medium' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(16, 185, 129, 0.3)',
                color: handoff.urgencyLevel === 'high' ? '#f87171' : handoff.urgencyLevel === 'medium' ? '#fbbf24' : '#34d399'
              }}
            >
              {urgencyConfig.label}
            </div>
          </div>

          {/* Trigger Reason */}
          <div className="pt-3 border-t border-white/5">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-2 font-mono">Analysis</span>
            <p className="text-xs font-medium text-slate-300 leading-relaxed italic">
              "{HANDOFF_REASON_LABELS[handoff.triggerReason] || handoff.triggerReason}"
            </p>
          </div>
        </div>
      </section>

      {/* Bot Internal State Section */}
      <section data-testid="bot-state-section" className="relative">
        <h3 className="flex items-center gap-2.5 text-[10px] font-bold text-emerald-500 uppercase tracking-[0.2em] mb-4">
          <Tag size={14} className="text-emerald-500/80" />
          Neural State
        </h3>
        <div className="bg-white/5 rounded-2xl p-5 border border-white/5 backdrop-blur-md shadow-2xl space-y-6">
          {/* Cart Contents */}
          <div>
            <h4 className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 font-mono">
              <ShoppingCart size={12} className="text-emerald-500/40" />
              Inventory
            </h4>
            {hasCartItems ? (
              <ul className="space-y-2">
                {context.cartState?.items.map((item, index) => (
                  <li
                    key={index}
                    className="text-xs font-medium text-slate-300 flex justify-between group bg-black/20 p-2 rounded-lg border border-white/5 hover:border-emerald-500/20 transition-all"
                  >
                    <span className="truncate mr-2 group-hover:text-emerald-400 transition-colors">{item.name}</span>
                    <span className="text-emerald-500 font-mono">×{item.quantity}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs font-medium text-slate-600 italic">No assets detected</p>
            )}
          </div>

          {/* Extracted Constraints */}
          <div className="pt-4 border-t border-white/5">
            <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 font-mono">Parameters</h4>
            {hasConstraints ? (
              <div className="space-y-2">
                {context.extractedConstraints?.budget && (
                  <div className="flex items-center justify-between bg-black/20 p-2 rounded-lg border border-white/5">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Budget</span>
                    <span className="text-xs font-bold text-slate-200">{context.extractedConstraints.budget}</span>
                  </div>
                )}
                {context.extractedConstraints?.size && (
                  <div className="flex items-center justify-between bg-black/20 p-2 rounded-lg border border-white/5">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Size</span>
                    <span className="text-xs font-bold text-slate-200">{context.extractedConstraints.size}</span>
                  </div>
                )}
                {context.extractedConstraints?.category && (
                  <div className="flex items-center justify-between bg-black/20 p-2 rounded-lg border border-white/5">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Category</span>
                    <span className="text-xs font-bold text-slate-200">{context.extractedConstraints.category}</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs font-medium text-slate-600 italic">No specific constraints</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
