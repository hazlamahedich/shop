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
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
        </svg>
        Saved Filters
        {savedFilters.length > 0 && (
          <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-blue-600 rounded-full">
            {savedFilters.length}
          </span>
        )}
        <svg className={`w-4 h-4 transition-transform ${isOpen ? 'transform rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200">
            <h3 className="font-medium text-gray-900">Saved Filters</h3>
          </div>

          {/* Save Current Filter */}
          <div className="px-4 py-3 border-b border-gray-200">
            {showSaveDialog ? (
              <div className="space-y-2">
                <input
                  type="text"
                  value={filterName}
                  onChange={(e) => setFilterName(e.target.value)}
                  placeholder="Filter name..."
                  className="block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
                    className="flex-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowSaveDialog(false);
                      setFilterName('');
                    }}
                    className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
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
                className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Save Current Filters
              </button>
            )}
          </div>

          {/* Saved Filters List */}
          <div className="max-h-64 overflow-y-auto">
            {savedFilters.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <svg className="w-12 h-12 mx-auto text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
                <p className="mt-2 text-sm text-gray-500">No saved filters yet</p>
                <p className="text-xs text-gray-400 mt-1">
                  Set up filters and save them for quick access
                </p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {savedFilters.map((filter) => (
                  <li key={filter.id} className="group">
                    <div className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50">
                      <button
                        type="button"
                        onClick={() => {
                          applySavedFilter(filter.id);
                          setIsOpen(false);
                        }}
                        className="flex-1 text-left"
                      >
                        <div className="font-medium text-gray-900 text-sm">{filter.name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          {getFilterDescription(filter)}
                        </div>
                        <div className="text-xs text-gray-400 mt-1">
                          {new Date(filter.createdAt).toLocaleDateString()}
                        </div>
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteSavedFilter(filter.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-600 transition-opacity focus:opacity-100"
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
