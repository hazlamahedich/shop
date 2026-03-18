/**
 * Tests for QuickTryButtons Component
 *
 * Story 1.13: Bot Preview Mode
 *
 * Tests the starter prompt buttons component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QuickTryButtons } from '../QuickTryButtons';

describe('QuickTryButtons', () => {
  const starterPrompts = [
    'What products do you have under $50?',
    'What are your business hours?',
    'Show me running shoes',
    'I need help with my order',
    'Tell me about your return policy',
  ];

  it('should render all starter prompts as buttons', () => {
    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={vi.fn()}
      />
    );

    starterPrompts.forEach((prompt) => {
      expect(screen.getByText(prompt)).toBeInTheDocument();
    });
  });

  it('should call onPromptClick when a button is clicked', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();

    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={handleClick}
      />
    );

    await user.click(screen.getByText(starterPrompts[0]));

    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith(starterPrompts[0]);
  });

  it('should render nothing when no prompts provided', () => {
    render(
      <QuickTryButtons starterPrompts={[]} onPromptClick={vi.fn()} />
    );

    expect(screen.queryByText(/Quick try:/)).not.toBeInTheDocument();
  });

  it('should disable buttons when disabled prop is true', () => {
    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={vi.fn()}
        disabled={true}
      />
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(starterPrompts.length);
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('should enable buttons when disabled prop is false', () => {
    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={vi.fn()}
        disabled={false}
      />
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(starterPrompts.length);
    buttons.forEach((button) => {
      expect(button).not.toBeDisabled();
    });
  });

  it('should have accessible labels for buttons', () => {
    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={vi.fn()}
      />
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    buttons.forEach((button, index) => {
      expect(button).toHaveAttribute('aria-label', `Try prompt: ${starterPrompts[index]}`);
    });
  });

  it('should display "Quick try:" label', () => {
    render(
      <QuickTryButtons
        starterPrompts={starterPrompts}
        onPromptClick={vi.fn()}
      />
    );

    expect(screen.getByText(/Quick try:/)).toBeInTheDocument();
  });
});
