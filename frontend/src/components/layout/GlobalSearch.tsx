import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, X, MessageSquare, HelpCircle, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { searchService, type GlobalSearchResults } from '../../services/searchService';

export const GlobalSearch: React.FC = () => {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<GlobalSearchResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const debouncedSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length < 2) {
        setResults(null);
        setIsLoading(false);
        return;
      }

      try {
        const searchResults = await searchService.search(searchQuery);
        setResults(searchResults);
        setSelectedIndex(-1);
      } catch (error) {
        console.error('Search failed:', error);
        setResults(null);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    []
  );

  useEffect(() => {
    if (query.length >= 2) {
      setIsLoading(true);
      setIsOpen(true);
      debouncedSearch(query);
    } else {
      setResults(null);
      setIsOpen(false);
    }
  }, [query, debouncedSearch]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!results || !isOpen) return;

    const totalItems = results.conversations.length + results.faqs.length;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % totalItems);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + totalItems) % totalItems);
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(selectedIndex);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleSelect = (index: number) => {
    if (!results) return;

    const conversationCount = results.conversations.length;
    
    if (index < conversationCount) {
      const conversation = results.conversations[index];
      navigate(`/conversations/${conversation.id}/history`);
    } else {
      const faqIndex = index - conversationCount;
      const faq = results.faqs[faqIndex];
      navigate(`/business-info-faq#faq-${faq.id}`);
    }
    
    setIsOpen(false);
    setQuery('');
    setResults(null);
    inputRef.current?.blur();
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setIsOpen(false);
    inputRef.current?.focus();
  };

  const totalItems = results ? results.conversations.length + results.faqs.length : 0;

  return (
    <div className="flex items-center w-full max-w-md relative">
      <div className="relative w-full">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.length >= 2 && setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search conversations, FAQs..."
          className="w-full pl-10 pr-10 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
          aria-label="Search"
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          role="combobox"
        />
        {isLoading && (
          <Loader2
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 animate-spin"
            size={18}
          />
        )}
        {!isLoading && query && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            aria-label="Clear search"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {isOpen && results && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-2 bg-white rounded-lg shadow-lg border border-gray-200 z-50 max-h-96 overflow-y-auto"
          role="listbox"
        >
          {totalItems === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <p className="text-sm">No results found for "{query}"</p>
            </div>
          ) : (
            <>
              {results.conversations.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase bg-gray-50">
                    Conversations
                  </div>
                  {results.conversations.map((conversation, index) => (
                    <button
                      key={conversation.id}
                      type="button"
                      onMouseDown={(e) => e.preventDefault()}
                      onClick={() => handleSelect(index)}
                      className={`w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-gray-50 ${
                        selectedIndex === index ? 'bg-blue-50' : ''
                      }`}
                      role="option"
                      aria-selected={selectedIndex === index}
                    >
                      <MessageSquare size={18} className="text-gray-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {conversation.platformSenderIdMasked}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {conversation.lastMessage || 'No message'}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400 capitalize">{conversation.status}</span>
                    </button>
                  ))}
                </div>
              )}

              {results.faqs.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase bg-gray-50">
                    FAQs
                  </div>
                  {results.faqs.map((faq, faqIndex) => {
                    const globalIndex = results.conversations.length + faqIndex;
                    return (
                      <button
                        key={faq.id}
                        onClick={() => handleSelect(globalIndex)}
                        className={`w-full px-4 py-3 flex items-start gap-3 text-left hover:bg-gray-50 ${
                          selectedIndex === globalIndex ? 'bg-blue-50' : ''
                        }`}
                        role="option"
                        aria-selected={selectedIndex === globalIndex}
                      >
                        <HelpCircle size={18} className="text-gray-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 truncate">{faq.question}</p>
                          <p className="text-xs text-gray-500 truncate">{faq.answer}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {totalItems > 0 && (
                <div className="px-4 py-2 text-xs text-gray-500 border-t border-gray-100">
                  {totalItems} result{totalItems !== 1 ? 's' : ''} found
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: ReturnType<typeof setTimeout> | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export default GlobalSearch;
