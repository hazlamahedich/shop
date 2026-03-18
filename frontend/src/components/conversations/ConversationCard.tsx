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
  active: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 shadow-[0_0_10px_rgba(16,185,129,0.1)]',
  handoff: 'bg-amber-500/20 text-amber-400 border border-amber-500/30 shadow-[0_0_10px_rgba(245,158,11,0.1)]',
  closed: 'bg-slate-500/20 text-slate-400 border border-slate-500/30',
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
    className: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
  },
  messenger: {
    icon: <MessageCircle size={12} />,
    label: 'Messenger',
    className: 'bg-blue-500/10 text-blue-400 border border-blue-500/20',
  },
  preview: {
    icon: <Eye size={12} />,
    label: 'Preview',
    className: 'bg-slate-500/10 text-slate-400 border border-slate-500/20',
  },
};

const getPlatformConfig = (platform: string): PlatformConfig => {
  const safePlatform = platform || 'unknown';
  return platformConfigs[safePlatform] || {
    icon: <MessageSquare size={12} />,
    label: safePlatform.charAt(0).toUpperCase() + safePlatform.slice(1),
    className: 'bg-white/5 text-slate-400 border border-white/10',
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

const ConversationCard: React.FC<ConversationCardProps> = ({ conversation, onClick }) => {
  const timezone = useBusinessHoursStore((state) => state.config?.timezone);
  const platformConfig = getPlatformConfig(conversation.platform);

  return (
    <div
      onClick={onClick}
      data-testid="conversation-card"
      className="p-6 border-b border-emerald-500/5 hover:bg-emerald-500/[0.03] cursor-pointer transition-all duration-300 group relative overflow-hidden"
    >
      <div className="absolute inset-y-0 left-0 w-1 bg-emerald-500 scale-y-0 group-hover:scale-y-100 transition-transform duration-500 origin-center shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
      
      {/* Header: Source badge and updated time */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center space-x-2">
          <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-[10px] font-bold tracking-wider uppercase rounded-lg ${platformConfig.className}`}>
            {platformConfig.icon}
            {platformConfig.label}
          </span>
        </div>
        <span className="flex items-center text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-black/20 px-2 py-1 rounded-md">
          <Clock size={12} className="mr-1.5 text-emerald-500/70" />
          {formatTimestamp(conversation.updatedAt, timezone)}
        </span>
      </div>

      {/* Customer ID and created date */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-emerald-500/10 rounded-xl text-emerald-400 group-hover:bg-emerald-500/20 transition-colors duration-300">
            <MessageSquare size={18} />
          </div>
          <h4 className="font-bold text-base text-slate-100 group-hover:text-emerald-400 transition-colors duration-300">
            {conversation.platformSenderIdMasked}
          </h4>
        </div>
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-white/5 px-2 py-1 rounded-md border border-white/5">
          {formatCreatedDate(conversation.createdAt, timezone)}
        </span>
      </div>

      {/* Last message preview */}
      <p className="text-sm text-slate-400 line-clamp-2 mb-5 group-hover:text-slate-300 transition-colors duration-300 leading-relaxed pl-12">
        {conversation.lastMessage || 'No messages yet'}
      </p>

      {/* Footer: Status badge and message count */}
      <div className="flex items-center justify-between pl-12">
        <span
          className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider rounded-xl transition-all duration-300 ${
            statusStyles[conversation.status]
          }`}
        >
          {statusLabels[conversation.status]}
        </span>

        {conversation.messageCount > 0 && (
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border border-white/5 px-2.5 py-1 rounded-lg bg-black/20">
            {conversation.messageCount} messages
          </span>
        )}
      </div>
    </div>
  );
};

export default ConversationCard;
