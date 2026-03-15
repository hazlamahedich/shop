import * as React from 'react';
import type { WidgetTheme } from '../types/widget';

export interface CarouselArrowsProps {
  onPrev: () => void;
  onNext: () => void;
  canScrollLeft: boolean;
  canScrollRight: boolean;
  theme: WidgetTheme;
}

export function CarouselArrows({ onPrev, onNext, canScrollLeft, canScrollRight, theme: _theme }: CarouselArrowsProps) {
  const handlePrevClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (canScrollLeft) {
      onPrev();
    }
  };

  const handleNextClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (canScrollRight) {
      onNext();
    }
  };

  const handlePrevKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (canScrollLeft) {
        onPrev();
      }
    }
  };

  const handleNextKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (canScrollRight) {
        onNext();
      }
    }
  };

  return (
    <div className="carousel-arrows" data-testid="carousel-arrows">
      <button
        type="button"
        className="carousel-arrow carousel-arrow-left"
        data-testid="carousel-arrow-left"
        onClick={handlePrevClick}
        onKeyDown={handlePrevKeyDown}
        disabled={!canScrollLeft}
        aria-label="Scroll left to previous products"
        title="Previous"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="15 18 9 12 15 6" />
        </svg>
      </button>
      <button
        type="button"
        className="carousel-arrow carousel-arrow-right"
        data-testid="carousel-arrow-right"
        onClick={handleNextClick}
        onKeyDown={handleNextKeyDown}
        disabled={!canScrollRight}
        aria-label="Scroll right to next products"
        title="Next"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="9 18 15 12 9 6" />
        </svg>
      </button>
    </div>
  );
}
