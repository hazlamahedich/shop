import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import { useCarousel } from './useCarousel';

describe('useCarousel', () => {
  it('returns carouselRef', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(result.current.carouselRef).toBeDefined();
    expect(result.current.carouselRef.current).toBeNull();
  });

  it('returns scrollToIndex function', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(result.current.scrollToIndex).toBeInstanceOf(Function);
  });

  it('returns scrollPrev function', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(result.current.scrollPrev).toBeInstanceOf(Function);
  });

  it('returns scrollNext function', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(result.current.scrollNext).toBeInstanceOf(Function);
  });

  it('calculates correct totalDots for desktop (3 visible cards)', () => {
    const { result: result3 } = renderHook(() =>
      useCarousel({
        itemCount: 3,
        isMobile: false,
      })
    );
    expect(result3.current.totalDots).toBe(1);

    const { result: result5 } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );
    expect(result5.current.totalDots).toBe(2);

    const { result: result7 } = renderHook(() =>
      useCarousel({
        itemCount: 7,
        isMobile: false,
      })
    );
    expect(result7.current.totalDots).toBe(3);
  });

  it('calculates correct totalDots for mobile (2 visible cards)', () => {
    const { result: result3 } = renderHook(() =>
      useCarousel({
        itemCount: 3,
        isMobile: true,
      })
    );
    expect(result3.current.totalDots).toBe(2);

    const { result: result5 } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: true,
      })
    );
    expect(result5.current.totalDots).toBe(3);
  });

  it('handles empty item count', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 0,
        isMobile: false,
      })
    );

    expect(result.current.activeIndex).toBe(0);
    expect(result.current.totalDots).toBe(0);
    expect(result.current.canScrollLeft).toBe(false);
    expect(result.current.canScrollRight).toBe(false);
  });

  it('handles single item', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 1,
        isMobile: false,
      })
    );

    expect(result.current.activeIndex).toBe(0);
    expect(result.current.totalDots).toBe(1);
    expect(result.current.canScrollLeft).toBe(false);
    expect(result.current.canScrollRight).toBe(false);
  });

  it('respects custom config', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 6,
        isMobile: false,
        config: {
          visibleCards: { mobile: 1, desktop: 2 },
          cardWidth: 120,
          cardGap: 8,
          scrollDuration: 200,
        },
      })
    );

    expect(result.current.totalDots).toBe(3);
  });

  it('returns initial activeIndex as 0', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(result.current.activeIndex).toBe(0);
  });

  it('returns canScrollLeft and canScrollRight booleans', () => {
    const { result } = renderHook(() =>
      useCarousel({
        itemCount: 5,
        isMobile: false,
      })
    );

    expect(typeof result.current.canScrollLeft).toBe('boolean');
    expect(typeof result.current.canScrollRight).toBe('boolean');
  });
});
