/**
 * SavedFilters Component
 *
 * Manages saved filter sets - save current filters and apply previously saved filters.
 */

import { useState, useRef, useEffect } from 'react';
import { useConversationStore } from '../../stores/conversationStore';
import type { SavedFilter } from '../../types/conversation';

export interface SavedFiltersProps {
  className?: string;
}

export const SavedFilters = ({ className = '' }: SavedFiltersProps) => {
  const { savedFilters, filters, saveCurrentFilters, deleteSavedFilter, applySavedFilter } =
    useConversationStore();
  const [isOpen, setIsOpen] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [filterName, setFilterName] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleSaveFilter = () => {
    if (filterName.trim()) {
      saveCurrentFilters(filterName.trim());
      setFilterName('');
      setShowSaveDialog(false);
    }
  };

  const hasActiveFilters =
    filters.searchQuery ||
    filters.dateRange.from ||
    filters.dateRange.to ||
    filters.statusFilters.length > 0 ||
    filters.sentimentFilters.length > 0 ||
    filters.hasHandoffFilter !== null;

  const getFilterDescription = (filter: SavedFilter): string => {
    const parts: string[] = [];

    if (filter.filters.searchQuery) {
      parts.push(`Search: "${filter.filters.searchQuery}"`);
    }
    if (filter.filters.dateRange.from || filter.filters.dateRange.to) {
      parts.push('Date range');
    }
    if (filter.filters.statusFilters.length > 0) {
      parts.push(`${filter.filters.statusFilters.length} status(es)`);
    }
    if (filter.filters.sentimentFilters.length > 0) {
      parts.push(`${filter.filters.sentimentFilters.length} sentiment(s)`);
    }
    if (filter.filters.hasHandoffFilter !== null) {
      parts.push('Handoff filter');
    }

    return parts.length > 0 ? parts.join(' • ') : 'No filters';
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-bold rounded-xl border transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 ${
          isOpen
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.3)]'
            : 'text-slate-300 bg-white/5 border-white/10 hover:bg-emerald-500/10 hover:text-emerald-300 hover:border-emerald-500/20'
        }`}
      >
        <svg className={`w-5 h-5 ${isOpen ? 'text-emerald-400' : 'text-slate-500'} group-hover:text-emerald-400 transition-colors`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
        Saved Filters
        {savedFilters.length > 0 && (
          <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-black bg-emerald-500 rounded-full shadow-[0_0_10px_rgba(16,185,129,0.5)]">
            {savedFilters.length}
          </span>
        )}
        <svg className={`w-4 h-4 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-3 w-80 bg-[#0a0a0a]/95 backdrop-blur-xl border border-emerald-500/20 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-50 overflow-hidden mantis-glass-panel">
          {/* Header */}
          <div className="px-5 py-4 border-b border-emerald-500/10">
            <h3 className="text-sm font-bold text-slate-100 uppercase tracking-widest">Saved Filters</h3>
          </div>

          {/* Save Current Filter */}
          <div className="px-5 py-4 border-b border-emerald-500/5 bg-emerald-500/[0.02]">
            {showSaveDialog ? (
              <div className="space-y-3">
                <input
                  type="text"
                  value={filterName}
                  onChange={(e) => setFilterName(e.target.value)}
                  placeholder="Filter name..."
                  className="block w-full px-4 py-2.5 bg-black/40 border border-emerald-500/20 rounded-xl text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all font-medium"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveFilter();
                    if (e.key === 'Escape') setShowSaveDialog(false);
                  }}
                />
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSaveFilter}
                    disabled={!hasActiveFilters || !filterName.trim()}
                    className="flex-1 px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-black bg-emerald-500 rounded-xl hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-600 disabled:cursor-not-allowed transition-all duration-300 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSaveDialog(false);
                      setFilterName('');
                    }}
                    className="px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-slate-400 bg-white/5 rounded-xl hover:bg-white/10 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowSaveDialog(true)}
                disabled={!hasActiveFilters}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-widest text-emerald-400 bg-emerald-500/5 border border-emerald-500/10 rounded-xl hover:bg-emerald-500/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all duration-300"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Save Current View
              </button>
            )}
          </div>

          {/* Saved Filters List */}
          <div className="max-h-64 overflow-y-auto custom-scrollbar">
            {savedFilters.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <div className="w-12 h-12 mx-auto bg-white/5 rounded-full flex items-center justify-center mb-4 border border-white/5">
                  <svg className="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                  </svg>
                </div>
                <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">No saved filters</p>
                <p className="text-[10px] text-slate-600 mt-2 leading-relaxed">
                  Save your common search views for quick access
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-white/5">
                {savedFilters.map((filter) => (
                  <li key={filter.id} className="group/item">
                    <div className="flex items-start gap-3 px-5 py-4 hover:bg-white/[0.03] transition-colors">
                      <button
                        type="button"
                        onClick={() => {
                          applySavedFilter(filter.id);
                          setIsOpen(false);
                        }}
                        className="flex-1 text-left"
                      >
                        <div className="font-bold text-slate-100 text-sm group-hover/item:text-emerald-400 transition-colors uppercase tracking-tight">
                          {filter.name}
                        </div>
                        <div className="text-[10px] font-medium text-slate-500 mt-1 line-clamp-1">
                          {getFilterDescription(filter)}
                        </div>
                        <div className="text-[10px] font-bold text-slate-700 mt-2 tracking-widest">
                          {new Date(filter.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteSavedFilter(filter.id)}
                        className="opacity-0 group-hover/item:opacity-100 p-2 text-slate-600 hover:text-red-400 transition-all rounded-lg hover:bg-red-500/10"
                        aria-label="Delete filter"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
