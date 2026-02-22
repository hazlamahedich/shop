/**
 * ConversationCard Component
 *
 * Displays a single conversation in the list with:
 * - Masked customer ID
 * - Source badge (Widget/Messenger/Preview)
 * - Last message preview
 * - Status badge
 * - Message count
 * - Created date and updated time
 *
 * Uses business timezone for timestamp calculations (from businessHoursStore).
 */

import React from 'react';
import { MessageSquare, Clock, Globe, MessageCircle, Eye } from 'lucide-react';
import type {
  Conversation as ConversationType,
  ConversationStatus,
} from '../../types/conversation';
import { useBusinessHoursStore } from '../../stores/businessHoursStore';

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

interface PlatformConfig {
  icon: React.ReactNode;
  label: string;
  className: string;
}

const platformConfigs: Record<string, PlatformConfig> = {
  widget: {
    icon: <Globe size={12} />,
    label: 'Website Chat',
    className: 'bg-blue-50 text-blue-600',
  },
  messenger: {
    icon: <MessageCircle size={12} />,
    label: 'Messenger',
    className: 'bg-indigo-50 text-indigo-600',
  },
  preview: {
    icon: <Eye size={12} />,
    label: 'Preview',
    className: 'bg-purple-50 text-purple-600',
  },
};

const getPlatformConfig = (platform: string): PlatformConfig => {
  const safePlatform = platform || 'unknown';
  return platformConfigs[safePlatform] || {
    icon: <MessageSquare size={12} />,
    label: safePlatform.charAt(0).toUpperCase() + safePlatform.slice(1),
    className: 'bg-gray-50 text-gray-600',
  };
};

const parseAsUTC = (timestamp: string): Date => {
  if (timestamp.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(timestamp)) {
    return new Date(timestamp);
  }
  return new Date(timestamp + 'Z');
};

const formatTimestamp = (timestamp: string, timezone?: string): string => {
  const date = parseAsUTC(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffHours < 24) return `${diffHours}h`;
  if (diffDays < 7) return `${diffDays}d`;
  
  try {
    return date.toLocaleDateString(undefined, timezone ? { timeZone: timezone } : undefined);
  } catch {
    return date.toLocaleDateString();
  }
};

const formatCreatedDate = (timestamp: string, timezone?: string): string => {
  const date = parseAsUTC(timestamp);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / 86400000);

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  
  try {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      timeZone: timezone 
    });
  } catch {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  }
};

export const ConversationCard: React.FC<ConversationCardProps> = ({ conversation, onClick }) => {
  const timezone = useBusinessHoursStore((state) => state.config?.timezone);
  const platformConfig = getPlatformConfig(conversation.platform);

  return (
    <div
      onClick={onClick}
      data-testid="conversation-card"
      className="p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
    >
      {/* Header: Source badge and updated time */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-full ${platformConfig.className}`}>
            {platformConfig.icon}
            {platformConfig.label}
          </span>
        </div>
        <span className="flex items-center text-xs text-gray-400">
          <Clock size={12} className="mr-1" />
          {formatTimestamp(conversation.updatedAt, timezone)}
        </span>
      </div>

      {/* Customer ID and created date */}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center space-x-2">
          <MessageSquare size={14} className="text-gray-400" />
          <h4 className="font-medium text-sm text-gray-900">
            {conversation.platformSenderIdMasked}
          </h4>
        </div>
        <span className="text-xs text-gray-400">
          Created: {formatCreatedDate(conversation.createdAt, timezone)}
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
