import * as React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProactiveModal } from './ProactiveModal';
import type { ProactiveTrigger } from '../types/widget';

vi.mock('focus-trap-react', () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

describe('ProactiveModal', () => {
  const defaultTrigger: ProactiveTrigger = {
    type: 'exit_intent',
    enabled: true,
    message: 'Wait! Before you go, can we help you find something?',
    actions: [
      { text: 'Get Help', prePopulatedMessage: 'I need help finding a product.' },
      { text: 'No thanks' },
    ],
    cooldown: 30,
  };

  let mockOnDismiss: () => void;

  beforeEach(() => {
    mockOnDismiss = vi.fn();
  });

  it('should not render when not open', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={false}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.queryByTestId('proactive-modal')).not.toBeInTheDocument();
  });

  it('should render when open', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByTestId('proactive-modal')).toBeInTheDocument();
  });

  it('should display the message', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByTestId('proactive-message')).toHaveTextContent(
      'Wait! Before you go, can we help you find something?'
    );
  });

  it('should render action buttons', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByTestId('proactive-action-button-0')).toBeInTheDocument();
    expect(screen.getByTestId('proactive-action-button-1')).toBeInTheDocument();
  });

  it('should call onAction when action button is clicked', () => {
    const onAction = vi.fn();

    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={onAction}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.click(screen.getByTestId('proactive-action-button-0'));

    expect(onAction).toHaveBeenCalledWith(defaultTrigger.actions[0]);
  });

  it('should call onDismiss when dismiss button is clicked', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.click(screen.getByTestId('proactive-dismiss-button'));

    expect(mockOnDismiss).toHaveBeenCalled();
  });

  it('should have correct aria attributes', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    const modal = screen.getByTestId('proactive-modal');
    expect(modal).toHaveAttribute('role', 'dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(modal).toHaveAttribute('aria-labelledby', 'proactive-title');
    expect(modal).toHaveAttribute('aria-describedby', 'proactive-message');
  });

  it('should close on escape key', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    fireEvent.keyDown(document, { key: 'Escape' });

    expect(mockOnDismiss).toHaveBeenCalled();
  });

  it('should render title', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
      />
    );

    expect(screen.getByTestId('proactive-title')).toBeInTheDocument();
  });

  it('should apply theme colors', () => {
    render(
      <ProactiveModal
        trigger={defaultTrigger}
        isOpen={true}
        onAction={vi.fn()}
        onDismiss={mockOnDismiss}
        theme={{
          primaryColor: '#ff0000',
          backgroundColor: '#00ff00',
          textColor: '#0000ff',
        }}
      />
    );

    const primaryButton = screen.getByTestId('proactive-action-button-0');
    expect(primaryButton).toHaveStyle({ backgroundColor: '#ff0000' });
  });
});
