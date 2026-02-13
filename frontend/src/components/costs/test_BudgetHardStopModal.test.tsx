/**
 * Tests for BudgetHardStopModal Component
 *
 * Story 3-8: Budget Alert Notifications
 * Tests focus trap and accessibility requirements
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { BudgetHardStopModal } from './BudgetHardStopModal';

const mockResumeBot = vi.fn();

vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn((selector) => {
    const state = {
      botStatus: {
        isPaused: false,
        pauseReason: null,
        budgetCap: null,
        monthlySpend: null,
      },
      resumeBot: mockResumeBot,
    };
    return selector(state);
  }),
}));

describe('BudgetHardStopModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('does not render when bot is not paused', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: false, pauseReason: null },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    const { container } = render(<BudgetHardStopModal />);
    expect(container.firstChild).toBeNull();
  });

  it('renders modal when bot is paused', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    expect(screen.getByTestId('budget-hard-stop-modal')).toBeInTheDocument();
    expect(screen.getByText(/Bot Paused/i)).toBeInTheDocument();
  });

  it('displays pause reason', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    expect(screen.getByText(/Budget exceeded/i)).toBeInTheDocument();
  });

  it('displays budget information', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: {
          isPaused: true,
          pauseReason: 'Budget exceeded',
          budgetCap: 100,
          monthlySpend: 105,
        },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    expect(screen.getByText(/\$100.00/)).toBeInTheDocument();
    expect(screen.getByText(/\$105.00/)).toBeInTheDocument();
  });

  it('calls onIncreaseBudget when Increase Budget clicked', () => {
    const onIncreaseBudget = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal onIncreaseBudget={onIncreaseBudget} />);
    fireEvent.click(screen.getByText('Increase Budget'));
    expect(onIncreaseBudget).toHaveBeenCalled();
  });

  it('disables Resume button when spend exceeds budget', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: {
          isPaused: true,
          pauseReason: 'Budget exceeded',
          budgetCap: 100,
          monthlySpend: 105,
        },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    const resumeButton = screen.getByRole('button', { name: /Resume bot operations/i });
    expect(resumeButton).toBeDisabled();
  });

  it('enables Resume button when budget exceeds spend', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: {
          isPaused: true,
          pauseReason: 'Budget exceeded',
          budgetCap: 200,
          monthlySpend: 105,
        },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    const resumeButton = screen.getByRole('button', { name: /Resume bot operations/i });
    expect(resumeButton).toBeEnabled();
  });

  it('calls resumeBot when Resume clicked', async () => {
    mockResumeBot.mockResolvedValue(undefined);

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: {
          isPaused: true,
          pauseReason: 'Budget exceeded',
          budgetCap: 200,
          monthlySpend: 105,
        },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);
    fireEvent.click(screen.getByRole('button', { name: /Resume bot operations/i }));

    await waitFor(() => {
      expect(mockResumeBot).toHaveBeenCalled();
    });
  });

  it('has correct ARIA attributes for accessibility', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);

    const modal = screen.getByRole('dialog');
    expect(modal).toHaveAttribute('aria-modal', 'true');
    expect(modal).toHaveAttribute('aria-labelledby');
    expect(modal).toHaveAttribute('aria-describedby');
  });

  it('traps focus within modal on Tab', async () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: {
          isPaused: true,
          pauseReason: 'Budget exceeded',
          budgetCap: 200,
          monthlySpend: 50,
        },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal />);

    const increaseButton = screen.getByRole('button', { name: /Increase budget to resume bot/i });
    const resumeButton = screen.getByRole('button', { name: /Resume bot operations/i });

    increaseButton.focus();
    expect(document.activeElement).toBe(increaseButton);

    fireEvent.keyDown(document.activeElement!, { key: 'Tab', shiftKey: true });
  });

  it('calls onClose when Escape pressed', () => {
    const onClose = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BudgetHardStopModal onClose={onClose} />);

    fireEvent.keyDown(document, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });
});

import { useCostTrackingStore } from '../../stores/costTrackingStore';
