import * as React from 'react';
import type { WidgetTheme } from '../types/widget';

export interface CarouselDotsProps {
  totalDots: number;
  activeIndex: number;
  onDotClick: (index: number) => void;
  theme: WidgetTheme;
}

export function CarouselDots({ totalDots, activeIndex, onDotClick, theme: _theme }: CarouselDotsProps) {
  if (totalDots <= 1) {
    return null;
  }

  const handleDotClick = (index: number) => (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDotClick(index);
  };

  const handleDotKeyDown = (index: number) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onDotClick(index);
    }
  };

  return (
    <div className="carousel-dots" data-testid="carousel-dots" role="tablist" aria-label="Carousel pages">
      {Array.from({ length: totalDots }, (_, index) => (
        <button
          key={index}
          type="button"
          className={`carousel-dot ${index === activeIndex ? 'active' : ''}`}
          data-testid={`carousel-dot-${index}`}
          data-active={index === activeIndex}
          onClick={handleDotClick(index)}
          onKeyDown={handleDotKeyDown(index)}
          role="tab"
          aria-selected={index === activeIndex}
          aria-label={`Page ${index + 1} of ${totalDots}`}
          tabIndex={index === activeIndex ? 0 : -1}
        />
      ))}
    </div>
  );
}
