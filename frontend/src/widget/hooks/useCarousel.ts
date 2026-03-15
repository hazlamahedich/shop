import * as React from 'react';
import { DEFAULT_CAROUSEL_CONFIG, type CarouselConfig } from '../types/widget';

interface CarouselState {
  activeIndex: number;
  canScrollLeft: boolean;
  canScrollRight: boolean;
  totalDots: number;
}

interface UseCarouselReturn extends CarouselState {
  carouselRef: React.RefObject<HTMLDivElement>;
  scrollToIndex: (index: number) => void;
  scrollPrev: () => void;
  scrollNext: () => void;
}

interface UseCarouselOptions {
  itemCount: number;
  config?: Partial<CarouselConfig>;
  isMobile?: boolean;
}

export function useCarousel({ itemCount, config, isMobile = false }: UseCarouselOptions): UseCarouselReturn {
  const carouselRef = React.useRef<HTMLDivElement>(null);
  const mergedConfig = { ...DEFAULT_CAROUSEL_CONFIG, ...config };

  const visibleCards = isMobile
    ? mergedConfig.visibleCards.mobile
    : mergedConfig.visibleCards.desktop;

  const [state, setState] = React.useState<CarouselState>({
    activeIndex: 0,
    canScrollLeft: false,
    canScrollRight: itemCount > visibleCards,
    totalDots: Math.ceil(itemCount / visibleCards),
  });

  const calculateCardWidth = React.useCallback(() => {
    if (!carouselRef.current) return mergedConfig.cardWidth;
    const containerWidth = carouselRef.current.clientWidth;
    const totalGaps = (visibleCards - 1) * mergedConfig.cardGap;
    return (containerWidth - totalGaps) / visibleCards;
  }, [visibleCards, mergedConfig.cardGap, mergedConfig.cardWidth]);

  const scrollToIndex = React.useCallback(
    (index: number) => {
      if (!carouselRef.current) return;

      const cardWidth = calculateCardWidth();
      const scrollPosition = index * (cardWidth + mergedConfig.cardGap);

      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      carouselRef.current.scrollTo({
        left: scrollPosition,
        behavior: prefersReducedMotion ? 'auto' : 'smooth',
      });
    },
    [calculateCardWidth, mergedConfig.cardGap]
  );

  const scrollPrev = React.useCallback(() => {
    const newIndex = Math.max(0, state.activeIndex - 1);
    scrollToIndex(newIndex);
  }, [state.activeIndex, scrollToIndex]);

  const scrollNext = React.useCallback(() => {
    const newIndex = Math.min(itemCount - 1, state.activeIndex + 1);
    scrollToIndex(newIndex);
  }, [itemCount, state.activeIndex, scrollToIndex]);

  const updateScrollState = React.useCallback(() => {
    if (!carouselRef.current) return;

    const { scrollLeft, scrollWidth, clientWidth } = carouselRef.current;
    const cardWidth = calculateCardWidth();
    const cardWithGap = cardWidth + mergedConfig.cardGap;

    const activeIndex = Math.round(scrollLeft / cardWithGap);
    const maxScroll = scrollWidth - clientWidth;

    setState((prev) => ({
      ...prev,
      activeIndex: Math.max(0, Math.min(activeIndex, itemCount - 1)),
      canScrollLeft: scrollLeft > 5,
      canScrollRight: scrollLeft < maxScroll - 5,
      totalDots: Math.ceil(itemCount / visibleCards),
    }));
  }, [calculateCardWidth, mergedConfig.cardGap, itemCount, visibleCards]);

  React.useEffect(() => {
    const carousel = carouselRef.current;
    if (!carousel) return;

    let timeoutId: ReturnType<typeof setTimeout>;

    const handleScroll = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateScrollState, 100);
    };

    carousel.addEventListener('scroll', handleScroll, { passive: true });

    updateScrollState();

    return () => {
      clearTimeout(timeoutId);
      carousel.removeEventListener('scroll', handleScroll);
    };
  }, [updateScrollState]);

  React.useEffect(() => {
    updateScrollState();
  }, [itemCount, visibleCards, updateScrollState]);

  return {
    carouselRef,
    activeIndex: state.activeIndex,
    canScrollLeft: state.canScrollLeft,
    canScrollRight: state.canScrollRight,
    totalDots: state.totalDots,
    scrollToIndex,
    scrollPrev,
    scrollNext,
  };
}
