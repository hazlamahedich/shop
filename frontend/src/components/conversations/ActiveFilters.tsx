/**
 * ActiveFilters Component
 *
 * Displays active filters as removable chips with visual indicators for each filter type.
 */

import { useConversationStore } from '../../stores/conversationStore';
import type { ConversationStatus, Sentiment } from '../../types/conversation';

const STATUS_LABELS: Record<ConversationStatus, string> = {
  active: 'Active',
  handoff: 'Handoff',
  closed: 'Closed',
};

const SENTIMENT_LABELS: Record<Sentiment, { label: string; emoji: string }> = {
  positive: { label: 'Positive', emoji: '😊' },
  neutral: { label: 'Neutral', emoji: '😐' },
  negative: { label: 'Negative', emoji: '😞' },
};

const getHandoffLabel = (hasHandoff: boolean): string => {
  return hasHandoff ? 'Has Handoff' : 'No Handoff';
};

export interface ActiveFiltersProps {
  className?: string;
}

export const ActiveFilters = ({ className = '' }: ActiveFiltersProps) => {
  const { filters, removeFilter, clearAllFilters } = useConversationStore();

  const hasActiveFilters =
    filters.searchQuery ||
    filters.dateRange.from ||
    filters.dateRange.to ||
    filters.statusFilters.length > 0 ||
    filters.sentimentFilters.length > 0 ||
    filters.hasHandoffFilter !== null;

  if (!hasActiveFilters) {
    return null;
  }

  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.searchQuery) count++;
    if (filters.dateRange.from || filters.dateRange.to) count++;
    count += filters.statusFilters.length;
    count += filters.sentimentFilters.length;
    if (filters.hasHandoffFilter !== null) count++;
    return count;
  };

  const handleRemoveFilter = (key: keyof typeof filters, value?: any) => {
    removeFilter(key, value);
  };

  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      <span className="text-[10px] font-bold text-emerald-500/50 uppercase tracking-widest mr-1">Active filters:</span>

      {/* Search Query */}
      {filters.searchQuery && (
        <FilterChip
          label={`Search: "${filters.searchQuery}"`}
          onRemove={() => handleRemoveFilter('searchQuery')}
          icon="🔍"
        />
      )}

      {/* Date Range */}
      {(filters.dateRange.from || filters.dateRange.to) && (
        <FilterChip
          label={`Date: ${filters.dateRange.from || '...'} to ${filters.dateRange.to || '...'}`}
          onRemove={() => handleRemoveFilter('dateRange')}
          icon="📅"
        />
      )}

      {/* Status Filters */}
      {filters.statusFilters.map((status) => (
        <FilterChip
          key={`status-${status}`}
          label={STATUS_LABELS[status]}
          onRemove={() => handleRemoveFilter('statusFilters', status)}
          color={status === 'active' ? 'emerald' : status === 'handoff' ? 'amber' : 'slate'}
        />
      ))}

      {/* Sentiment Filters */}
      {filters.sentimentFilters.map((sentiment) => (
        <FilterChip
          key={`sentiment-${sentiment}`}
          label={SENTIMENT_LABELS[sentiment].label}
          onRemove={() => handleRemoveFilter('sentimentFilters', sentiment)}
          icon={SENTIMENT_LABELS[sentiment].emoji}
          color="emerald"
        />
      ))}

      {/* Handoff Filter */}
      {filters.hasHandoffFilter !== null && (
        <FilterChip
          label={getHandoffLabel(filters.hasHandoffFilter)}
          onRemove={() => handleRemoveFilter('hasHandoffFilter')}
          icon="👥"
          color={filters.hasHandoffFilter ? 'emerald' : 'slate'}
        />
      )}

      {/* Clear All Button */}
      <button
        type="button"
        onClick={clearAllFilters}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-red-400 hover:text-red-300 bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 rounded-lg transition-all duration-300"
      >
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
        Reset ({getActiveFilterCount()})
      </button>
    </div>
  );
};

interface FilterChipProps {
  label: string;
  onRemove: () => void;
  icon?: string;
  color?: 'emerald' | 'amber' | 'slate';
}

const FilterChip = ({ label, onRemove, icon, color = 'emerald' }: FilterChipProps) => {
const colorClasses: Record<Exclude<typeof color, undefined>, string> = {
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 hover:text-emerald-300',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20 hover:text-amber-300',
    slate: 'bg-white/5 text-white/50 border-white/10 hover:bg-white/10 hover:text-white/70',
};

  return (
    <button
      type="button"
      onClick={onRemove}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wide transition-all duration-300 border focus:outline-none focus:ring-2 focus:ring-offset-w ${colorClasses[color]}`}
    >
      {icon && <span className="text-xs">{icon}</span>}
      <span>{label}</span>
      <svg className="w-3 h-3 ml-0.5 opacity-60 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  );
};
