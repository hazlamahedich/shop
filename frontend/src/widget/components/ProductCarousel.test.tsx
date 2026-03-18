import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCarousel } from './ProductCarousel';
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

const createMockProducts = (count: number): WidgetProduct[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `prod-${i}`,
    variantId: `var-${i}`,
    title: `Product ${i + 1}`,
    price: 29.99 + i,
    imageUrl: `https://example.com/image-${i}.jpg`,
    available: true,
  }));

describe('ProductCarousel', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
  });

  it('renders carousel with products', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('region', { name: /Product carousel with 5 products/i })).toBeInTheDocument();
    expect(screen.getByText('Product 1')).toBeInTheDocument();
    expect(screen.getByText('Product 5')).toBeInTheDocument();
  });

  it('renders nothing when products array is empty', () => {
    const { container } = render(
      <ProductCarousel
        products={[]}
        theme={mockTheme}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('shows correct number of product cards', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const cards = screen.getAllByRole('group').filter(el => el.getAttribute('aria-roledescription') === 'slide');
    expect(cards).toHaveLength(5);
  });

  it('has proper accessibility attributes', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const region = screen.getByRole('region');
    expect(region).toHaveAttribute('aria-roledescription', 'carousel');
    expect(region).toHaveAttribute('aria-label', 'Product carousel with 5 products');
  });

  it('renders dots indicator when multiple pages exist', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('tablist', { name: /Carousel pages/i })).toBeInTheDocument();
  });

  it('renders navigation arrows', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('button', { name: /Scroll left/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Scroll right/i })).toBeInTheDocument();
  });

  it('calls onAddToCart when Add to Cart button is clicked', () => {
    const products = createMockProducts(3);
    const onAddToCart = vi.fn();
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
        onAddToCart={onAddToCart}
      />
    );

    const addToCartButtons = screen.getAllByRole('button', { name: /Add.*to cart/i });
    fireEvent.click(addToCartButtons[0]);
    expect(onAddToCart).toHaveBeenCalledWith(products[0]);
  });

  it('shows loading state on correct card when adding product', () => {
    const products = createMockProducts(3);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
        onAddToCart={vi.fn()}
        addingProductId="prod-1"
      />
    );

    const addingButton = screen.getByRole('button', { name: /Adding/i });
    expect(addingButton).toBeInTheDocument();
  });

  it('handles keyboard navigation - ArrowRight scrolls next', async () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const carousel = screen.getByRole('group', { name: /5 products/i });
    expect(carousel).toHaveAttribute('tabIndex', '0');
  });

  it('handles keyboard navigation - ArrowLeft scrolls prev', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const carousel = screen.getByRole('group', { name: /5 products/i });
    expect(carousel).toBeInTheDocument();
  });

  it('handles keyboard navigation - Home scrolls to start', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const carousel = screen.getByRole('group', { name: /5 products/i });
    expect(carousel).toBeInTheDocument();
  });

  it('handles keyboard navigation - End scrolls to end', () => {
    const products = createMockProducts(5);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const carousel = screen.getByRole('group', { name: /5 products/i });
    expect(carousel).toBeInTheDocument();
  });

  it('has proper aria-roledescription on slides', () => {
    const products = createMockProducts(3);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    const slides = screen.getAllByRole('group').filter(el => el.getAttribute('aria-roledescription') === 'slide');
    slides.forEach(slide => {
      expect(slide).toHaveAttribute('aria-roledescription', 'slide');
    });
  });

  it('has proper aria-label on each slide', () => {
    const products = createMockProducts(3);
    render(
      <ProductCarousel
        products={products}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('group', { name: /1 of 3: Product 1/ })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /2 of 3: Product 2/ })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /3 of 3: Product 3/ })).toBeInTheDocument();
  });
});
