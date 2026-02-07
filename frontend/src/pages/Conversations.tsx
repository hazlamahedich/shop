/**
 * Conversations Page
 *
 * Displays a paginated list of customer conversations with search and filter capabilities.
 * This is a business dashboard view for monitoring bot activity.
 *
 * Story 3-1: Conversation List with Pagination
 * Story 3-2: Search and Filter Conversations
 */

import React, { useEffect, useState } from 'react';
import { AlertCircle, SlidersHorizontal } from 'lucide-react';
import { useConversationStore } from '../stores/conversationStore';
import ConversationCard from '../components/conversations/ConversationCard';
import Pagination from '../components/ui/Pagination';
import { SearchBar } from '../components/conversations/SearchBar';
import { FilterPanel } from '../components/conversations/FilterPanel';
import { ActiveFilters } from '../components/conversations/ActiveFilters';
import { SavedFilters } from '../components/conversations/SavedFilters';

const Conversations: React.FC = () => {
  const {
    conversations,
    pagination,
    loadingState,
    error,
    currentPage,
    sortBy,
    sortOrder,
    fetchConversations,
    nextPage,
    prevPage,
    setPerPage,
    setSorting,
    syncWithUrl,
    clearError,
  } = useConversationStore();

  const [isFilterPanelOpen, setIsFilterPanelOpen] = useState(false);

  // Sync filters from URL and fetch conversations on mount
  useEffect(() => {
    syncWithUrl();
  }, []);

  const handleRetry = () => {
    clearError();
    fetchConversations();
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const [newSortBy, newSortOrder] = e.target.value.split('-') as [
      'updated_at' | 'status' | 'created_at',
      'asc' | 'desc'
    ];
    setSorting(newSortBy, newSortOrder);
  };

  return (
    <div className="h-full bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Conversations</h2>

          <div className="flex items-center gap-3">
            {/* Saved Filters */}
            <SavedFilters />

            {/* Filter Toggle Button */}
            <button
              type="button"
              onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
              className={`inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                isFilterPanelOpen
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'text-gray-700 bg-white border-gray-300 hover:bg-gray-50'
              }`}
            >
              <SlidersHorizontal size={16} />
              Filters
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-md">
          <SearchBar placeholder="Search by customer ID or message content..." />
        </div>

        {/* Active Filters */}
        <ActiveFilters />

        {/* Sorting Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Sort by:</span>
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={handleSortChange}
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loadingState === 'loading'}
            >
              <option value="updated_at-desc">Last Updated (Newest)</option>
              <option value="updated_at-asc">Last Updated (Oldest)</option>
              <option value="created_at-desc">Created (Newest)</option>
              <option value="created_at-asc">Created (Oldest)</option>
              <option value="status-asc">Status (A-Z)</option>
              <option value="status-desc">Status (Z-A)</option>
            </select>
          </div>

          {/* Results Count */}
          {pagination && (
            <span className="text-sm text-gray-500">
              {pagination.total} result{pagination.total !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      {isFilterPanelOpen && (
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <FilterPanel />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Error state */}
        {error && (
          <div className="flex flex-col items-center justify-center h-full p-8">
            <AlertCircle className="text-red-500 mb-4" size={48} />
            <p className="text-gray-900 font-medium mb-2">Failed to load conversations</p>
            <p className="text-gray-500 text-sm mb-4">{error}</p>
            <button
              onClick={handleRetry}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loadingState === 'loading' && !error && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        )}

        {/* Empty state */}
        {loadingState === 'success' && conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full p-8">
            <p className="text-gray-900 font-medium mb-2">No conversations yet</p>
            <p className="text-gray-500 text-sm">
              Try adjusting your filters or search terms
            </p>
          </div>
        )}

        {/* Conversation list */}
        {loadingState === 'success' && conversations.length > 0 && (
          <div>
            {conversations.map((conversation) => (
              <ConversationCard
                key={conversation.id}
                conversation={conversation}
                // TODO: Add click handler in Story 4-8 (conversation-history-view)
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination && pagination.totalPages > 1 && (
        <Pagination
          currentPage={pagination.page}
          totalPages={pagination.totalPages}
          total={pagination.total}
          perPage={pagination.perPage}
          onPageChange={(page) => {
            if (page > currentPage) {
              nextPage();
            } else if (page < currentPage) {
              prevPage();
            }
          }}
          onPerPageChange={setPerPage}
          isLoading={loadingState === 'loading'}
        />
      )}
    </div>
  );
};

export default Conversations;
