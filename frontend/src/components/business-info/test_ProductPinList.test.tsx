/**
 * Tests for ProductPinList Component
 *
 * Story 1.15: Product Highlight Pins
 *
 * Tests component functionality including:
 * - Empty state rendering
 * - Product card display
 * - Pin/unpin operations
 * - Search functionality
 * - Pagination
 * - Loading states
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProductPinList } from './ProductPinList';
import type { ProductPinItem } from '../../stores/botConfigStore';
import { useBotConfigStore } from '../../stores/botConfigStore';

// Mock products data
const mockProducts: ProductPinItem[] = [
  {
    product_id: 'shopify_prod_1',
    title: 'Running Shoes',
    image_url: 'https://example.com/shoes.jpg',
    is_pinned: false,
    pinned_order: undefined,
    pinned_at: undefined,
  },
  {
    product_id: 'shopify_prod_2',
    title: 'Yoga Mat',
    image_url: 'https://example.com/yoga.jpg',
    is_pinned: true,
    pinned_order: 1,
    pinned_at: '2024-01-15T10:30:00Z',
  },
  {
    product_id: 'shopify_prod_3',
    title: 'Water Bottle',
    image_url: 'https://example.com/bottle.jpg',
    is_pinned: true,
    pinned_order: 2,
    pinned_at: '2024-01-15T10:31:00Z',
  },
];

// Mock pin limit info
const mockPinLimitInfo = {
  pin_limit: 10,
  pinned_count: 2,
};

// Mock pagination
const mockPagination = {
  page: 1,
  limit: 20,
  total: 50,
  has_more: true,
};

// Mock the bot config store
const mockFetchProductPins = vi.fn();
const mockPinProduct = vi.fn();
const mockUnpinProduct = vi.fn();
const mockSetSearchQuery = vi.fn();
const mockTogglePinnedOnly = vi.fn();
const mockClearProductsError = vi.fn();

const mockStore = {
  productPins: [],
  productsLoading: false,
  productsError: null,
  searchQuery: '',
  pinnedOnly: false,
  pagination: undefined,
  pinLimitInfo: null,
  fetchProductPins: mockFetchProductPins,
  pinProduct: mockPinProduct,
  unpinProduct: mockUnpinProduct,
  setSearchQuery: mockSetSearchQuery,
  togglePinnedOnly: mockTogglePinnedOnly,
  clearProductsError: mockClearProductsError,
};

describe('ProductPinList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock useBotConfigStore to return our mock store
    vi.mocked(useBotConfigStore).mockReturnValue(mockStore);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Component Rendering', () => {
    it('should render the component', () => {
      render(<ProductPinList />);
      expect(screen.getByTestId('product-pin-list')).toBeInTheDocument();
    });

    it('should render the header with title', () => {
      render(<ProductPinList />);
      expect(screen.getByText('Product Highlight Pins')).toBeInTheDocument();
    });

    it('should render the description text', () => {
      render(<ProductPinList />);
      expect(screen.getByText(/Prioritize important products to boost their recommendations/)).toBeInTheDocument();
    });

    it('should render the help section', () => {
      render(<ProductPinList />);
      expect(screen.getByText('About Product Highlight Pins')).toBeInTheDocument();
      expect(screen.getByText('Pin Important Products')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', async () => {
      mockStore.productsLoading = true;
      mockStore.productPins = [];

      render(<ProductPinList />);

      expect(screen.getByTestId('loading-state')).toBeInTheDocument();
      expect(screen.getByText('Loading products...')).toBeInTheDocument();
    });

    it('should disable controls when loading', async () => {
      mockStore.productsLoading = true;

      render(<ProductPinList />);

      const searchInput = screen.getByLabelText('Search products');
      expect(searchInput).toBeDisabled();
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no products', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;

      render(<ProductPinList />);

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText(/No products found/)).toBeInTheDocument();
    });

    it('should show search empty state when search has no results', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.searchQuery = 'nonexistent';

      render(<ProductPinList />);

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText(/No products found matching "nonexistent"/)).toBeInTheDocument();
    });

    it('should show pinned only empty message', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.pinnedOnly = true;

      render(<ProductPinList />);

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText(/No pinned products yet/)).toBeInTheDocument();
    });
  });

  describe('Product Display', () => {
    it('should render product cards', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      expect(screen.getByText('Running Shoes')).toBeInTheDocument();
      expect(screen.getByText('Yoga Mat')).toBeInTheDocument();
      expect(screen.getByText('Water Bottle')).toBeInTheDocument();
    });

    it('should render product images', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const images = screen.getAllByRole('img');
      expect(images.length).toBeGreaterThan(0);
    });

    it('should show pin status badge for pinned products', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      expect(screen.getAllByText('Pinned #1').length).toBe(1);
      expect(screen.getAllByText('Pinned #2').length).toBe(1);
    });

    it('should display product ID', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      expect(screen.getByText('ID: shopify_prod_1')).toBeInTheDocument();
      expect(screen.getByText('ID: shopify_prod_2')).toBeInTheDocument();
    });
  });

  describe('Pin Toggle', () => {
    it('should render pin buttons for each product', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const pinButtons = screen.getAllByRole('button');
      const pinButtonsForProducts = pinButtons.filter(btn =>
        btn.getAttribute('aria-label')?.includes('Pin') || btn.getAttribute('aria-label')?.includes('Unpin')
      );
      expect(pinButtonsForProducts.length).toBe(3);
    });

    it('should show correct pin button state for pinned products', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const pinnedButton = screen.getByLabelText('Unpin Yoga Mat');
      expect(pinnedButton).toHaveClass('bg-blue-600');
    });

    it('should show correct pin button state for unpinned products', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.searchQuery = '';
      mockStore.pinnedOnly = false;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const unpinnedButton = screen.getByLabelText('Pin Running Shoes');
      expect(unpinnedButton).toHaveClass('bg-gray-200');
    });
  });

  describe('Pin Limit Display', () => {
    it('should display pin limit info', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      expect(screen.getByText('2/10 products pinned')).toBeInTheDocument();
    });

    it('should show warning when limit reached', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = { ...mockPinLimitInfo, pinned_count: 10 };

      render(<ProductPinList />);

      expect(screen.getByText('(Pin limit reached)')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should render search input', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.searchQuery = '';

      render(<ProductPinList />);

      const searchInput = screen.getByLabelText('Search products');
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute('placeholder', 'Search products...');
    });

    it('should render clear button when search has value', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.searchQuery = 'test query';

      render(<ProductPinList />);

      const clearButton = screen.getByLabelText('Clear search');
      expect(clearButton).toBeInTheDocument();
    });
  });

  describe('Pinned Only Toggle', () => {
    it('should render pinned only toggle button', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.pinnedOnly = false;

      render(<ProductPinList />);

      expect(screen.getByRole('button', { name: /Showing All Products|Showing Pinned Only/ })).toBeInTheDocument();
    });

    it('should toggle between All Products and Pinned Only', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = [];
      mockStore.pinnedOnly = false;

      render(<ProductPinList />);

      const button = screen.getByRole('button', { name: /Showing All Products|Showing Pinned Only/ });
      expect(button).toHaveTextContent('Showing Pinned');

      await userEvent.click(button);

      expect(mockTogglePinnedOnly).toHaveBeenCalledWith(true);
      expect(mockFetchProductPins).toHaveBeenCalledWith({ pinnedOnly: true });
    });
  });

  describe('Pagination', () => {
    it('should render pagination when there are more products', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = { ...mockPagination, total: 100 };

      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      expect(screen.getByText('Page 1 of 5')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Previous' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Next' })).toBeInTheDocument();
    });

    it('should disable previous button on first page', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = { ...mockPagination, page: 1 };
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const prevButton = screen.getByRole('button', { name: 'Previous' });
      expect(prevButton).toBeDisabled();
    });

    it('should disable next button on last page', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = { ...mockPagination, page: 5 };
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const nextButton = screen.getByRole('button', { name: 'Next' });
      expect(nextButton).toBeDisabled();
    });
  });

  describe('Store Interactions', () => {
    it('should call fetchProductPins on mount', async () => {
      render(<ProductPinList />);

      // The component calls fetchProductPins on mount via useEffect
      await waitFor(() => {
        expect(mockFetchProductPins).toHaveBeenCalled();
      });
    });

    it('should handle pin product interaction', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const pinButton = screen.getByLabelText('Pin Running Shoes');
      await userEvent.click(pinButton);

      expect(mockPinProduct).toHaveBeenCalledWith('shopify_prod_1');
    });

    it('should handle unpin product interaction', async () => {
      mockStore.productsLoading = false;
      mockStore.productPins = mockProducts;
      mockStore.pagination = mockPagination;
      mockStore.pinLimitInfo = mockPinLimitInfo;

      render(<ProductPinList />);

      const unpinButton = screen.getByLabelText('Unpin Yoga Mat');
      await userEvent.click(unpinButton);

      expect(mockUnpinProduct).toHaveBeenCalledWith('shopify_prod_2');
    });
  });
});
