import { describe, test, expect, vi, beforeEach } from 'vitest';
import * as React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ChatWindowSkeleton } from './components/ChatWindowSkeleton';

describe('Widget Lazy Loading', () => {
  describe('LoadingSpinner', () => {
    test('renders spinner element', () => {
      const { container } = render(<LoadingSpinner />);
      const spinner = container.querySelector('div[style*="animation"]');
      expect(spinner).toBeTruthy();
    });

    test('has spinner container with centered layout', () => {
      const { container } = render(<LoadingSpinner />);
      const spinnerContainer = container.querySelector('[style*="justify-content: center"]');
      expect(spinnerContainer).toBeTruthy();
    });
  });

  describe('ChatWindowSkeleton', () => {
    test('renders skeleton structure', () => {
      const { container } = render(<ChatWindowSkeleton />);
      expect(container.firstChild).toBeTruthy();
    });

    test('has placeholder elements for header, body, and input', () => {
      const { container } = render(<ChatWindowSkeleton />);
      const skeletonDivs = container.querySelectorAll('div[style*="background-color"]');
      expect(skeletonDivs.length).toBeGreaterThan(0);
    });

    test('maintains consistent dimensions', () => {
      const { container } = render(<ChatWindowSkeleton />);
      const root = container.firstChild as HTMLElement;
      expect(root.style.height).toBe('100%');
    });
  });

  describe('ChatWindow Lazy Import', () => {
    test('ChatWindow module can be dynamically imported', async () => {
      const chatWindowModule = await import('./components/ChatWindow');
      expect(chatWindowModule.default).toBeDefined();
    });
  });
});
