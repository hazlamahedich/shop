/**
 * ConversationCostDetail Component
 *
 * Displays detailed cost breakdown for a conversation:
 * - Summary statistics (total cost, tokens, requests, avg cost)
 * - Provider/model information
 * - Request-by-request breakdown with timestamps, token counts, and costs
 *
 * Story 3-5: Real-Time Cost Tracking
 */

import React, { useEffect } from 'react';
import { DollarSign, Hash, Clock, Cpu, Loader2, AlertCircle } from 'lucide-react';
import { useCostTrackingStore } from '../../stores/costTrackingStore';
import { formatCost, formatTokens } from '../../types/cost';
import type { CostRecord } from '../../types/cost';

interface ConversationCostDetailProps {
  conversationId: string;
}

// Format timestamp for display
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// Format processing time
const formatProcessingTime = (ms?: number): string => {
  if (!ms) return 'N/A';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
};

// Stat card component
const StatCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: string | number;
  colorClass?: string;
}> = ({ icon, label, value, colorClass = 'text-gray-900' }) => (
  <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
    <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-white rounded-lg shadow-sm">
      {icon}
    </div>
    <div>
      <p className="text-xs text-gray-500 uppercase tracking-wide">{label}</p>
      <p className={`text-lg font-semibold ${colorClass}`}>{value}</p>
    </div>
  </div>
);

// Request row component
const RequestRow: React.FC<{ request: CostRecord; index: number }> = ({ request, index }) => (
  <tr className="hover:bg-gray-50 transition-colors">
    <td className="px-4 py-3 text-sm text-gray-500">#{index + 1}</td>
    <td className="px-4 py-3 text-sm text-gray-900 font-medium">
      {formatTimestamp(request.requestTimestamp)}
    </td>
    <td className="px-4 py-3">
      <div className="flex items-center space-x-2">
        <span className="px-2 py-1 text-xs font-medium bg-blue-50 text-blue-700 rounded">
          {request.provider}
        </span>
        <span className="text-xs text-gray-600">{request.model}</span>
      </div>
    </td>
    <td className="px-4 py-3 text-sm text-gray-900">
      {formatTokens(request.promptTokens)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-900">
      {formatTokens(request.completionTokens)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-900">
      {formatTokens(request.totalTokens)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-900 text-right">
      {formatCost(request.inputCostUsd, 6)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-900 text-right">
      {formatCost(request.outputCostUsd, 6)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-900 text-right font-semibold">
      {formatCost(request.totalCostUsd)}
    </td>
    <td className="px-4 py-3 text-sm text-gray-500 text-right">
      {formatProcessingTime(request.processingTimeMs)}
    </td>
  </tr>
);

export const ConversationCostDetail: React.FC<ConversationCostDetailProps> = ({
  conversationId,
}) => {
  const {
    conversationCosts,
    conversationCostsLoading,
    conversationCostsError,
    fetchConversationCost,
  } = useCostTrackingStore();

  const costData = conversationCosts[conversationId];
  const isLoading = conversationCostsLoading[conversationId];
  const error = conversationCostsError[conversationId];

  // Fetch cost data on mount
  useEffect(() => {
    if (!costData && !error) {
      fetchConversationCost(conversationId);
    }
  }, [conversationId, costData, error, fetchConversationCost]);

  // Loading state
  if (isLoading && !costData) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-sm text-gray-500">Loading cost details...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !costData) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="flex flex-col items-center space-y-3 text-center">
          <AlertCircle className="w-8 h-8 text-red-500" />
          <p className="text-sm text-gray-900 font-medium">Failed to load cost details</p>
          <p className="text-sm text-gray-500 max-w-md">{error}</p>
          <button
            onClick={() => fetchConversationCost(conversationId)}
            className="mt-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No data state
  if (!costData) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <DollarSign className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">No cost data available for this conversation</p>
        </div>
      </div>
    );
  }

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
    <div className="space-y-6">
      {/* Header with conversation info */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Cost Breakdown</h3>
          <p className="text-sm text-gray-500">
            Conversation ID: <span className="font-mono">{conversationId}</span>
          </p>
        </div>
        {costData.provider && (
          <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-lg">
            <Cpu size={16} className="text-gray-400" />
            <span className="text-sm font-medium text-gray-700">{costData.provider}</span>
            <span className="text-xs text-gray-500">/</span>
            <span className="text-sm text-gray-600">{costData.model}</span>
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<DollarSign size={18} className="text-blue-600" />}
          label="Total Cost"
          value={formatCost(costData.totalCostUsd)}
          colorClass={costColorClass}
        />
        <StatCard
          icon={<Hash size={18} className="text-purple-600" />}
          label="Total Tokens"
          value={formatTokens(costData.totalTokens)}
        />
        <StatCard
          icon={<Clock size={18} className="text-green-600" />}
          label="Requests"
          value={costData.requestCount}
        />
        <StatCard
          icon={<Cpu size={18} className="text-orange-600" />}
          label="Avg Cost/Request"
          value={formatCost(costData.avgCostPerRequest)}
        />
      </div>

      {/* Request Breakdown Table */}
      {costData.requests.length > 0 ? (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-900">
              Request Details ({costData.requests.length})
            </h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    #
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider / Model
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Prompt
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Completion
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Total
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Input Cost
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Output Cost
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Total Cost
                  </th>
                  <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">
                    Processing Time
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {costData.requests.map((request, index) => (
                  <RequestRow key={request.id} request={request} index={index} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-center p-8 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-500">No individual request records available</p>
        </div>
      )}
    </div>
  );
};

export default ConversationCostDetail;
