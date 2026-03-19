/**
 * ConversationCard Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Displays conversation status, customer ID, platform, message preview, and metrics.
 */

import React from 'react';
import { MessageSquare, Globe, MessageCircle, Eye } from 'lucide-react';
import type {
  Conversation as ConversationType,
  ConversationStatus,
} from '../../types/conversation';

interface ConversationCardProps {
  conversation: ConversationType;
  onClick?: () => void;
}

const statusConfig: Record<ConversationStatus, { color: string; bgColor: string; borderColor: string; label: string }> = {
  active: { color: '#00FF88', bgColor: '#00FF8810', borderColor: '#00FF8840', label: 'OPEN' },
  handoff: { color: '#FF8800', bgColor: '#FF880020', borderColor: '#FF880040', label: 'HANDOFF' },
  closed: { color: '#6a6a6a', bgColor: 'transparent', borderColor: '#2f2f2f', label: 'CLOSED' },
};

interface PlatformConfig {
  icon: React.ReactNode;
  label: string;
}

const platformConfigs: Record<string, PlatformConfig> = {
  widget: { icon: <Globe size={14} />, label: 'WIDGET' },
  messenger: { icon: <MessageCircle size={14} />, label: 'MESSENGER' },
  preview: { icon: <Eye size={14} />, label: 'PREVIEW' },
};

const getPlatformConfig = (platform: string): PlatformConfig => {
  const safePlatform = platform || 'unknown';
  return platformConfigs[safePlatform] || {
    icon: <MessageSquare size={14} />,
    label: safePlatform.toUpperCase(),
  };
};

const parseAsUTC = (timestamp: string): Date => {
  if (timestamp.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(timestamp)) {
    return new Date(timestamp);
  }
  return new Date(timestamp + 'Z');
};

const formatTimestamp = (timestamp: string): string => {
  const date = parseAsUTC(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'NOW';
  if (diffMins < 60) return `${diffMins} MIN AGO`;
  if (diffHours < 24) return `${diffHours} HR AGO`;
  if (diffDays === 1) return '1 DAY AGO';
  if (diffDays < 7) return `${diffDays} DAYS AGO`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toUpperCase();
};

const ConversationCard: React.FC<ConversationCardProps> = ({ conversation, onClick }) => {
  const platformConfig = getPlatformConfig(conversation.platform);
  const status = statusConfig[conversation.status];

  return (
    <div
      onClick={onClick}
      data-testid="conversation-card"
      className="flex items-center gap-5 px-6 py-5 cursor-pointer transition-all duration-200 group relative"
      style={{
        backgroundColor: '#0A0A0A',
        borderBottom: '1px solid #2f2f2f',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#080808';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = '#0A0A0A';
      }}
    >
      {/* Status Indicator */}
      <div className="flex items-center gap-3 w-28 flex-shrink-0">
        <div
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{
            backgroundColor: status.color,
            boxShadow: conversation.status === 'active' ? `0 0 8px ${status.color}` : 'none',
          }}
        />
        <span
          className="text-[10px] font-bold uppercase tracking-widest"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: status.color }}
        >
          [{status.label}]
        </span>
      </div>

      {/* Content Section */}
      <div className="flex-1 min-w-0">
        {/* Header Row */}
        <div className="flex items-center gap-3 mb-2">
          <span
            className="text-[13px] font-semibold"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FFFFFF' }}
          >
            {conversation.platformSenderIdMasked}
          </span>
          <span
            className="text-[10px] font-medium"
            style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
          >
            // {platformConfig.label}
          </span>
        </div>

        {/* Message Preview */}
        <p
          className="text-[12px] font-medium truncate"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
        >
          {conversation.lastMessage || 'No messages in queue'}
        </p>
      </div>

      {/* Meta Section */}
      <div className="flex flex-col items-end gap-2 flex-shrink-0">
        <span
          className="text-[10px] font-semibold uppercase tracking-wider"
          style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
        >
          {formatTimestamp(conversation.updatedAt)}
        </span>

        {conversation.messageCount > 0 && (
          <div className="flex items-center gap-2">
            <span
              className="text-[9px] font-semibold"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}
            >
              MSGS:
            </span>
            <span
              className="text-[11px] font-bold"
              style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}
            >
              {conversation.messageCount}
            </span>
          </div>
        )}
      </div>

      {/* Hover indicator line */}
      <div
        className="absolute bottom-0 left-0 h-px transition-all duration-300 opacity-0 group-hover:opacity-100"
        style={{
          backgroundColor: status.color,
          boxShadow: `0 0 10px ${status.color}`,
          width: '100%',
        }}
      />
    </div>
  );
};

export default ConversationCard;
