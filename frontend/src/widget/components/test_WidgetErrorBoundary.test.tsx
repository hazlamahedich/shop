import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { WidgetErrorBoundary } from './WidgetErrorBoundary';

function ThrowError({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error');
  }
  return <div>Content</div>;
}

describe('WidgetErrorBoundary', () => {
  const originalConsoleError = console.error;

  beforeEach(() => {
    console.error = vi.fn();
  });

  afterEach(() => {
    console.error = originalConsoleError;
    cleanup();
  });

  it('should render children when no error', () => {
    render(
      <WidgetErrorBoundary>
        <div>Test content</div>
      </WidgetErrorBoundary>
    );
    expect(screen.getByText('Test content')).toBeDefined();
  });

  it('should render fallback when error occurs', () => {
    render(
      <WidgetErrorBoundary>
        <ThrowError shouldThrow={true} />
      </WidgetErrorBoundary>
    );
    expect(screen.getByText(/chat unavailable/i)).toBeDefined();
  });

  it('should render custom fallback when provided', () => {
    render(
      <WidgetErrorBoundary fallback={<div>Custom error</div>}>
        <ThrowError shouldThrow={true} />
      </WidgetErrorBoundary>
    );
    expect(screen.getByText('Custom error')).toBeDefined();
  });

  it('should log error to console', () => {
    render(
      <WidgetErrorBoundary>
        <ThrowError shouldThrow={true} />
      </WidgetErrorBoundary>
    );
    expect(console.error).toHaveBeenCalled();
  });
});
