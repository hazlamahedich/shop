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
      className="w-80 bg-gray-50 border-l border-gray-200 p-4 overflow-y-auto"
    >
      {/* Customer Info Section */}
      <section data-testid="customer-info-section" className="mb-6">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
          <User size={16} />
          Customer Info
        </h3>
        <div className="bg-white rounded-lg p-3 border border-gray-200">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">ID</span>
              <span className="font-mono text-gray-900">{customer.maskedId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Orders</span>
              <span className="text-gray-900">{customer.orderCount}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Handoff Context Section */}
      <section data-testid="handoff-context-section" className="mb-6">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
          <Clock size={16} />
          Handoff Context
        </h3>
        <div className="bg-white rounded-lg p-3 border border-gray-200 space-y-3">
          {/* Wait Time */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Waiting</span>
            <span className="text-sm font-medium text-gray-900">
              {formatWaitTime(handoff.waitTimeSeconds)}
            </span>
          </div>

          {/* Urgency Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-500">Urgency</span>
            <span
              data-testid="urgency-badge"
              className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${urgencyConfig.bg} ${urgencyConfig.color}`}
            >
              {urgencyConfig.emoji} {urgencyConfig.label}
            </span>
          </div>

          {/* Trigger Reason */}
          <div>
            <span className="text-sm text-gray-500 block mb-1">Reason</span>
            <span className="text-sm text-gray-900">
              {HANDOFF_REASON_LABELS[handoff.triggerReason] || handoff.triggerReason}
            </span>
          </div>
        </div>
      </section>

      {/* Bot Internal State Section */}
      <section data-testid="bot-state-section">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 mb-3">
          <Tag size={16} />
          Bot State
        </h3>
        <div className="bg-white rounded-lg p-3 border border-gray-200 space-y-4">
          {/* Cart Contents */}
          <div>
            <h4 className="flex items-center gap-1 text-xs font-medium text-gray-500 mb-2">
              <ShoppingCart size={12} />
              Cart
            </h4>
            {hasCartItems ? (
              <ul className="space-y-1">
                {context.cartState?.items.map((item, index) => (
                  <li
                    key={index}
                    className="text-sm text-gray-700 flex justify-between"
                  >
                    <span className="truncate mr-2">{item.name}</span>
                    <span className="text-gray-500">x{item.quantity}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400 italic">No items in cart</p>
            )}
          </div>

          {/* Extracted Constraints */}
          <div>
            <h4 className="text-xs font-medium text-gray-500 mb-2">Detected Constraints</h4>
            {hasConstraints ? (
              <div className="space-y-1 text-sm">
                {context.extractedConstraints?.budget && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Budget</span>
                    <span className="text-gray-900">{context.extractedConstraints.budget}</span>
                  </div>
                )}
                {context.extractedConstraints?.size && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Size</span>
                    <span className="text-gray-900">{context.extractedConstraints.size}</span>
                  </div>
                )}
                {context.extractedConstraints?.category && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Category</span>
                    <span className="text-gray-900">{context.extractedConstraints.category}</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-gray-400 italic">No constraints detected</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
