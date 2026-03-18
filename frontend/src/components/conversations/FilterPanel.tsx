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
  { value: 'active', label: 'Active', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { value: 'handoff', label: 'Handoff', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  { value: 'closed', label: 'Closed', color: 'bg-slate-500/10 text-slate-400 border-slate-500/20' },
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
    <div className="space-y-8 py-2">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Date Range */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
            Date Range
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="date-from" className="block text-[10px] font-bold text-slate-600 mb-2 uppercase tracking-tight">
                From
              </label>
              <input
                type="date"
                id="date-from"
                name="date-from"
                value={dateFrom}
                onChange={(e) => handleDateFromChange(e.target.value)}
                className="block w-full px-4 py-2.5 bg-black/40 border border-emerald-500/10 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all"
              />
            </div>
            <div>
              <label htmlFor="date-to" className="block text-[10px] font-bold text-slate-600 mb-2 uppercase tracking-tight">
                To
              </label>
              <input
                type="date"
                id="date-to"
                name="date-to"
                value={dateTo}
                onChange={(e) => handleDateToChange(e.target.value)}
                className="block w-full px-4 py-2.5 bg-black/40 border border-emerald-500/10 rounded-xl text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all"
              />
            </div>
          </div>
        </div>

        {/* Status Filter */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
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
                  className={`inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wide transition-all duration-300 border ${
                    isSelected
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                      : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10 hover:text-slate-200'
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Sentiment Filter */}
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
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
                  className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-wide transition-all duration-300 border ${
                    isSelected
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                      : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10 hover:text-slate-200'
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
        <div className="space-y-4">
          <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
            Handoff Status
          </label>
          <div className="flex items-center gap-6">
            <label className="inline-flex items-center group cursor-pointer">
              <input
                type="radio"
                name="handoff"
                checked={filters.hasHandoffFilter === true}
                onChange={() => setHasHandoffFilter(true)}
                className="h-4 w-4 bg-black/40 border-emerald-500/30 text-emerald-500 focus:ring-emerald-500/20 focus:ring-offset-0"
              />
              <span className="ml-2 text-xs font-bold text-slate-400 group-hover:text-slate-200 transition-colors uppercase tracking-tight">Has handoff</span>
            </label>
            <label className="inline-flex items-center group cursor-pointer">
              <input
                type="radio"
                name="handoff"
                checked={filters.hasHandoffFilter === false}
                onChange={() => setHasHandoffFilter(false)}
                className="h-4 w-4 bg-black/40 border-emerald-500/30 text-emerald-500 focus:ring-emerald-500/20 focus:ring-offset-0"
              />
              <span className="ml-2 text-xs font-bold text-slate-400 group-hover:text-slate-200 transition-colors uppercase tracking-tight">No handoff</span>
            </label>
            <label className="inline-flex items-center group cursor-pointer">
              <input
                type="radio"
                name="handoff"
                checked={filters.hasHandoffFilter === null}
                onChange={() => setHasHandoffFilter(null)}
                className="h-4 w-4 bg-black/40 border-emerald-500/30 text-emerald-500 focus:ring-emerald-500/20 focus:ring-offset-0"
              />
              <span className="ml-2 text-xs font-bold text-slate-400 group-hover:text-slate-200 transition-colors uppercase tracking-tight">Any</span>
            </label>
          </div>
        </div>
      </div>

      {/* Clear All Button */}
      {hasActiveFilters && (
        <div className="pt-6 border-t border-emerald-500/10 flex justify-end">
          <button
            type="button"
            onClick={handleClearAll}
            className="px-6 py-2.5 text-[10px] font-bold uppercase tracking-widest text-red-400 hover:text-red-300 bg-red-500/5 hover:bg-red-500/10 border border-red-500/20 rounded-xl transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-red-500/20"
          >
            Reset All Filters
          </button>
        </div>
      )}
    </div>
  );
};
