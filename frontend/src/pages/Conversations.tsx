/**
 * Conversations Page
 *
 * Displays a paginated list of customer conversations.
 * This is a business dashboard view for monitoring bot activity.
 *
 * Story 3-1: Conversation List with Pagination
 */

import React, { useEffect } from 'react';
import { Search, AlertCircle } from 'lucide-react';
import { useConversationStore } from '../stores/conversationStore';
import ConversationCard from '../components/conversations/ConversationCard';
import Pagination from '../components/ui/Pagination';

const Conversations: React.FC = () => {
  const {
    conversations,
    pagination,
    loadingState,
    error,
    currentPage,
    perPage,
    fetchConversations,
    nextPage,
    prevPage,
    setPerPage,
    clearError,
  } = useConversationStore();

  // Fetch conversations on mount
  useEffect(() => {
    fetchConversations();
  }, []);

  const handleRetry = () => {
    clearError();
    fetchConversations();
  };

  return (
    <div className="h-full bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Conversations</h2>

        <div className="flex items-center justify-between">
          {/* Search placeholder - will be implemented in Story 3-2 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search conversations..."
              disabled
              className="w-full pl-9 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </div>

          {/* Sorting controls */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Sort by:</span>
            <select
              className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
              disabled={loadingState === 'loading'}
            >
              <option value="updated_at">Last Updated</option>
              <option value="created_at">Created Date</option>
              <option value="status">Status</option>
            </select>
          </div>
        </div>
      </div>

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
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Loading state */}
        {loadingState === 'loading' && !error && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}

        {/* Empty state */}
        {loadingState === 'success' && conversations.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full p-8">
            <p className="text-gray-900 font-medium mb-2">No conversations yet</p>
            <p className="text-gray-500 text-sm">
              Conversations will appear here when customers message your bot
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
