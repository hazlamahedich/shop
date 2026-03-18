/**
 * SearchBar Component
 *
 * Search input field for filtering conversations by customer ID or message content.
 */

import { useState, useEffect } from 'react';
import { useConversationStore } from '../../stores/conversationStore';

export interface SearchBarProps {
  placeholder?: string;
  debounceMs?: number;
}

export const SearchBar = ({
  placeholder = 'Search by customer ID or message content...',
  debounceMs = 300,
}: SearchBarProps) => {
  const { filters, setSearchQuery } = useConversationStore();
  const [localValue, setLocalValue] = useState(filters.searchQuery);

  // Sync local value with store
  useEffect(() => {
    setLocalValue(filters.searchQuery);
  }, [filters.searchQuery]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localValue !== filters.searchQuery) {
        setSearchQuery(localValue);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [localValue, debounceMs, filters.searchQuery, setSearchQuery]);

  const handleClear = () => {
    setLocalValue('');
    // setSearchQuery('') will be called by the debounced effect
  };

  const hasValue = localValue.length > 0;

  return (
    <div className="relative group">
      <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
        <svg
          className="w-5 h-5 text-slate-500 group-focus-within:text-emerald-400 transition-colors duration-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <input
        type="text"
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        placeholder={placeholder}
        className="block w-full pl-10 pr-10 py-2.5 bg-black/40 border border-emerald-500/10 rounded-xl text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500/40 transition-all duration-300 sm:text-sm"
        aria-label="Search conversations"
      />

      {hasValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-emerald-400 focus:outline-none transition-colors duration-300"
          aria-label="Clear search"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
};
