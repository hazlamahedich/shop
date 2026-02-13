/** Interactive Tutorial Component Tests.

Tests the main tutorial container component including:
- Rendering with various states
- Step navigation functionality
- Progress tracking
- Modal behavior
- Accessibility features
*/

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { InteractiveTutorial } from '../InteractiveTutorial';

// Mock tutorial store
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

describe('InteractiveTutorial - Component Rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should not render when not started', () => {
    mockTutorialStore.isStarted = false;
    const { container } = render(<InteractiveTutorial />);

    expect(container.firstChild).toBeNull();
  });

  it('should render tutorial when started', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Interactive Tutorial')).toBeInTheDocument();
    expect(screen.getByText(/Follow these steps to learn how to use/)).toBeInTheDocument();
  });

  it('should show current step title', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
  });

  it('should show progress indicator', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Step 3 of 8')).toBeInTheDocument();
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

  it('should show step content for current step', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    expect(screen.getByText(/View Conversation List/)).toBeInTheDocument();
    expect(screen.getByText(/Your dashboard displays all customer conversations/)).toBeInTheDocument();
  });
});

describe('InteractiveTutorial - Step Navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

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

  it('should call jumpToStep when clicking step dot', async () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    const step5Dot = dots[4]; // 0-indexed

    await userEvent.click(step5Dot);

    expect(mockTutorialStore.jumpToStep).toHaveBeenCalledWith(5);
  });

  it('should not call previousStep when on step 1', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    const prevButton = screen.queryByRole('button', { name: /previous/i });

    expect(prevButton).not.toBeInTheDocument();
  });

  it('should call previousStep when on step 2+', async () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    const prevButton = screen.getByRole('button', { name: /previous/i });

    await userEvent.click(prevButton);

    expect(mockTutorialStore.previousStep).toHaveBeenCalled();
  });
});

describe('InteractiveTutorial - Completion Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should show completion modal when tutorial completed', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.isCompleted = true;
    render(<InteractiveTutorial />);

    expect(screen.getByText(/Tutorial Complete/)).toBeInTheDocument();
  });

  it('should show completion summary', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.isCompleted = true;
    mockTutorialStore.completedSteps = ['step-1', 'step-2', 'step-3', 'step-4', 'step-5', 'step-6', 'step-7', 'step-8'];
    render(<InteractiveTutorial />);

    expect(screen.getByText(/Congratulations/)).toBeInTheDocument();
    expect(screen.getByText(/You've completed all 8 tutorial steps/)).toBeInTheDocument();
  });

  it('should call onComplete when clicking Go to Dashboard', async () => {
    const mockOnComplete = vi.fn();
    mockTutorialStore.isStarted = true;
    mockTutorialStore.isCompleted = true;
    render(<InteractiveTutorial onComplete={mockOnComplete} />);

    const goToDashboardButton = screen.getByRole('button', { name: /go to dashboard/i });

    await userEvent.click(goToDashboardButton);

    expect(mockOnComplete).toHaveBeenCalled();
  });
});

describe('InteractiveTutorial - Auto-start Behavior', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should auto-start tutorial when not started', async () => {
    mockTutorialStore.isStarted = false;
    render(<InteractiveTutorial />);

    await waitFor(() => {
      expect(mockTutorialStore.startTutorial).toHaveBeenCalled();
    });
  });

  it('should not auto-start when already started', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    expect(mockTutorialStore.startTutorial).not.toHaveBeenCalled();
  });
});

describe('InteractiveTutorial - Accessibility', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should have ARIA labels on step dots', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    dots.forEach((dot, index) => {
      expect(dot).toHaveAttribute('aria-label', expect.stringContaining(`Step ${index + 1}`));
    });
  });

  it('should mark current step with aria-selected', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    const dots = screen.getAllByRole('tab');
    const currentDot = dots[2];

    expect(currentDot).toHaveAttribute('aria-selected', 'true');
  });

  it('should have proper ARIA role for step list', () => {
    mockTutorialStore.isStarted = true;
    render(<InteractiveTutorial />);

    const stepList = screen.getByRole('tablist');
    expect(stepList).toHaveAttribute('aria-label', 'Tutorial steps');
  });
});

describe('InteractiveTutorial - Step Content Accuracy', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('should show Step 1: Dashboard Overview', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 1;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Dashboard Overview')).toBeInTheDocument();
    expect(screen.getByText(/View Conversation List/)).toBeInTheDocument();
  });

  it('should show Step 2: Cost Tracking', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 2;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Cost Tracking')).toBeInTheDocument();
    expect(screen.getByText(/View Cost Tracking Panel/)).toBeInTheDocument();
  });

  it('should show Step 3: LLM Provider Switching', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 3;
    render(<InteractiveTutorial />);

    expect(screen.getByText('LLM Provider Switching')).toBeInTheDocument();
    expect(screen.getByText(/View Provider Settings/)).toBeInTheDocument();
  });

  it('should show Step 4: Bot Testing with BotPreview', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 4;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Test Your Bot')).toBeInTheDocument();
    expect(screen.getByText(/Test Bot with Preview Pane/)).toBeInTheDocument();
  });

  it('should show Step 5: Bot Personality Selection', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 5;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Bot Personality Selection')).toBeInTheDocument();
    expect(screen.getByText(/Select Bot Personality/)).toBeInTheDocument();
  });

  it('should show Step 6: Business Info & FAQ Configuration', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 6;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Business Info & FAQ Configuration')).toBeInTheDocument();
    expect(screen.getByText(/Configure Business Info & FAQ/)).toBeInTheDocument();
  });

  it('should show Step 7: Bot Naming', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 7;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Bot Naming')).toBeInTheDocument();
    expect(screen.getByText(/Set Bot Name/)).toBeInTheDocument();
  });

  it('should show Step 8: Smart Greetings & Product Pins', () => {
    mockTutorialStore.isStarted = true;
    mockTutorialStore.currentStep = 8;
    render(<InteractiveTutorial />);

    expect(screen.getByText('Smart Greetings & Product Pins')).toBeInTheDocument();
    expect(screen.getByText(/Configure Greetings & Pins/)).toBeInTheDocument();
  });
});
