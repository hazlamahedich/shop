/**
 * ProductPinList Component
 *
 * Story 1.15: Product Highlight Pins
 *
 * Displays merchant's products with pin status controls.
 * Merchants can pin important products to boost their recommendations.
 *
 * AC 1: Pin Products List Management
 * AC 2: Pin and Unpin Products
 * AC 3: Product Search and Filter
 * AC 5: Pin Limits and Validation
 * AC 8: Accessibility and Responsive Design
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { Search, Pin, X, ChevronLeft, ChevronRight } from 'lucide-react';

import { useBotConfigStore } from '../../stores/botConfigStore';
import { useOnboardingPhaseStore } from '../../stores/onboardingPhaseStore';
import { useToast } from '../../context/ToastContext';



// Simple search input that maintains its own state and preserves focus
function ProductSearchInput({
  onSearch,
  disabled,
}: {
  onSearch: (query: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Restore focus after re-render if it was focused before
  useEffect(() => {
    if (isFocused && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isFocused]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);

    // Debounce the search callback
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      onSearch(newValue);
    }, 300);
  };

  const handleFocus = () => {
    setIsFocused(true);
  };

  const handleBlur = () => {
    setIsFocused(false);
  };

  const handleClear = () => {
    setValue('');
    onSearch('');
  };

  return (
    <div className="relative flex-1 group">
      <Search
        className="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-[var(--mantis-glow)] transition-colors"
        size={18}
      />
      <input
        ref={inputRef}
        type="text"
        placeholder="Search neural assets..."
        value={value}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        disabled={disabled}
        className="w-full pl-11 pr-11 py-3 bg-black/20 border border-white/10 rounded-xl focus:ring-2 focus:ring-[var(--mantis-glow)]/50 focus:border-[var(--mantis-glow)]/50 focus:bg-black/40 transition-all duration-300 disabled:opacity-20 disabled:cursor-not-allowed text-white placeholder:text-white/20"
        aria-label="Search products"
      />
      {value && (
        <button
          type="button"
          onClick={handleClear}
          disabled={disabled}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-1 text-white/30 hover:text-white transition-colors p-1"
          aria-label="Clear search"
        >
          <X size={16} />
        </button>
      )}
    </div>
  );
}

export function ProductPinList() {
  const { toast } = useToast();

  // Store state
  const productPins = useBotConfigStore((state) => state.productPins);
  const productsLoading = useBotConfigStore((state) => state.productsLoading);
  const productsError = useBotConfigStore((state) => state.productsError);
  const pinnedOnly = useBotConfigStore((state) => state.pinnedOnly);
  const pagination = useBotConfigStore((state) => state.pagination);
  const pinLimitInfo = useBotConfigStore((state) => state.pinLimitInfo);

  // Store actions
  const fetchProductPins = useBotConfigStore((state) => state.fetchProductPins);
  const pinProduct = useBotConfigStore((state) => state.pinProduct);
  const unpinProduct = useBotConfigStore((state) => state.unpinProduct);
  const togglePinnedOnly = useBotConfigStore((state) => state.togglePinnedOnly);
  const clearProductsError = useBotConfigStore((state) => state.clearProductsError);
  const markBotConfigComplete = useOnboardingPhaseStore((state) => state.markBotConfigComplete);

  // Track local search query for display purposes (not used for input control)
  const [currentSearchQuery, setCurrentSearchQuery] = useState('');

  // Keep fetchProductPins in a ref for stable callback
  const fetchProductPinsRef = useRef(fetchProductPins);
  useEffect(() => {
    fetchProductPinsRef.current = fetchProductPins;
  }, [fetchProductPins]);

  // Load products on mount
  useEffect(() => {
    fetchProductPins();
  }, [fetchProductPins]);

  // Handle search - stable callback that doesn't change on re-renders
  const handleSearch = useCallback((query: string) => {
    setCurrentSearchQuery(query);
    fetchProductPinsRef.current({ search: query });
  }, []); // Empty deps - callback never changes

  // Toggle product pin
  const handleTogglePin = async (productId: string, currentlyPinned: boolean, status?: string) => {
    // Prevent pinning draft products
    if (status === 'draft') {
      toast('Draft products cannot be pinned. Publish the product in Shopify first.', 'warning');
      return;
    }

    if (currentlyPinned) {
      try {
        await unpinProduct(productId);
        toast('Product unpinned successfully!', 'success');
      } catch (err) {
        console.error('Failed to unpin product:', err);
        const message = err instanceof Error ? err.message : 'Failed to unpin product. Please try again.';
        toast(message, 'error');
      }
    } else {
      try {
        await pinProduct(productId);
        markBotConfigComplete('pins');
        toast('Product pinned successfully!', 'success');
      } catch (err) {
        console.error('Failed to pin product:', err);
        const message = err instanceof Error ? err.message : 'Failed to pin product. Please try again.';
        toast(message, 'error');
      }
    }
  };

  // Toggle "Show Pinned Only"
  const handleTogglePinnedOnly = () => {
    const newValue = !pinnedOnly;
    togglePinnedOnly();
    fetchProductPins({ pinnedOnly: newValue });
  };

  // Pagination
  const currentPage = pagination?.page || 1;
  const totalPages = pagination ? Math.ceil(pagination.total / pagination.limit) : 1;

  const handlePageChange = (newPage: number) => {
    fetchProductPins({ page: newPage });
  };

  return (
    <div className="max-w-7xl mx-auto py-8" data-testid="product-pin-list">
      {/* Header */}
      <div className="mb-10">
        <h2 className="text-3xl font-bold text-white mb-4 flex items-center gap-3">
          <span className="w-1.5 h-8 bg-[var(--mantis-glow)] rounded-full"></span>
          Priority Anchors
        </h2>
        <p className="text-lg text-white/50 max-w-2xl leading-relaxed">
          Anchor high-value assets to top-level recommendation queues for a 
          <span className="text-[var(--mantis-glow)] font-bold decoration-[var(--mantis-glow)]/30 underline underline-offset-4 mx-1">200% relevance boost</span>.
        </p>
        {pinLimitInfo && (
          <div className="inline-flex items-center gap-3 mt-6 px-4 py-2 bg-white/5 border border-white/10 rounded-xl backdrop-blur-sm">
            <div className="flex gap-1.5">
              {[...Array(pinLimitInfo.pinLimit)].map((_, i) => (
                <div 
                  key={i} 
                  className={`w-2.5 h-2.5 rounded-sm transition-all duration-500 ${
                    i < pinLimitInfo.pinnedCount 
                      ? 'bg-[var(--mantis-glow)] shadow-[0_0_8px_rgba(34,197,94,0.5)]' 
                      : 'bg-white/10'
                  }`}
                />
              ))}
            </div>
            <span className="text-xs font-bold text-white/40 uppercase tracking-widest">
              {pinLimitInfo.pinnedCount} / {pinLimitInfo.pinLimit} Neural Slots Occupied
            </span>
          </div>
        )}
      </div>

      {/* Error Display */}
      {productsError && (
        <div
          role="alert"
          className="mb-8 p-5 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-start gap-4 animate-shake backdrop-blur-md"
        >
          <X size={24} className="text-red-400 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-base font-bold text-red-200 uppercase tracking-tight">Sync Error</p>
            <p className="text-sm text-white/70 mt-1">{productsError}</p>
          </div>
          <button
            type="button"
            onClick={clearProductsError}
            className="text-white/20 hover:text-white transition-colors p-1"
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-10">
        {/* Search Input */}
        <ProductSearchInput
          onSearch={handleSearch}
          disabled={productsLoading}
        />

        {/* Show Pinned Only Toggle */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            type="button"
            onClick={handleTogglePinnedOnly}
            disabled={productsLoading}
            className={`w-full sm:w-auto px-6 py-3 rounded-xl border transition-all duration-300 font-bold text-sm tracking-tight ${
              pinnedOnly
                ? 'bg-[var(--mantis-glow)] text-white border-transparent shadow-[0_0_15px_rgba(34,197,94,0.3)]'
                : 'bg-white/5 text-white/60 border-white/10 hover:bg-white/10 hover:text-white'
            } disabled:opacity-20 disabled:cursor-not-allowed`}
            aria-pressed={pinnedOnly}
          >
            {pinnedOnly ? 'Show All Assets' : 'Filter: Anchored Only'}
          </button>
        </div>
      </div>

      {/* Product List */}
      <div className="mt-6">
        {productsLoading ? (
          <div className="flex flex-col justify-center items-center py-20 bg-white/5 border border-dashed border-white/10 rounded-3xl" data-testid="loading-state">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[var(--mantis-glow)] mb-4" />
            <p className="text-white/40 font-bold uppercase tracking-widest text-xs">Synchronizing Neural Assets...</p>
          </div>
        ) : productPins.length === 0 ? (
          <div className="text-center py-20 bg-white/5 border border-dashed border-white/10 rounded-3xl" data-testid="empty-state">
            <div className="text-white/30 text-lg font-medium" aria-live="polite">
              {currentSearchQuery
                ? `No assets found matching "${currentSearchQuery}"`
                : pinnedOnly
                  ? 'No neural anchors established. Establish priority anchors to boost relevance.'
                  : 'Core repository empty. Synchronize with Shopify to populate assets.'}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {productPins.map((product) => {
              // Debug: Log draft products
              if (product.title?.toLowerCase().includes('draft')) {
                console.log('Draft product data:', { productId: product.productId, title: product.title, status: product.status });
              }
              return (
              <div
                key={product.productId}
                className="group relative bg-[#1A1A1A]/40 backdrop-blur-md border border-white/10 rounded-2xl overflow-hidden hover:border-[var(--mantis-glow)]/40 hover:shadow-[0_0_30px_rgba(34,197,94,0.1)] transition-all duration-500"
                data-testid={`product-card-${product.productId}`}
              >
                {/* Product Image */}
                <div className="relative h-48 w-full overflow-hidden bg-black/40">
                  {product.imageUrl ? (
                    <img
                      src={product.imageUrl}
                      alt={product.title || product.productId}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                      loading="lazy"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-white/10">
                      <Search size={48} />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60" />
                  
                  {/* Pin Toggle Button - Overlay version */}
                  <button
                    type="button"
                    onClick={() => handleTogglePin(product.productId, product.isPinned, product.status)}
                    disabled={productsLoading || product.status === 'draft'}
                    className={`absolute top-4 right-4 p-3 rounded-xl backdrop-blur-md transition-all duration-300 shadow-2xl ${
                      product.status === 'draft'
                        ? 'bg-black/40 text-white/10 cursor-not-allowed'
                        : product.isPinned
                          ? 'bg-[var(--mantis-glow)] text-white scale-110 shadow-[0_0_15px_rgba(34,197,94,0.5)]'
                          : 'bg-black/60 text-white/40 hover:bg-white/10 hover:text-white hover:scale-105 border border-white/5'
                    } disabled:opacity-20`}
                    aria-label={
                      product.status === 'draft'
                        ? 'Cannot anchor draft assets'
                        : `${product.isPinned ? 'Remove Anchor' : 'Establish Anchor'} ${product.title || product.productId}`
                    }
                    aria-pressed={product.isPinned}
                    title={product.status === 'draft' ? 'Draft assets cannot be anchored. Publish in Shopify first.' : undefined}
                  >
                    <Pin size={18} fill={product.isPinned ? 'currentColor' : 'none'} />
                  </button>
                </div>

                {/* Product Info */}
                <div className="p-5">
                  {/* Status Badges */}
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    {product.status === 'draft' && (
                      <span className="px-2 py-0.5 bg-amber-500/10 text-amber-400 text-[10px] font-bold uppercase tracking-wider rounded-md border border-amber-500/20">
                        Inert
                      </span>
                    )}
                    {product.isPinned && (
                      <span className="px-2 py-0.5 bg-[var(--mantis-glow)]/10 text-[var(--mantis-glow)] text-[10px] font-bold uppercase tracking-wider rounded-md border border-[var(--mantis-glow)]/20 flex items-center gap-1">
                        <Pin size={10} fill="currentColor" />
                        Priority Alpha
                      </span>
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="text-sm font-bold text-white line-clamp-2 min-h-[2.5rem] group-hover:text-[var(--mantis-glow)] transition-colors">
                    {product.title || product.productId}
                  </h3>

                  {/* Meta */}
                  <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between text-[10px] font-bold text-white/20 uppercase tracking-widest">
                    <span>Asset ID</span>
                    <span className="font-mono text-[var(--mantis-glow)]/40">{product.productId.slice(0, 8)}...</span>
                  </div>
                </div>
              </div>
            );
            })}
          </div>
        )}

        {/* Pagination */}        {pagination && pagination.total > pagination.limit && (
          <div className="flex justify-center items-center gap-6 mt-12 px-6 py-4 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm w-fit mx-auto">
            <button
              type="button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || productsLoading}
              className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 disabled:opacity-20 disabled:cursor-not-allowed flex items-center gap-2 transition-all group"
              aria-label="Previous page"
            >
              <ChevronLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
              <span className="text-xs font-bold uppercase tracking-widest">Prev</span>
            </button>

            <span className="text-xs font-mono font-bold text-white/40 uppercase tracking-widest">
              Matrix Page {currentPage} <span className="text-white/10">/</span> {totalPages}
            </span>

            <button
              type="button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || productsLoading}
              className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 disabled:opacity-20 disabled:cursor-not-allowed flex items-center gap-2 transition-all group"
              aria-label="Next page"
            >
              <span className="text-xs font-bold uppercase tracking-widest">Next</span>
              <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="mt-12 p-8 bg-white/5 border border-white/10 rounded-3xl relative overflow-hidden group">
        <div className="absolute top-0 left-0 p-20 bg-[var(--mantis-glow)]/5 blur-3xl rounded-full -translate-x-1/2 -translate-y-1/2" />
        
        <h3 className="relative text-xl font-bold text-white mb-6 flex items-center gap-3">
          <Pin size={22} className="text-[var(--mantis-glow)]" />
          Neural Link Protocol
        </h3>
        
        <div className="relative grid md:grid-cols-3 gap-8 text-sm text-white/60">
          <div className="p-5 bg-black/20 rounded-2xl border border-white/5">
            <h4 className="font-bold text-white/80 mb-3 uppercase tracking-widest text-xs">Priority Weights</h4>
            <p className="leading-relaxed">
              Anchor up to 10 assets for primary injection into the recommendation engine. 
              Anchored assets receive a critical priority bias during inference.
            </p>
          </div>
          <div className="p-5 bg-black/20 rounded-2xl border border-white/5">
            <h4 className="font-bold text-white/80 mb-3 uppercase tracking-widest text-xs">Sequence Control</h4>
            <p className="leading-relaxed">
              Link sequence determines propagation order. Assets with lower link indices 
              are prioritized during the initial retrieval phase.
            </p>
          </div>
          <div className="p-5 bg-black/20 rounded-2xl border border-white/5">
            <h4 className="font-bold text-white/80 mb-3 uppercase tracking-widest text-xs">Asset Status</h4>
            <p className="leading-relaxed">
              <span className="text-amber-400 font-bold uppercase tracking-tighter mr-1">Inert</span>
              and
              <span className="text-white/40 font-bold uppercase tracking-tighter mx-1">Archived</span>
              assets are visible in the configuration matrix but excluded from active inference cycles.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductPinList;
