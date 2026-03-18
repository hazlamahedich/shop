import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CarouselArrows } from './CarouselArrows';
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

describe('CarouselArrows', () => {
  it('renders left and right arrows', () => {
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={vi.fn()}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('button', { name: /Scroll left/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Scroll right/i })).toBeInTheDocument();
  });

  it('calls onPrev when left arrow is clicked', () => {
    const onPrev = vi.fn();
    render(
      <CarouselArrows
        onPrev={onPrev}
        onNext={vi.fn()}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Scroll left/i }));
    expect(onPrev).toHaveBeenCalledOnce();
  });

  it('calls onNext when right arrow is clicked', () => {
    const onNext = vi.fn();
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={onNext}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Scroll right/i }));
    expect(onNext).toHaveBeenCalledOnce();
  });

  it('disables left arrow when cannot scroll left', () => {
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={vi.fn()}
        canScrollLeft={false}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('button', { name: /Scroll left/i })).toBeDisabled();
  });

  it('disables right arrow when cannot scroll right', () => {
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={vi.fn()}
        canScrollLeft={true}
        canScrollRight={false}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('button', { name: /Scroll right/i })).toBeDisabled();
  });

  it('does not call onPrev when left arrow is disabled and clicked', () => {
    const onPrev = vi.fn();
    render(
      <CarouselArrows
        onPrev={onPrev}
        onNext={vi.fn()}
        canScrollLeft={false}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Scroll left/i }));
    expect(onPrev).not.toHaveBeenCalled();
  });

  it('does not call onNext when right arrow is disabled and clicked', () => {
    const onNext = vi.fn();
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={onNext}
        canScrollLeft={true}
        canScrollRight={false}
        theme={mockTheme}
      />
    );

    fireEvent.click(screen.getByRole('button', { name: /Scroll right/i }));
    expect(onNext).not.toHaveBeenCalled();
  });

  it('has proper aria-labels', () => {
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={vi.fn()}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    expect(screen.getByRole('button', { name: /Scroll left to previous products/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Scroll right to next products/i })).toBeInTheDocument();
  });

  it('calls onPrev on Enter key press', () => {
    const onPrev = vi.fn();
    render(
      <CarouselArrows
        onPrev={onPrev}
        onNext={vi.fn()}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    fireEvent.keyDown(screen.getByRole('button', { name: /Scroll left/i }), { key: 'Enter' });
    expect(onPrev).toHaveBeenCalledOnce();
  });

  it('calls onNext on Space key press', () => {
    const onNext = vi.fn();
    render(
      <CarouselArrows
        onPrev={vi.fn()}
        onNext={onNext}
        canScrollLeft={true}
        canScrollRight={true}
        theme={mockTheme}
      />
    );

    fireEvent.keyDown(screen.getByRole('button', { name: /Scroll right/i }), { key: ' ' });
    expect(onNext).toHaveBeenCalledOnce();
  });
});
