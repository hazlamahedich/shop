import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { SuccessCheckmark } from './SuccessCheckmark';

describe('SuccessCheckmark', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it('should not render when not visible', () => {
    render(<SuccessCheckmark isVisible={false} />);
    expect(screen.queryByTestId('success-checkmark')).toBeNull();
  });

  it('should render when visible', () => {
    render(<SuccessCheckmark isVisible={true} />);
    expect(screen.getByTestId('success-checkmark')).toBeDefined();
  });

  it('should have correct default size (24px)', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const checkmark = screen.getByTestId('success-checkmark');
    expect(checkmark.getAttribute('width')).toBe('24');
    expect(checkmark.getAttribute('height')).toBe('24');
  });

  it('should accept custom size', () => {
    render(<SuccessCheckmark isVisible={true} size={32} />);
    const checkmark = screen.getByTestId('success-checkmark');
    expect(checkmark.getAttribute('width')).toBe('32');
    expect(checkmark.getAttribute('height')).toBe('32');
  });

  it('should have success green color (#22c55e)', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.getAttribute('stroke')).toBe('#22c55e');
  });

  it('should trigger onComplete callback after 400ms', () => {
    const onComplete = vi.fn();
    render(<SuccessCheckmark isVisible={true} onComplete={onComplete} />);
    
    expect(onComplete).not.toHaveBeenCalled();
    
    vi.advanceTimersByTime(400);
    
    expect(onComplete).toHaveBeenCalledTimes(1);
  });

  it('should not trigger onComplete when not visible', () => {
    const onComplete = vi.fn();
    render(<SuccessCheckmark isVisible={false} onComplete={onComplete} />);
    
    vi.advanceTimersByTime(400);
    
    expect(onComplete).not.toHaveBeenCalled();
  });

  it('should apply checkmark-draw animation when visible', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.style.animationName).toBe('checkmark-draw');
  });

  it('should set animation duration to 400ms', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.style.animationDuration).toBe('400ms');
  });

  it('should use ease-out timing function', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.style.animationTimingFunction).toBe('ease-out');
  });

  it('should set stroke-dashoffset to 0 when visible', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.getAttribute('stroke-dashoffset')).toBe('0');
  });

  it('should have stroke-dasharray of 24', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const path = screen.getByTestId('success-checkmark').querySelector('path');
    expect(path?.getAttribute('stroke-dasharray')).toBe('24');
  });

  it('should have accessibility attributes', () => {
    render(<SuccessCheckmark isVisible={true} />);
    const checkmark = screen.getByTestId('success-checkmark');
    expect(checkmark.getAttribute('role')).toBe('img');
    expect(checkmark.getAttribute('aria-label')).toBe('Success');
  });
});
