import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCardCompact } from './ProductCardCompact';
import type { WidgetProduct, WidgetTheme } from '../types/widget';

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1e293b',
  botBubbleColor: '#f1f5f9',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 12,
  width: 400,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

const mockProduct: WidgetProduct = {
  id: 'prod-1',
  variantId: 'var-1',
  title: 'Test Product',
  price: 29.99,
  imageUrl: 'https://example.com/image.jpg',
  available: true,
};

describe('ProductCardCompact', () => {
  it('renders product image, title, and price', () => {
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'Test Product' })).toBeInTheDocument();
  });

  it('truncates long titles with ellipsis', () => {
    const longTitleProduct: WidgetProduct = {
      ...mockProduct,
      title: 'This is a very long product title that should be truncated with ellipsis after two lines of text',
    };

    render(
      <ProductCardCompact
        product={longTitleProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    const title = screen.getByText(/This is a very long product title/);
    expect(title).toHaveClass('carousel-card-title');
  });

  it('shows loading skeleton initially', () => {
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    const skeleton = document.querySelector('.carousel-card-skeleton');
    expect(skeleton).toBeInTheDocument();
  });

  it('shows "Add to Cart" button when onAddToCart is provided', () => {
    const onAddToCart = vi.fn();
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        onAddToCart={onAddToCart}
        cardWidth={140}
      />
    );

    expect(screen.getByRole('button', { name: /Add.*to cart/i })).toBeInTheDocument();
  });

  it('does not show "Add to Cart" button when onAddToCart is not provided', () => {
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    expect(screen.queryByRole('button', { name: /Add.*to cart/i })).not.toBeInTheDocument();
  });

  it('button shows loading state when adding', () => {
    const onAddToCart = vi.fn();
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        onAddToCart={onAddToCart}
        isAdding={true}
        cardWidth={140}
      />
    );

    expect(screen.getByRole('button', { name: /Adding/i })).toBeInTheDocument();
  });

  it('calls onAddToCart when button is clicked', () => {
    const onAddToCart = vi.fn();
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        onAddToCart={onAddToCart}
        cardWidth={140}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Add.*to cart/i }));
    expect(onAddToCart).toHaveBeenCalledWith(mockProduct);
  });

  it('calls onClick when card is clicked', () => {
    const onClick = vi.fn();
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        onClick={onClick}
        cardWidth={140}
      />
    );

    fireEvent.click(screen.getByRole('group'));
    expect(onClick).toHaveBeenCalledWith(mockProduct);
  });

  it('shows "Sold Out" when product is not available', () => {
    const unavailableProduct: WidgetProduct = {
      ...mockProduct,
      available: false,
    };

    render(
      <ProductCardCompact
        product={unavailableProduct}
        theme={mockTheme}
        onAddToCart={vi.fn()}
        cardWidth={140}
      />
    );

    expect(screen.getByRole('button', { name: /Sold Out/i })).toBeInTheDocument();
  });

  it('has hover animation CSS class', () => {
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    const card = screen.getByRole('group');
    expect(card).toHaveClass('carousel-card');
  });

  it('shows featured badge for pinned products', () => {
    const pinnedProduct: WidgetProduct = {
      ...mockProduct,
      isPinned: true,
    };

    render(
      <ProductCardCompact
        product={pinnedProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    expect(screen.getByLabelText('Featured product')).toBeInTheDocument();
  });

  it('shows fallback icon when image fails to load', async () => {
    render(
      <ProductCardCompact
        product={mockProduct}
        theme={mockTheme}
        cardWidth={140}
      />
    );

    const img = screen.getByRole('img', { name: 'Test Product' });
    fireEvent.error(img);

    expect(screen.getByText('📦')).toBeInTheDocument();
  });
});
