import * as React from 'react';
import type { WidgetProduct, WidgetTheme, CarouselConfig } from '../types/widget';
import { DEFAULT_CAROUSEL_CONFIG } from '../types/widget';
import { ProductCardCompact } from './ProductCardCompact';
import { CarouselArrows } from './CarouselArrows';
import { CarouselDots } from './CarouselDots';
import { useCarousel } from '../hooks/useCarousel';

export interface ProductCarouselProps {
  products: WidgetProduct[];
  theme: WidgetTheme;
  onAddToCart?: (product: WidgetProduct) => void;
  onProductClick?: (product: WidgetProduct) => void;
  addingProductId?: string | null;
  config?: Partial<CarouselConfig>;
}

export function ProductCarousel({
  products,
  theme,
  onAddToCart,
  onProductClick,
  addingProductId,
  config,
}: ProductCarouselProps) {
  const [isMobile, setIsMobile] = React.useState(false);

  const mergedConfig = { ...DEFAULT_CAROUSEL_CONFIG, ...config };

  React.useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const { carouselRef, activeIndex, canScrollLeft, canScrollRight, totalDots, scrollToIndex, scrollPrev, scrollNext } =
    useCarousel({
      itemCount: products.length,
      config: mergedConfig,
      isMobile,
    });

  const visibleCards = isMobile ? mergedConfig.visibleCards.mobile : mergedConfig.visibleCards.desktop;

  const calculateCardWidth = React.useCallback(() => {
    if (!carouselRef.current) return mergedConfig.cardWidth;
    const containerWidth = carouselRef.current.clientWidth;
    const totalGaps = (visibleCards - 1) * mergedConfig.cardGap;
    return Math.floor((containerWidth - totalGaps) / visibleCards);
  }, [visibleCards, mergedConfig.cardGap, mergedConfig.cardWidth]);

  const [cardWidth, setCardWidth] = React.useState(mergedConfig.cardWidth);

  React.useEffect(() => {
    const updateCardWidth = () => {
      setCardWidth(calculateCardWidth());
    };

    updateCardWidth();
    window.addEventListener('resize', updateCardWidth);
    return () => window.removeEventListener('resize', updateCardWidth);
  }, [calculateCardWidth]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      scrollPrev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      scrollNext();
    } else if (e.key === 'Home') {
      e.preventDefault();
      scrollToIndex(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      scrollToIndex(products.length - 1);
    }
  };

  if (products.length === 0) {
    return null;
  }

  return (
    <div
      className="product-carousel-wrapper"
      data-testid="product-carousel-wrapper"
      role="region"
      aria-label={`Product carousel with ${products.length} products`}
      aria-roledescription="carousel"
      onKeyDown={handleKeyDown}
    >
      <div
        ref={carouselRef}
        className="product-carousel"
        data-testid="product-carousel"
        role="group"
        aria-label={`${products.length} products`}
        tabIndex={0}
      >
        {products.map((product, index) => (
          <div
            key={product.id}
            role="group"
            aria-label={`${index + 1} of ${products.length}: ${product.title}`}
            aria-roledescription="slide"
          >
            <ProductCardCompact
              product={product}
              theme={theme}
              onAddToCart={onAddToCart}
              onClick={onProductClick}
              isAdding={addingProductId === product.id}
              cardWidth={cardWidth}
            />
          </div>
        ))}
      </div>

      <CarouselArrows
        onPrev={scrollPrev}
        onNext={scrollNext}
        canScrollLeft={canScrollLeft}
        canScrollRight={canScrollRight}
        theme={theme}
      />

      <CarouselDots
        totalDots={totalDots}
        activeIndex={Math.floor(activeIndex / visibleCards)}
        onDotClick={(index) => scrollToIndex(index * visibleCards)}
        theme={theme}
      />
    </div>
  );
}
