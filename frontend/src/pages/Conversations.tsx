/**
 * Conversations Page
 *
 * Displays a paginated list of customer conversations with search and filter capabilities.
 * Re-imagined with high-fidelity Mantis aesthetic.
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, SlidersHorizontal, MessageSquare, ArrowUpDown } from 'lucide-react';
import { useConversationStore } from '../stores/conversationStore';
import ConversationCard from '../components/conversations/ConversationCard';
import Pagination from '../components/ui/Pagination';
import { SearchBar } from '../components/conversations/SearchBar';
import { FilterPanel } from '../components/conversations/FilterPanel';
import { ActiveFilters } from '../components/conversations/ActiveFilters';
import { SavedFilters } from '../components/conversations/SavedFilters';
import { ExportButton, ExportProgress, ExportOptionsModal } from '../components/export';
import { GlassCard } from '../components/ui/GlassCard';

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

  // Sync filters from URL and fetch conversations on mount
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
    <div className="h-full flex flex-col space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/5 border border-emerald-500/10 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">
            <MessageSquare size={12} />
            Neural Logs
          </div>
          <h1 className="text-5xl font-black tracking-tight text-white leading-none mantis-glow-text">
            Conversations
          </h1>
          <p className="text-lg text-emerald-900/40 font-medium max-w-xl">
            Monitor real-time customer interactions and neural response accuracy.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <ExportButton />
          <button
            type="button"
            onClick={() => setIsFilterPanelOpen(!isFilterPanelOpen)}
            className={`h-14 px-8 font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl border transition-all duration-300 flex items-center gap-3 ${
              isFilterPanelOpen
                ? 'bg-emerald-500 text-black border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.3)]'
                : 'bg-white/5 border-white/10 text-white hover:bg-white/10 hover:border-white/20'
            }`}
          >
            <SlidersHorizontal size={18} />
            {isFilterPanelOpen ? 'Close Filters' : 'Filter Array'}
          </button>
        </div>
      </div>

      <ExportProgress />

      <GlassCard accent="mantis" className="flex-1 flex flex-col border-emerald-500/5 bg-emerald-500/[0.01] overflow-hidden">
        {/* Search and Sort Sub-header */}
        <div className="p-8 border-b border-white/[0.03] space-y-8 bg-white/[0.01]">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-end">
            <div className="lg:col-span-2 space-y-4">
              <label className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em] ml-1">Search Registry</label>
              <SearchBar placeholder="Scan by customer ID or message content..." />
            </div>
            <div className="space-y-4">
              <label className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em] ml-1">Sort Index</label>
              <div className="relative group">
                <select
                  value={`${sortBy}-${sortOrder}`}
                  onChange={handleSortChange}
                  className="w-full h-14 bg-white/5 border border-white/10 rounded-2xl px-6 pr-12 text-white font-black text-xs uppercase tracking-widest appearance-none transition-all focus:border-emerald-500/40 focus:bg-emerald-500/[0.03] cursor-pointer"
                  disabled={loadingState === 'loading'}
                >
                  <option value="updated_at-desc" className="bg-[#030303]">Last Updated (Newest)</option>
                  <option value="updated_at-asc" className="bg-[#030303]">Last Updated (Oldest)</option>
                  <option value="created_at-desc" className="bg-[#030303]">Created (Newest)</option>
                  <option value="created_at-asc" className="bg-[#030303]">Created (Oldest)</option>
                  <option value="status-asc" className="bg-[#030303]">Status (A-Z)</option>
                  <option value="status-desc" className="bg-[#030303]">Status (Z-A)</option>
                </select>
                <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-emerald-900/40">
                  <ArrowUpDown size={16} />
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-4 pt-4">
            <ActiveFilters />
            <SavedFilters />
          </div>
        </div>

        {/* Filter Panel Transition */}
        {isFilterPanelOpen && (
          <div className="px-8 py-8 border-b border-emerald-500/10 bg-emerald-500/[0.03] animate-in slide-in-from-top-4 duration-500">
            <FilterPanel />
          </div>
        )}

        {/* List Content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar bg-white/[0.005]">
          {error && (
            <div className="flex flex-col items-center justify-center h-full p-20 text-center space-y-8">
              <div className="w-20 h-20 bg-red-500/10 border border-red-500/20 rounded-full flex items-center justify-center text-red-500">
                <AlertCircle size={40} />
              </div>
              <div className="space-y-4">
                <p className="text-xl font-black text-white uppercase tracking-tight">Access Protocol Failure</p>
                <p className="text-xs text-emerald-900/40 max-w-sm mx-auto uppercase tracking-widest font-black leading-relaxed">
                  {error}
                </p>
              </div>
              <button
                onClick={handleRetry}
                className="h-14 px-8 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-black text-[10px] uppercase tracking-[0.3em] rounded-2xl hover:bg-emerald-500 hover:text-black transition-all duration-300"
              >
                Retry Neural Handshake
              </button>
            </div>
          )}

          {loadingState === 'loading' && !error && (
            <div className="flex flex-col items-center justify-center h-full gap-4">
              <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
              <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.4em]">Parsing Logs...</p>
            </div>
          )}

          {loadingState === 'success' && conversations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full p-20 text-center space-y-6">
              <div className="w-20 h-20 bg-white/[0.02] border border-white/[0.05] rounded-full flex items-center justify-center mx-auto text-emerald-900/10">
                <MessageSquare size={40} />
              </div>
              <div className="space-y-2">
                <p className="text-white/60 font-bold">Neural logs are empty.</p>
                <p className="text-xs text-emerald-900/30 max-w-sm mx-auto uppercase tracking-widest font-black leading-relaxed">
                  No interactions found matching the current calibration profile.
                </p>
              </div>
            </div>
          )}

          {loadingState === 'success' && conversations.length > 0 && (
            <div className="divide-y divide-white/[0.03]">
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
          <div className="p-8 border-t border-white/[0.03] bg-white/[0.01]">
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
      </GlassCard>

      <ExportOptionsModal />
    </div>
  );
};

export default Conversations;
