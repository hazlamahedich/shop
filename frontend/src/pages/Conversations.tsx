/**
 * Conversations Page
 *
 * Displays a paginated list of customer conversations with search and filter capabilities.
 * Industrial Technical Dashboard design with terminal aesthetics.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, SlidersHorizontal, MessageSquare, ChevronDown, Download } from 'lucide-react';
import { useConversationStore } from '../stores/conversationStore';
import ConversationCard from '../components/conversations/ConversationCard';
import Pagination from '../components/ui/Pagination';
import { SearchBar } from '../components/conversations/SearchBar';
import { FilterPanel } from '../components/conversations/FilterPanel';
import { ActiveFilters } from '../components/conversations/ActiveFilters';
import { SavedFilters } from '../components/conversations/SavedFilters';
import { ExportButton, ExportProgress, ExportOptionsModal } from '../components/export';

const Conversations: React.FC = () => {
  const navigate = useNavigate();

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

  useEffect(() => {
    syncWithUrl();
  }, [syncWithUrl]);

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
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0C0C0C' }}>
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 px-10 pt-8 pb-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full" style={{ backgroundColor: '#00FF8810' }}>
            <MessageSquare size={12} style={{ color: '#00FF88' }} />
            <span className="text-[10px] font-bold uppercase tracking-[0.2em]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#00FF88' }}>
              Neural Logs
            </span>
          </div>
          <h1 className="text-5xl font-bold tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif', color: '#FFFFFF', letterSpacing: '-1px' }}>
            Conversations
          </h1>
          <p className="text-sm" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
            Monitor real-time customer interactions and neural response accuracy.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <ExportButton />
          <button
            type="button"
            onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
            className="flex items-center gap-3 px-6 py-3.5 border transition-all duration-300"
            style={{
              fontFamily: 'JetBrains Mono, monospace',
              backgroundColor: isFilterPanelOpen ? '#00FF88' : '#0A0A0A',
              color: isFilterPanelOpen ? '#0C0C0C' : '#FFFFFF',
              borderColor: isFilterPanelOpen ? '#00FF88' : '#2f2f2f',
              borderRadius: 0,
              fontSize: '10px',
              fontWeight: 700,
              letterSpacing: '0.2em',
            }}
          >
            <SlidersHorizontal size={16} />
            {isFilterPanelOpen ? 'CLOSE FILTERS' : 'FILTER ARRAY'}
          </button>
        </div>
      </div>

      <ExportProgress />

      {/* Main Content Card */}
      <div className="flex-1 flex flex-col mx-10 mb-8 border" style={{ backgroundColor: '#0A0A0A', borderColor: '#2f2f2f' }}>
        {/* Search and Sort Section */}
        <div className="p-6 space-y-6" style={{ backgroundColor: '#0A0A0A', borderBottom: '1px solid #2f2f2f' }}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-end">
            <div className="lg:col-span-2 space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.3em]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                Search Registry
              </label>
              <SearchBar placeholder="Scan by customer ID or message content..." />
            </div>
            <div className="space-y-2">
              <label className="text-[10px] font-bold uppercase tracking-[0.3em]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                Sort Index
              </label>
              <div className="relative">
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={handleSortChange}
                  className="w-full py-3.5 px-5 pr-10 appearance-none cursor-pointer transition-all focus:outline-none"
                  style={{
                    fontFamily: 'JetBrains Mono, monospace',
                    backgroundColor: '#080808',
                    border: '1px solid #2f2f2f',
                    color: '#FFFFFF',
                    fontSize: '11px',
                    fontWeight: 500,
                    borderRadius: 0,
                  }}
                  disabled={loadingState === 'loading'}
                >
                  <option value="updated_at-desc" style={{ backgroundColor: '#0C0C0C' }}>Last Updated (Newest)</option>
                  <option value="updated_at-asc" style={{ backgroundColor: '#0C0C0C' }}>Last Updated (Oldest)</option>
                  <option value="created_at-desc" style={{ backgroundColor: '#0C0C0C' }}>Created (Newest)</option>
                  <option value="created_at-asc" style={{ backgroundColor: '#0C0C0C' }}>Created (Oldest)</option>
                  <option value="status-asc" style={{ backgroundColor: '#0C0C0C' }}>Status (A-Z)</option>
                  <option value="status-desc" style={{ backgroundColor: '#0C0C0C' }}>Status (Z-A)</option>
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: '#6a6a6a' }}>
                  <ChevronDown size={14} />
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
            <ActiveFilters />
            <SavedFilters />
          </div>
        </div>

        {/* Filter Panel */}
        {isFilterPanelOpen && (
          <div className="px-6 py-6" style={{ backgroundColor: '#080808', borderBottom: '1px solid #2f2f2f' }}>
            <FilterPanel />
          </div>
        )}

        {/* List Content */}
        <div className="flex-1 overflow-y-auto" style={{ backgroundColor: '#0C0C0C' }}>
          {error && (
            <div className="flex flex-col items-center justify-center h-full p-20 text-center space-y-6">
              <div className="w-16 h-16 flex items-center justify-center" style={{ backgroundColor: '#FF444420', border: '1px solid #FF444440' }}>
                <AlertCircle size={32} style={{ color: '#FF4444' }} />
              </div>
              <div className="space-y-2">
                <p className="text-xl font-bold uppercase" style={{ fontFamily: 'Space Grotesk, sans-serif', color: '#FFFFFF' }}>
                  Access Protocol Failure
                </p>
                <p className="text-xs uppercase tracking-widest font-bold max-w-sm mx-auto" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                  {error}
                </p>
              </div>
              <button
                onClick={handleRetry}
                className="px-6 py-3 border transition-all duration-300"
                style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  backgroundColor: '#00FF8810',
                  borderColor: '#00FF8840',
                  color: '#00FF88',
                  fontSize: '10px',
                  fontWeight: 700,
                  letterSpacing: '0.2em',
                  borderRadius: 0,
                }}
              >
                Retry Neural Handshake
              </button>
            </div>
          )}

          {loadingState === 'loading' && !error && (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div className="w-10 h-10 border-2 animate-spin" style={{ borderColor: '#2f2f2f', borderTopColor: '#00FF88' }} />
              <p className="text-[10px] font-bold uppercase tracking-[0.4em]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                Parsing Logs...
              </p>
            </div>
          )}

          {loadingState === 'success' && conversations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full p-20 text-center space-y-4">
              <div className="w-16 h-16 flex items-center justify-center" style={{ backgroundColor: '#1A1A1A' }}>
                <MessageSquare size={32} style={{ color: '#6a6a6a' }} />
              </div>
              <div className="space-y-2">
                <p className="font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                  Neural logs are empty.
                </p>
                <p className="text-[10px] font-bold uppercase tracking-widest" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>
                  No interactions found matching the current calibration profile.
                </p>
              </div>
            </div>
          )}

          {loadingState === 'success' && conversations.length > 0 && (
            <div>
              {conversations.map((conversation) => (
                <ConversationCard
                  key={conversation.id}
                  conversation={conversation}
                  onClick={() => navigate(`/conversations/${conversation.id}/history`, { state: { from: '/conversations' } })}
                />
              ))}
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {pagination && pagination.totalPages > 1 && (
          <div className="px-6 py-5 flex items-center justify-between" style={{ backgroundColor: '#0A0A0A', borderTop: '1px solid #2f2f2f' }}>
            <div className="flex items-center gap-4">
              <span className="text-[11px]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#8a8a8a' }}>
                SHOWING {((pagination.page - 1) * pagination.perPage) + 1}-{Math.min(pagination.page * pagination.perPage, pagination.total)} OF {pagination.total} RECORDS
              </span>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#6a6a6a' }}>PER PAGE:</span>
                <span className="text-[11px]" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#FFFFFF' }}>{pagination.perPage}</span>
              </div>
            </div>
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
          </div>
        )}
      </div>

      <ExportOptionsModal />
    </div>
  );
};

export default Conversations;
