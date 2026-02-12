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
import { useToast } from '../../context/ToastContext';

type ProductPinItem = {
  productId: string;
  title: string;
  imageUrl?: string;
  isPinned: boolean;
  pinnedOrder?: number;
  pinnedAt?: string;
};

type PaginationMeta = {
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

type PinLimitInfo = {
  pinLimit: number;
  pinnedCount: number;
};

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
    <div className="relative flex-1">
      <Search
        className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
        size={20}
      />
      <input
        ref={inputRef}
        type="text"
        placeholder="Search products..."
        value={value}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        disabled={disabled}
        className="w-full pl-10 pr-10 py-2.5 px-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        aria-label="Search products"
      />
      {value && (
        <button
          type="button"
          onClick={handleClear}
          disabled={disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 rounded disabled:opacity-50"
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
  }, []);

  // Handle search - stable callback that doesn't change on re-renders
  const handleSearch = useCallback((query: string) => {
    setCurrentSearchQuery(query);
    fetchProductPinsRef.current({ search: query });
  }, []); // Empty deps - callback never changes

  // Toggle product pin
  const handleTogglePin = async (productId: string, currentlyPinned: boolean) => {
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
    <div className="max-w-6xl mx-auto px-6 py-8" data-testid="product-pin-list">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Product Highlight Pins</h2>
        <p className="text-gray-600 mb-2">
          Prioritize important products to boost their recommendations.
          Pinned products appear first with 2x relevance.
        </p>
        {pinLimitInfo && (
          <div className="inline-flex items-center gap-2 mt-3">
            <span className="text-sm text-gray-600">
              {pinLimitInfo.pinnedCount}/{pinLimitInfo.pinLimit} products pinned
            </span>
            {pinLimitInfo.pinnedCount >= pinLimitInfo.pinLimit && (
              <span className="text-sm font-medium text-amber-600">
                (Pin limit reached)
              </span>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {productsError && (
        <div
          role="alert"
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
        >
          <X size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700 mt-1">{productsError}</p>
          </div>
          <button
            type="button"
            onClick={clearProductsError}
            className="text-red-600 hover:text-red-800"
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* Controls Bar */}
      <div className="flex items-center justify-between gap-4 mb-6">
        {/* Search Input */}
        <ProductSearchInput
          onSearch={handleSearch}
          disabled={productsLoading}
        />

        {/* Show Pinned Only Toggle */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleTogglePinnedOnly}
            disabled={productsLoading}
            className={`px-4 py-2 rounded-md border transition-colors duration-200 ${
              pinnedOnly
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
            aria-pressed={pinnedOnly}
          >
            <span className="text-sm font-medium">
              {pinnedOnly ? 'All Products' : 'Pinned Only'}
            </span>
          </button>
        </div>
      </div>

      {/* Product List */}
      <div className="mt-6">
        {productsLoading ? (
          <div className="flex justify-center items-center py-12" data-testid="loading-state">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
            <p className="ml-4 text-gray-600">Loading products...</p>
          </div>
        ) : productPins.length === 0 ? (
          <div className="text-center py-12" data-testid="empty-state">
            <div className="text-gray-500 mb-4" aria-live="polite">
              {currentSearchQuery
                ? `No products found matching "${currentSearchQuery}"`
                : pinnedOnly
                  ? 'No pinned products yet. Pin important products to boost their recommendations.'
                  : 'No products found. Connect your Shopify store to add products.'}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {productPins.map((product) => (
              <div
                key={product.productId}
                className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-all duration-200 relative"
                data-testid={`product-card-${product.productId}`}
              >
                {/* Pin Toggle Button */}
                <button
                  type="button"
                  onClick={() => handleTogglePin(product.productId, product.isPinned)}
                  disabled={productsLoading}
                  className={`absolute top-3 right-3 p-2 rounded-full transition-colors duration-200 ${
                    product.isPinned
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                  aria-label={`${product.isPinned ? 'Unpin' : 'Pin'} ${product.title || product.productId}`}
                  aria-pressed={product.isPinned}
                >
                  <Pin size={20} />
                </button>

                {/* Product Image */}
                {product.imageUrl && (
                  <img
                    src={product.imageUrl}
                    alt={product.title || product.productId}
                    className="w-full h-48 object-cover rounded-t-lg"
                    loading="lazy"
                  />
                )}

                {/* Product Info */}
                <div className="mt-3">
                  {/* Title */}
                  <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 min-h-[3.5rem]">
                    {product.title || product.productId}
                  </h3>

                  {/* Pin Status Badge */}
                  {product.isPinned && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-600 text-white text-xs font-medium rounded-full mt-2">
                      <Pin size={12} />
                      Pinned
                      {product.pinnedOrder && ` #${product.pinnedOrder}`}
                    </span>
                  )}

                  {/* Product ID (for reference) */}
                  <p className="text-xs text-gray-500 mt-2">
                    ID: {product.productId}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.total > pagination.limit && (
          <div className="flex justify-center items-center gap-4 mt-8">
            <button
              type="button"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1 || productsLoading}
              className="px-4 py-2 rounded-md border border-gray-300 hover:bg-gray-100 disabled:text-gray-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              aria-label="Previous page"
            >
              <ChevronLeft size={16} />
              Previous
            </button>

            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>

            <button
              type="button"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages || productsLoading}
              className="px-4 py-2 rounded-md border border-gray-300 hover:bg-gray-100 disabled:text-gray-400 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              aria-label="Next page"
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Help Section */}
      <div className="mt-8 p-6 bg-blue-50 border border-blue-200 rounded-xl">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">About Product Highlight Pins</h3>
        <div className="grid md:grid-cols-2 gap-6 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">Pin Important Products</h4>
            <p className="text-blue-700">
              Pin up to 10 products that you want to feature prominently in bot recommendations.
              Pinned products get a 2x relevance boost.
            </p>
          </div>
          <div>
            <h4 className="font-medium mb-2">Prioritize Order</h4>
            <p className="text-blue-700">
              Products pinned earlier in the list appear first when the bot recommends items.
              Use the pin number to control priority.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProductPinList;
