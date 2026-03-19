/**
 * SearchBar Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Search input field for filtering conversations.
 */

import { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';
import { useConversationStore } from '../../stores/conversationStore';

export interface SearchBarProps {
  placeholder?: string;
  debounceMs?: number;
}

export const SearchBar = ({
  placeholder = 'SCAN BY CUSTOMER ID OR MESSAGE CONTENT...',
  debounceMs = 300,
}: SearchBarProps) => {
  const { filters, setSearchQuery } = useConversationStore();
  const [localValue, setLocalValue] = useState(filters.searchQuery);

  useEffect(() => {
    setLocalValue(filters.searchQuery);
  }, [filters.searchQuery]);

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
  };

  const hasValue = localValue.length > 0;

  return (
    <div className="relative group">
      <div 
        className="flex items-center gap-4 px-5 py-4 transition-all"
        style={{
          backgroundColor: '#080808',
          border: '1px solid #2f2f2f',
        }}
      >
        <Search size={16} style={{ color: '#6a6a6a' }} className="flex-shrink-0" />
        <input
          type="text"
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent outline-none"
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '11px',
            fontWeight: 500,
            color: '#FFFFFF',
            letterSpacing: '0.5px',
          }}
          aria-label="Search conversations"
        />
        {hasValue && (
          <button
            type="button"
            onClick={handleClear}
            className="transition-colors flex-shrink-0"
            style={{ color: '#6a6a6a' }}
            aria-label="Clear search"
          >
            <X size={14} />
          </button>
        )}
      </div>
    </div>
  );
};
