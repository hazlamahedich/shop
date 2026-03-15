import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CarouselDots } from './CarouselDots';
import type { WidgetTheme } from '../types/widget';

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

describe('CarouselDots', () => {
  it('renders correct number of dots', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    expect(dots).toHaveLength(5);
  });

  it('renders nothing when only one dot', () => {
    const { container } = render(
      <CarouselDots
        totalDots={1}
        activeIndex={0}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders nothing when zero dots', () => {
    const { container } = render(
      <CarouselDots
        totalDots={0}
        activeIndex={0}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('highlights active dot', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={2}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    expect(dots[2]).toHaveClass('active');
    expect(dots[0]).not.toHaveClass('active');
    expect(dots[1]).not.toHaveClass('active');
    expect(dots[3]).not.toHaveClass('active');
    expect(dots[4]).not.toHaveClass('active');
  });

  it('calls onDotClick with correct index when clicked', () => {
    const onDotClick = vi.fn();
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={onDotClick}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    fireEvent.click(dots[3]);
    expect(onDotClick).toHaveBeenCalledWith(3);
  });

  it('has proper role="tablist"', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('tablist', { name: /Carousel pages/i })).toBeInTheDocument();
  });

  it('has proper aria-selected on active dot', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={2}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    expect(dots[2]).toHaveAttribute('aria-selected', 'true');
    expect(dots[0]).toHaveAttribute('aria-selected', 'false');
  });

  it('has proper aria-label for each dot', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('tab', { name: 'Page 1 of 5' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Page 2 of 5' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Page 5 of 5' })).toBeInTheDocument();
  });

  it('active dot has tabIndex 0', () => {
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={2}
        onDotClick={vi.fn()}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    expect(dots[2]).toHaveAttribute('tabIndex', '0');
    expect(dots[0]).toHaveAttribute('tabIndex', '-1');
  });

  it('calls onDotClick on Enter key press', () => {
    const onDotClick = vi.fn();
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={onDotClick}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    fireEvent.keyDown(dots[3], { key: 'Enter' });
    expect(onDotClick).toHaveBeenCalledWith(3);
  });

  it('calls onDotClick on Space key press', () => {
    const onDotClick = vi.fn();
    render(
      <CarouselDots
        totalDots={5}
        activeIndex={0}
        onDotClick={onDotClick}
        theme={mockTheme}
      />
    );

    const dots = screen.getAllByRole('tab');
    fireEvent.keyDown(dots[2], { key: ' ' });
    expect(onDotClick).toHaveBeenCalledWith(2);
  });
});
