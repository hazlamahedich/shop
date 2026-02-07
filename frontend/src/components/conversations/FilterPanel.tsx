/**
 * FilterPanel Component
 *
 * Panel with filter options for date range, status, sentiment, and handoff.
 * Note: The toggle button is handled by the parent component.
 */

import { useState } from 'react';
import { useConversationStore } from '../../stores/conversationStore';
import type { ConversationStatus, Sentiment } from '../../types/conversation';

const STATUS_OPTIONS: { value: ConversationStatus; label: string; color: string }[] = [
  { value: 'active', label: 'Active', color: 'bg-green-100 text-green-800' },
  { value: 'handoff', label: 'Handoff', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'closed', label: 'Closed', color: 'bg-gray-100 text-gray-800' },
];

const SENTIMENT_OPTIONS: { value: Sentiment; label: string; emoji: string }[] = [
  { value: 'positive', label: 'Positive', emoji: '😊' },
  { value: 'neutral', label: 'Neutral', emoji: '😐' },
  { value: 'negative', label: 'Negative', emoji: '😞' },
];

export const FilterPanel = () => {
  const {
    filters,
    setDateRange,
    setStatusFilters,
    setSentimentFilters,
    setHasHandoffFilter,
    clearAllFilters,
  } = useConversationStore();

  const [dateFrom, setDateFrom] = useState(filters.dateRange.from || '');
  const [dateTo, setDateTo] = useState(filters.dateRange.to || '');

  const handleDateFromChange = (value: string) => {
    setDateFrom(value);
    setDateRange(value || null, filters.dateRange.to);
  };

  const handleDateToChange = (value: string) => {
    setDateTo(value);
    setDateRange(filters.dateRange.from, value || null);
  };

  const toggleStatus = (status: ConversationStatus) => {
    const newStatuses = filters.statusFilters.includes(status)
      ? filters.statusFilters.filter((s) => s !== status)
      : [...filters.statusFilters, status];
    setStatusFilters(newStatuses);
  };

  const toggleSentiment = (sentiment: Sentiment) => {
    const newSentiments = filters.sentimentFilters.includes(sentiment)
      ? filters.sentimentFilters.filter((s) => s !== sentiment)
      : [...filters.sentimentFilters, sentiment];
    setSentimentFilters(newSentiments);
  };

  const hasActiveFilters =
    filters.searchQuery ||
    filters.dateRange.from ||
    filters.dateRange.to ||
    filters.statusFilters.length > 0 ||
    filters.sentimentFilters.length > 0 ||
    filters.hasHandoffFilter !== null;

  const handleClearAll = () => {
    setDateFrom('');
    setDateTo('');
    clearAllFilters();
  };

  return (
    <div className="space-y-6">
      {/* Date Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Date Range
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="date-from" className="block text-xs text-gray-500 mb-1">
              From
            </label>
            <input
              type="date"
              id="date-from"
              name="date-from"
              value={dateFrom}
              onChange={(e) => handleDateFromChange(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label htmlFor="date-to" className="block text-xs text-gray-500 mb-1">
              To
            </label>
            <input
              type="date"
              id="date-to"
              name="date-to"
              value={dateTo}
              onChange={(e) => handleDateToChange(e.target.value)}
              className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Status Filter */}
      <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((option) => {
                const isSelected = filters.statusFilters.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => toggleStatus(option.value)}
                    className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-blue-100 text-blue-800 border-2 border-blue-500'
                        : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>
      </div>

      {/* Sentiment Filter */}
      <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sentiment
            </label>
            <div className="flex flex-wrap gap-2">
              {SENTIMENT_OPTIONS.map((option) => {
                const isSelected = filters.sentimentFilters.includes(option.value);
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => toggleSentiment(option.value)}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-purple-100 text-purple-800 border-2 border-purple-500'
                        : 'bg-gray-100 text-gray-700 border-2 border-transparent hover:bg-gray-200'
                    }`}
                  >
                    <span>{option.emoji}</span>
                    <span>{option.label}</span>
                  </button>
                );
              })}
            </div>
      </div>

      {/* Handoff Filter */}
      <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Handoff Status
            </label>
            <div className="flex items-center gap-4">
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="handoff"
                  checked={filters.hasHandoffFilter === true}
                  onChange={() => setHasHandoffFilter(true)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Has handoff</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="handoff"
                  checked={filters.hasHandoffFilter === false}
                  onChange={() => setHasHandoffFilter(false)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">No handoff</span>
              </label>
              <label className="inline-flex items-center">
                <input
                  type="radio"
                  name="handoff"
                  checked={filters.hasHandoffFilter === null}
                  onChange={() => setHasHandoffFilter(null)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                />
                <span className="ml-2 text-sm text-gray-700">Any</span>
              </label>
            </div>
      </div>

      {/* Clear All Button */}
      {hasActiveFilters && (
        <div className="pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={handleClearAll}
            className="w-full px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Clear All Filters
          </button>
        </div>
      )}
    </div>
  );
};
