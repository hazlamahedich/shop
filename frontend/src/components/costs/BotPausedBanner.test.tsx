/**
 * Tests for BotPausedBanner Component
 *
 * Story 3-8: Budget Alert Notifications
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { BotPausedBanner } from './BotPausedBanner';

const mockResumeBot = vi.fn();

vi.mock('../../stores/costTrackingStore', () => ({
  useCostTrackingStore: vi.fn((selector) => {
    const state = {
      botStatus: {
        isPaused: false,
        pauseReason: null,
        budgetPercentage: null,
        budgetCap: null,
        monthlySpend: null,
      },
      resumeBot: mockResumeBot,
    };
    return selector(state);
  }),
}));

describe('BotPausedBanner', () => {
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

    const { container } = render(<BotPausedBanner />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when bot is paused', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    expect(screen.getByTestId('bot-paused-banner')).toBeInTheDocument();
    expect(screen.getByText(/Bot Paused/)).toBeInTheDocument();
  });

  it('displays pause reason', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded' },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    expect(screen.getByText(/Budget exceeded/)).toBeInTheDocument();
  });

  it('displays budget information when available', () => {
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

    render(<BotPausedBanner />);
    expect(screen.getByText(/Current budget: \$100.00/)).toBeInTheDocument();
    expect(screen.getByText(/Spent: \$105.00/)).toBeInTheDocument();
  });

  it('calls onIncreaseBudget when button clicked', () => {
    const onIncreaseBudget = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', budgetCap: 100 },
        merchantSettings: { budgetCap: 100, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner onIncreaseBudget={onIncreaseBudget} />);
    fireEvent.click(screen.getByText('Increase Budget to Resume'));
    expect(onIncreaseBudget).toHaveBeenCalled();
  });

  it('calls onViewSpending when View Spending clicked', () => {
    const onViewSpending = vi.fn();

    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', budgetCap: 100 },
        merchantSettings: { budgetCap: 100, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner onViewSpending={onViewSpending} />);
    fireEvent.click(screen.getByText('View Spending'));
    expect(onViewSpending).toHaveBeenCalled();
  });

  it('has no dismiss option (action required)', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', budgetCap: 100 },
        merchantSettings: { budgetCap: 100, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    expect(screen.queryByLabelText(/Dismiss/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/✕/)).not.toBeInTheDocument();
  });

  it('uses alert role for accessibility', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', budgetCap: 100 },
        merchantSettings: { budgetCap: 100, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('shows Resume Bot button when no budget limit set', () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', monthlySpend: 50 },
        merchantSettings: { budgetCap: null, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    expect(screen.getByText('Resume Bot')).toBeInTheDocument();
    expect(screen.queryByText('Increase Budget to Resume')).not.toBeInTheDocument();
    expect(screen.getByText(/No budget limit set/)).toBeInTheDocument();
  });

  it('calls resumeBot when Resume Bot button clicked', async () => {
    vi.mocked(useCostTrackingStore).mockImplementation((selector) => {
      const state = {
        botStatus: { isPaused: true, pauseReason: 'Budget exceeded', monthlySpend: 50 },
        merchantSettings: { budgetCap: null, config: {} },
        resumeBot: mockResumeBot,
      };
      return selector(state);
    });

    render(<BotPausedBanner />);
    fireEvent.click(screen.getByText('Resume Bot'));
    expect(mockResumeBot).toHaveBeenCalled();
  });
});

import { useCostTrackingStore } from '../../stores/costTrackingStore';
