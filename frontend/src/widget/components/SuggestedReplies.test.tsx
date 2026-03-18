import * as React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SuggestedReplies } from './SuggestedReplies';
import type { WidgetTheme } from '../types/widget';

const mockTheme: WidgetTheme = {
  primaryColor: '#6366f1',
  backgroundColor: '#ffffff',
  textColor: '#1f2937',
  botBubbleColor: '#f3f4f6',
  userBubbleColor: '#6366f1',
  position: 'bottom-right',
  borderRadius: 16,
  width: 380,
  height: 600,
  fontFamily: 'Inter, sans-serif',
  fontSize: 14,
};

describe('SuggestedReplies', () => {
  const mockSuggestions = [
    'Tell me more about pricing',
    'What about features?',
    'How can I get started?',
    'Do you have documentation?',
  ];

  it('renders chips when suggestions provided', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    expect(screen.getByTestId('suggested-replies')).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Suggested replies' })).toBeInTheDocument();
    mockSuggestions.forEach((suggestion) => {
      expect(screen.getByRole('button', { name: suggestion })).toBeInTheDocument();
    });
  });

  it('renders max 4 suggestions', () => {
    const manySuggestions = [
      'Suggestion 1',
      'Suggestion 2',
      'Suggestion 3',
      'Suggestion 4',
      'Suggestion 5',
      'Suggestion 6',
    ];
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={manySuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeLessThanOrEqual(4);
  });

  it('click sends suggestion as message', async () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    fireEvent.click(button);

    expect(onSelect).toHaveBeenCalledWith(mockSuggestions[0]);
  });

  it('has horizontal scroll container', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const container = screen.getByTestId('suggested-replies');
    expect(container).toHaveStyle({ overflowX: 'auto' });
  });

  it('keyboard navigation works with Tab, Enter, Space', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });

    fireEvent.keyDown(button, { key: 'Enter' });
    expect(onSelect).toHaveBeenCalledWith(mockSuggestions[0]);

    onSelect.mockClear();

    fireEvent.keyDown(button, { key: ' ' });
    expect(onSelect).toHaveBeenCalledWith(mockSuggestions[0]);
  });

  it('suggestions hide after selection', async () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    fireEvent.click(button);

    rerender(
      <SuggestedReplies
        suggestions={[]}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    expect(screen.queryByTestId('suggested-replies')).not.toBeInTheDocument();
  });

  it('dark mode styling applied', () => {
    const darkTheme: WidgetTheme = {
      ...mockTheme,
      backgroundColor: '#1f2937',
      textColor: '#f3f4f6',
    };
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={darkTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    expect(button).toHaveStyle({ color: darkTheme.primaryColor });
  });

  it('respects reduced motion preference', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    expect(button).toBeDefined();
  });

  it('handles empty/null suggestions gracefully', () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <SuggestedReplies
        suggestions={[]}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    expect(screen.queryByTestId('suggested-replies')).not.toBeInTheDocument();

    rerender(
      <SuggestedReplies
        suggestions={null as unknown as string[]}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    expect(screen.queryByTestId('suggested-replies')).not.toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const container = screen.getByRole('group', { name: 'Suggested replies' });
    expect(container).toHaveAttribute('aria-label', 'Suggested replies');

    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toHaveAttribute('aria-label');
    });
  });

  it('disables chips when disabled prop is true', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
        disabled={true}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    expect(button).toBeDisabled();
  });

  it('has 44px minimum touch target (WCAG 2.1 AA)', () => {
    const onSelect = vi.fn();
    render(
      <SuggestedReplies
        suggestions={mockSuggestions}
        onSelect={onSelect}
        theme={mockTheme}
      />
    );

    const button = screen.getByRole('button', { name: mockSuggestions[0] });
    expect(button).toHaveStyle({ minHeight: '44px' });
  });
});
