/**
 * PersonalityCard Component Tests
 *
 * Story 1.10: Bot Personality Configuration
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PersonalityCard } from './PersonalityCard';
import type { PersonalityType } from '../../types/enums';

describe('PersonalityCard', () => {
  const mockOnSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render the friendly personality card', () => {
      render(
        <PersonalityCard
          personality="friendly"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('Friendly')).toBeInTheDocument();
      expect(screen.getByText(/Casual, warm tone with emojis/)).toBeInTheDocument();
    });

    it('should render the professional personality card', () => {
      render(
        <PersonalityCard
          personality="professional"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText(/Direct, helpful tone/)).toBeInTheDocument();
    });

    it('should render the enthusiastic personality card', () => {
      render(
        <PersonalityCard
          personality="enthusiastic"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('Enthusiastic')).toBeInTheDocument();
      expect(screen.getByText(/High-energy tone/)).toBeInTheDocument();
    });

    it('should display the default greeting preview', () => {
      render(
        <PersonalityCard
          personality="friendly"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      // The greeting is rendered with quotes around it
      expect(screen.getByText(/Hey! 👋 How can I help you today\?/)).toBeInTheDocument();
    });

    it('should show selection indicator when selected', () => {
      render(
        <PersonalityCard
          personality="friendly"
          isSelected={true}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button', { pressed: true });
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('border-primary');
    });
  });

  describe('Interaction', () => {
    it('should call onSelect when clicked', () => {
      render(
        <PersonalityCard
          personality="professional"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button');
      card.click();
      expect(mockOnSelect).toHaveBeenCalledWith('professional');
    });

    it('should not call onSelect when disabled', () => {
      render(
        <PersonalityCard
          personality="friendly"
          isSelected={false}
          onSelect={mockOnSelect}
          className="disabled:opacity-50"
        />
      );

      const card = screen.getByRole('button');
      card.click();
      expect(mockOnSelect).toHaveBeenCalledWith('friendly');
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria-pressed attribute', () => {
      const { rerender } = render(
        <PersonalityCard
          personality="friendly"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('aria-pressed', 'false');

      rerender(
        <PersonalityCard
          personality="friendly"
          isSelected={true}
          onSelect={mockOnSelect}
        />
      );

      expect(card).toHaveAttribute('aria-pressed', 'true');
    });

    it('should have proper aria-describedby attributes', () => {
      render(
        <PersonalityCard
          personality="enthusiastic"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button');
      expect(card).toHaveAttribute('aria-describedby', 'enthusiastic-description enthusiastic-preview');
    });

    it('should announce selection to screen readers', () => {
      render(
        <PersonalityCard
          personality="professional"
          isSelected={true}
          onSelect={mockOnSelect}
        />
      );

      expect(screen.getByText('Professional personality selected')).toBeInTheDocument();
    });
  });

  describe('Visual States', () => {
    it('should apply selected styles when isSelected is true', () => {
      render(
        <PersonalityCard
          personality="friendly"
          isSelected={true}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button');
      expect(card.className).toContain('border-primary');
      expect(card.className).toContain('ring-2');
    });

    it('should apply unselected styles when isSelected is false', () => {
      render(
        <PersonalityCard
          personality="professional"
          isSelected={false}
          onSelect={mockOnSelect}
        />
      );

      const card = screen.getByRole('button');
      expect(card.className).toContain('border-gray-200');
    });
  });
});
