/**
 * ConversationCard Component
 *
 * Displays a single conversation in the list with:
 * - Masked customer ID
 * - Last message preview
 * - Status badge
 * - Message count
 * - Updated time
 */

import React from 'react';
import { MessageSquare, Clock } from 'lucide-react';
import type {
  Conversation as ConversationType,
  ConversationStatus,
} from '../../types/conversation';

interface ConversationCardProps {
  conversation: ConversationType;
  onClick?: () => void;
}

const statusStyles: Record<ConversationStatus, string> = {
  active: 'bg-green-100 text-green-700',
  handoff: 'bg-yellow-100 text-yellow-700',
  closed: 'bg-gray-100 text-gray-700',
};

const statusLabels: Record<ConversationStatus, string> = {
  active: 'Active',
  handoff: 'Handoff',
  closed: 'Closed',
};

// Format timestamp relative to now
const formatTimestamp = (timestamp: string): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  return date.toLocaleDateString();
};

export const ConversationCard: React.FC<ConversationCardProps> = ({ conversation, onClick }) => {
  return (
    <div
      onClick={onClick}
      data-testid="conversation-card"
      className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      {/* Header: Customer ID and time */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center space-x-2">
          <MessageSquare size={14} className="text-gray-400" />
          <h4 className="font-medium text-sm text-gray-900">
            {conversation.platformSenderIdMasked}
          </h4>
        </div>
        <span className="flex items-center text-xs text-gray-400">
          <Clock size={12} className="mr-1" />
          {formatTimestamp(conversation.updatedAt)}
        </span>
      </div>

      {/* Last message preview */}
      <p className="text-sm text-gray-600 truncate mb-2">
        {conversation.lastMessage || 'No messages yet'}
      </p>

      {/* Footer: Status badge and message count */}
      <div className="flex items-center justify-between">
        <span
          className={`px-2 py-0.5 text-[11px] font-medium rounded-full ${
            statusStyles[conversation.status]
          }`}
        >
          {statusLabels[conversation.status]}
        </span>

        {conversation.messageCount > 0 && (
          <span className="text-xs text-gray-400">
            {conversation.messageCount} {conversation.messageCount === 1 ? 'message' : 'messages'}
          </span>
        )}
      </div>
    </div>
  );
};

export default ConversationCard;
