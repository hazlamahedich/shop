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
      <span className="text-sm text-gray-500">Active filters:</span>

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
          color="blue"
        />
      ))}

      {/* Sentiment Filters */}
      {filters.sentimentFilters.map((sentiment) => (
        <FilterChip
          key={`sentiment-${sentiment}`}
          label={SENTIMENT_LABELS[sentiment].label}
          onRemove={() => handleRemoveFilter('sentimentFilters', sentiment)}
          icon={SENTIMENT_LABELS[sentiment].emoji}
          color="purple"
        />
      ))}

      {/* Handoff Filter */}
      {filters.hasHandoffFilter !== null && (
        <FilterChip
          label={getHandoffLabel(filters.hasHandoffFilter)}
          onRemove={() => handleRemoveFilter('hasHandoffFilter')}
          icon="👥"
          color={filters.hasHandoffFilter ? 'yellow' : 'gray'}
        />
      )}

      {/* Clear All Button */}
      <button
        type="button"
        onClick={clearAllFilters}
        className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
        Clear all ({getActiveFilterCount()})
      </button>
    </div>
  );
};

interface FilterChipProps {
  label: string;
  onRemove: () => void;
  icon?: string;
  color?: 'blue' | 'purple' | 'yellow' | 'gray';
}

const FilterChip = ({ label, onRemove, icon, color = 'blue' }: FilterChipProps) => {
  const colorClasses: Record<Exclude<typeof color, undefined>, string> = {
    blue: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
    purple: 'bg-purple-100 text-purple-800 hover:bg-purple-200',
    yellow: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    gray: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
  };

  return (
    <button
      type="button"
      onClick={onRemove}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 ${colorClasses[color]}`}
    >
      {icon && <span>{icon}</span>}
      <span>{label}</span>
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  );
};
