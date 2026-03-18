/** Interactive Tutorial Keyboard Navigation Tests.

Tests keyboard navigation (arrows, enter, escape), screen reader announcements,
and focus management for the InteractiveTutorial component.
*/

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { InteractiveTutorial } from '../InteractiveTutorial';

// Mock the tutorial store
const mockTutorialStore = {
  currentStep: 1,
  completedSteps: [],
  isStarted: false,
  isCompleted: false,
  isSkipped: false,
  startedAt: null,
  completedAt: null,
  stepsTotal: 8,
  startTutorial: vi.fn(),
  nextStep: vi.fn(),
  previousStep: vi.fn(),
  jumpToStep: vi.fn(),
  completeStep: vi.fn(),
  skipTutorial: vi.fn(),
  completeTutorial: vi.fn(),
};

vi.mock('../../stores/tutorialStore', () => ({
  useTutorialStore: () => mockTutorialStore,
}));

describe('InteractiveTutorial - Keyboard Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should render tutorial when started', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Interactive Tutorial')).toBeInTheDocument();
    expect(screen.getByText('Follow these steps to learn how to use your shopping bot dashboard.')).toBeInTheDocument();
  });

  it('should not render when not started', () => {
    mockTutorialStore.isStarted = false;
    const { container } = render(<InteractiveTutorial />);

    expect(container.firstChild).toBeNull();
  });

  it('should show step 1 of 8 progress', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Step 1 of 8')).toBeInTheDocument();
  });

  it('should display all 8 step navigation dots', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    expect(dots).toHaveLength(8);
  });

  it('should highlight current step dot', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    const currentDot = dots[2]; // 0-indexed, so 2 = step 3

    expect(currentDot).toHaveClass('bg-blue-600');
  });

  it('should mark completed steps with green dot', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    mockTutorialStore.completedSteps = ['step-1', 'step-2'];
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');

    // First two should be green (completed)
    expect(dots[0]).toHaveClass('bg-green-500');
    expect(dots[1]).toHaveClass('bg-green-500');
  });
});

describe('InteractiveTutorial - Keyboard Events', () => {
  it('should advance to next step on ArrowRight', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 2;
    mockTutorialStore.stepsTotal = 8;
    render(<InteractiveTutorial />);

    fireEvent.keyDown(window, { key: 'ArrowRight' });

    expect(mockTutorialStore.nextStep).toHaveBeenCalled();
  });

  it('should go to previous step on ArrowLeft', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    fireEvent.keyDown(window, { key: 'ArrowLeft' });

    expect(mockTutorialStore.previousStep).toHaveBeenCalled();
  });

  it('should not go to previous when on step 1', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    fireEvent.keyDown(window, { key: 'ArrowLeft' });

    expect(mockTutorialStore.previousStep).not.toHaveBeenCalled();
  });

  it('should advance on Enter key', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 2;
    mockTutorialStore.stepsTotal = 8;
    render(<InteractiveTutorial />);

    fireEvent.keyDown(window, { key: 'Enter' });

    expect(mockTutorialStore.nextStep).toHaveBeenCalled();
  });

  it('should show skip confirmation on Escape', () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    fireEvent.keyDown(window, { key: 'Escape' });

    expect(confirmSpy).toHaveBeenCalledWith(
      'Are you sure you want to skip the tutorial? You can restart it anytime from the Help menu.'
    );
    expect(mockTutorialStore.skipTutorial).toHaveBeenCalled();

    confirmSpy.mockRestore();
  });
});

describe('InteractiveTutorial - Screen Reader Support', () => {
  it('should create ARIA live region for announcements', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 2;
    render(<InteractiveTutorial />);

    await waitFor(() => {
      const announcer = document.getElementById('tutorial-announcer');
      expect(announcer).toBeInTheDocument();
      expect(announcer).toHaveAttribute('aria-live', 'polite');
      expect(announcer).toHaveAttribute('aria-atomic', 'true');
    });
  });

  it('should announce step changes to screen readers', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    const { rerender } = render(<InteractiveTutorial />);

    // Change step to 4
    mockTutorialStore.currentStep = 4;
    rerender(<InteractiveTutorial />);

    await waitFor(() => {
      const announcer = document.getElementById('tutorial-announcer');
      expect(announcer?.textContent).toContain('Step 4 of 8');
    });
  });

  it('should announce progress percentage', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 4;
    mockTutorialStore.stepsTotal = 8;
    const { rerender } = render(<InteractiveTutorial />);

    await waitFor(() => {
      const announcer = document.getElementById('tutorial-announcer');
      expect(announcer?.textContent).toContain('50% complete');
    });
  });
});

describe('InteractiveTutorial - Step Navigation', () => {
  it('should complete current step when moving to next', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 2;
    render(<InteractiveTutorial />);

    const nextButtons = screen.getAllByRole('button', { name: /next/i });
    const nextButton = nextButtons.find(btn => btn.textContent?.includes('Next'));

    if (nextButton) {
      await userEvent.click(nextButton);

      expect(mockTutorialStore.completeStep).toHaveBeenCalledWith(2);
    }
  });

  it('should jump to step when clicking step dot', async () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    const step5Dot = dots[4]; // 0-indexed

    await userEvent.click(step5Dot);

    expect(mockTutorialStore.jumpToStep).toHaveBeenCalledWith(5);
  });
});
