/**
 * Comprehensive test suite for DeploymentWizard component.
 * Tests component rendering, interactions, state management, accessibility, and edge cases.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';

// Mock the stores - declare mock store variables first
let mockDeploymentStoreState: any;
let mockOnboardingStoreState: any;

vi.mock('../../../stores/deploymentStore', () => ({
  useDeploymentStore: vi.fn(() => mockDeploymentStoreState),
}));

vi.mock('../../../stores/onboardingStore', () => ({
  onboardingStore: vi.fn(() => mockOnboardingStoreState),
}));

// Mock all UI components to isolate testing - using factory functions with return
vi.mock('../ui/Card', () => {
  return {
    Card: ({ children, ...props }: any) => <div data-testid="card" {...props}>{children}</div>,
    CardHeader: ({ children, ...props }: any) => <div data-testid="card-header" {...props}>{children}</div>,
    CardTitle: ({ children, ...props }: any) => <h2 data-testid="card-title" {...props}>{children}</h2>,
    CardDescription: ({ children, ...props }: any) => <p data-testid="card-description" {...props}>{children}</p>,
    CardContent: ({ children, ...props }: any) => <div data-testid="card-content" {...props}>{children}</div>,
    CardFooter: ({ children, ...props }: any) => <div data-testid="card-footer" {...props}>{children}</div>,
  };
});

vi.mock('../ui/Button', () => {
  return {
    Button: ({ children, disabled, ...props }: any) => (
      <button data-testid="button" disabled={disabled} {...props}>
        {children}
      </button>
    ),
  };
});

vi.mock('../ui/Select', () => {
  return {
    Select: ({ label, options, value, onChange, disabled, placeholder, ...props }: any) => (
      <div data-testid="select">
        <label data-testid="select-label">{label}</label>
        <select
          data-testid="select-input"
          value={value || ''}
          onChange={onChange}
          disabled={disabled}
          {...props}
        >
          <option value="">{placeholder}</option>
          {options.map((opt: any) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>
    ),
  };
});

vi.mock('../ui/Progress', () => {
  return {
    Progress: ({ value, max, ...props }: any) => (
      <div data-testid="progress" {...props}>
        <span data-testid="progress-value">{value}%</span>
        <span data-testid="progress-max">/ 100%</span>
      </div>
    ),
  };
});

vi.mock('../ui/Alert', () => {
  return {
    Alert: ({ variant, title, children, ...props }: any) => (
      <div data-testid={`alert-${variant}`} {...props}>
        {title && <h3 data-testid="alert-title">{title}</h3>}
        {children}
      </div>
    ),
  };
});

vi.mock('../ui/Badge', () => {
  return {
    Badge: ({ variant, children, ...props }: any) => (
      <span data-testid={`badge-${variant}`} {...props}>
        {children}
      </span>
    ),
  };
});

vi.mock('../ui/ScrollArea', () => {
  return {
    ScrollArea: ({ children, ...props }: any) => (
      <div data-testid="scroll-area" {...props}>
        {children}
      </div>
    ),
  };
});

// Import the component AFTER mocks
const { DeploymentWizard } = await import('../DeploymentWizard');

describe('DeploymentWizard', () => {
  beforeEach(() => {
    // Reset mock implementations
    vi.clearAllMocks();

    // Initialize mock deployment store state
    mockDeploymentStoreState = {
      platform: null,
      status: 'pending',
      progress: 0,
      logs: [],
      currentStep: null,
      errorMessage: null,
      troubleshootingUrl: null,
      merchantKey: null,
      deploymentId: null,
      estimatedSeconds: 900,
      startDeployment: vi.fn(),
      cancelDeployment: vi.fn(),
      reset: vi.fn(),
      setPlatform: vi.fn(),
      pollDeploymentStatus: vi.fn(() => () => {}), // Returns cleanup function
      updateDeploymentStatus: vi.fn(),
      addLog: vi.fn(),
    };

    // Initialize mock onboarding store state
    mockOnboardingStoreState = {
      isComplete: vi.fn().mockReturnValue(true),
    };
  });

  afterEach(() => {
    cleanup();
  });

  describe('Component Rendering', () => {
    it('renders initial state with platform selection', () => {
      render(<DeploymentWizard />);

      // Check main card elements
      expect(screen.getByTestId('card')).toBeInTheDocument();
      expect(screen.getByTestId('card-title')).toHaveTextContent('Deploy Your Bot');
      expect(screen.getByTestId('card-description')).toHaveTextContent(
        'Choose your cloud platform and deploy with one click.'
      );
      expect(screen.getByTestId('card-description')).toHaveTextContent('Estimated time:');

      // Check platform selection
      expect(screen.getByTestId('select')).toBeInTheDocument();
      expect(screen.getByTestId('select-label')).toHaveTextContent('Select Deployment Platform');
      expect(screen.getByTestId('select-input')).toHaveValue('');

      // Check platform options
      const options = screen.getByTestId('select-input').querySelectorAll('option');
      expect(options).toHaveLength(4); // 3 options + placeholder

      // Check platform labels
      expect(options[1]).toHaveValue('flyio');
      expect(options[1]).toHaveTextContent('Fly.io (Recommended)');
      expect(options[2]).toHaveValue('railway');
      expect(options[2]).toHaveTextContent('Railway');
      expect(options[3]).toHaveValue('render');
      expect(options[3]).toHaveTextContent('Render');
    });

    it('shows platform info when platform is selected', () => {
      mockDeploymentStoreState.platform = 'flyio';

      render(<DeploymentWizard />);

      // Should show platform info
      const platformInfo = screen.getByText('Fastest deploy experience, free tier available');
      expect(platformInfo).toBeInTheDocument();

      // Should show documentation link
      const link = screen.getByRole('link', { name: 'View Fly.io documentation →' });
      expect(link).toHaveAttribute('href', 'https://fly.io/docs/hands-on/start/');
    });

    it('disables deploy button when no platform is selected', () => {
      render(<DeploymentWizard />);

      const deployButton = screen.getByRole('button', { name: 'Select a platform to deploy' });
      expect(deployButton).toBeInTheDocument();
      expect(deployButton).toBeDisabled();
    });

    it('shows correct deploy button text when platform is selected', () => {
      mockDeploymentStoreState.platform = 'flyio';

      render(<DeploymentWizard />);

      const deployButton = screen.getByRole('button', { name: 'Deploy to Fly.io' });
      expect(deployButton).toBeInTheDocument();
      expect(deployButton).not.toBeDisabled();
    });

    it('shows prerequisites warning when not complete', () => {
      mockOnboardingStoreState.isComplete.mockReturnValue(false);

      render(<DeploymentWizard />);

      const warning = screen.getByText('Complete all prerequisites before deploying');
      expect(warning).toBeInTheDocument();
      expect(warning).toHaveClass('text-sm', 'text-slate-500', 'text-center');
    });
  });

  describe('Deployment States', () => {
    it('shows deploying state with progress', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.progress = 50;
      mockDeploymentStoreState.currentStep = 'Building container';

      render(<DeploymentWizard />);

      // Should show status badge
      const badge = screen.getByTestId('badge-default');
      expect(badge).toHaveTextContent('Deploying: Building container');

      // Should show progress
      expect(screen.getByTestId('progress-value')).toHaveTextContent('50%');

      // Should show cancel button
      const cancelButton = screen.getByRole('button', { name: 'Cancel' });
      expect(cancelButton).toBeInTheDocument();
      expect(cancelButton).not.toBeDisabled();
    });

    it('shows success state with merchant key', () => {
      mockDeploymentStoreState.status = 'success';
      mockDeploymentStoreState.progress = 100;
      mockDeploymentStoreState.merchantKey = 'test-merchant-key-123';

      render(<DeploymentWizard />);

      // Should show success badge
      const badge = screen.getByTestId('badge-success');
      expect(badge).toHaveTextContent('Deployment Complete');

      // Should show success message
      const alert = screen.getByTestId('alert-default');
      expect(alert).toBeInTheDocument();
      expect(screen.getByText('Your bot has been deployed successfully')).toBeInTheDocument();

      // Should show merchant key
      const merchantKey = screen.getByText('test-merchant-key-123');
      expect(merchantKey).toBeInTheDocument();
      expect(merchantKey.closest('code')).toHaveClass('px-1', 'py-0.5', 'bg-slate-100', 'rounded', 'text-sm');

      // Should show next steps
      expect(screen.getByText('Next Steps:')).toBeInTheDocument();
      expect(screen.getByText('Connect your Facebook Page (Story 1.3)')).toBeInTheDocument();
      expect(screen.getByText('Connect your Shopify Store (Story 1.4)')).toBeInTheDocument();
      expect(screen.getByText('Configure your LLM Provider (Story 1.5)')).toBeInTheDocument();

      // Should show deploy again button
      const deployAgainButton = screen.getByRole('button', { name: 'Deploy Again' });
      expect(deployAgainButton).toBeInTheDocument();
    });

    it('shows failed state with error message', () => {
      mockDeploymentStoreState.status = 'failed';
      mockDeploymentStoreState.progress = 75;
      mockDeploymentStoreState.errorMessage = 'Failed to authenticate with provider';
      mockDeploymentStoreState.troubleshootingUrl = 'https://example.com/troubleshooting';

      render(<DeploymentWizard />);

      // Should show error badge
      const badge = screen.getByTestId('badge-destructive');
      expect(badge).toHaveTextContent('Deployment Failed');

      // Should show error alert
      const alert = screen.getByTestId('alert-destructive');
      expect(alert).toBeInTheDocument();
      expect(screen.getByText('Deployment Failed')).toBeInTheDocument();
      expect(screen.getByText('Failed to authenticate with provider')).toBeInTheDocument();

      // Should show troubleshooting link
      const link = screen.getByRole('link', { name: 'View troubleshooting guide →' });
      expect(link).toHaveAttribute('href', 'https://example.com/troubleshooting');
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');

      // Should show deploy again button
      const deployAgainButton = screen.getByRole('button', { name: 'Deploy Again' });
      expect(deployAgainButton).toBeInTheDocument();
    });

    it('shows cancelled state', () => {
      mockDeploymentStoreState.status = 'cancelled';

      render(<DeploymentWizard />);

      // Should show cancelled badge
      const badge = screen.getByTestId('badge-default');
      expect(badge).toHaveTextContent('Deployment Cancelled');

      // Should show deploy again button
      const deployAgainButton = screen.getByRole('button', { name: 'Deploy Again' });
      expect(deployAgainButton).toBeInTheDocument();
    });

    it('shows deployment logs when available', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.logs = [
        { timestamp: new Date().toISOString(), level: 'info', message: 'Starting deployment...' },
        { timestamp: new Date().toISOString(), level: 'info', message: 'Pulling image...' },
        { timestamp: new Date().toISOString(), level: 'warning', message: 'Cache miss, rebuilding...' },
        { timestamp: new Date().toISOString(), level: 'error', message: 'Failed to build image' },
      ];

      render(<DeploymentWizard />);

      // Should show scroll area with logs
      const scrollArea = screen.getByTestId('scroll-area');
      expect(scrollArea).toBeInTheDocument();

      // Should show log title
      expect(screen.getByText('Deployment Logs')).toBeInTheDocument();

      // Should show all log entries
      const logEntries = scrollArea.querySelectorAll('.flex.gap-2');
      expect(logEntries).toHaveLength(4);

      // Check log styling
      const errorLog = logEntries[3].querySelector('.text-red-600');
      expect(errorLog).toBeInTheDocument();

      const warningLog = scrollArea.querySelector('.text-yellow-600');
      expect(warningLog).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('allows platform selection', async () => {
      const user = userEvent.setup();
      render(<DeploymentWizard />);

      const select = screen.getByTestId('select-input');

      // Select Fly.io
      await user.selectOptions(select, 'flyio');

      // Verify setPlatform was called
      expect(mockDeploymentStoreState.setPlatform).toHaveBeenCalledWith('flyio');

      // Verify platform info is shown
      const platformInfo = screen.getByText('Fastest deploy experience, free tier available');
      expect(platformInfo).toBeInTheDocument();
    });

    it('calls startDeployment when deploy button is clicked', async () => {
      const user = userEvent.setup();
      mockDeploymentStoreState.platform = 'flyio';

      render(<DeploymentWizard />);

      const deployButton = screen.getByRole('button', { name: 'Deploy to Fly.io' });

      // Click deploy button
      await user.click(deployButton);

      // Verify startDeployment was called
      expect(mockDeploymentStoreState.startDeployment).toHaveBeenCalledWith('flyio');
    });

    it('calls cancelDeployment when cancel button is clicked', async () => {
      const user = userEvent.setup();
      mockDeploymentStoreState.status = 'inProgress';

      render(<DeploymentWizard />);

      const cancelButton = screen.getByRole('button', { name: 'Cancel' });

      // Click cancel button
      await user.click(cancelButton);

      // Verify cancelDeployment was called
      expect(mockDeploymentStoreState.cancelDeployment).toHaveBeenCalled();
    });

    it('calls reset when deploy again button is clicked', async () => {
      const user = userEvent.setup();
      mockDeploymentStoreState.status = 'success';

      render(<DeploymentWizard />);

      const deployAgainButton = screen.getByRole('button', { name: 'Deploy Again' });

      // Click deploy again button
      await user.click(deployAgainButton);

      // Verify reset was called
      expect(mockDeploymentStoreState.reset).toHaveBeenCalled();
    });
  });

  describe('State Management', () => {
    it('handles platform state correctly', () => {
      mockDeploymentStoreState.platform = 'railway';

      render(<DeploymentWizard />);

      // Verify platform is reflected in UI
      const select = screen.getByTestId('select-input');
      expect(select).toHaveValue('railway');

      // Verify platform info is shown
      const platformInfo = screen.getByText('Simple deployment with $5 free credit monthly');
      expect(platformInfo).toBeInTheDocument();
    });

    it('disables controls during deployment', () => {
      mockDeploymentStoreState.status = 'inProgress';

      render(<DeploymentWizard />);

      // Platform select should be disabled
      const select = screen.getByTestId('select-input');
      expect(select).toHaveAttribute('disabled');

      // Deploy button should not be visible (replaced by cancel button)
      expect(screen.queryByRole('button', { name: 'Deploy to Fly.io' })).not.toBeInTheDocument();
    });

    it('updates progress correctly', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.progress = 75;

      render(<DeploymentWizard />);

      expect(screen.getByTestId('progress-value')).toHaveTextContent('75%');
    });
  });

  describe('Edge Cases', () => {
    it('handles empty logs array', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.logs = [];

      render(<DeploymentWizard />);

      // Should not show scroll area
      expect(screen.queryByTestId('scroll-area')).not.toBeInTheDocument();
    });

    it('handles missing merchant key in success state', () => {
      mockDeploymentStoreState.status = 'success';
      mockDeploymentStoreState.merchantKey = null;

      render(<DeploymentWizard />);

      // Should still show success message but without merchant key
      const alert = screen.getByTestId('alert-default');
      expect(alert).toBeInTheDocument();
      expect(screen.getByText('Your bot has been deployed successfully')).toBeInTheDocument();
      expect(screen.queryByText('Your merchant key is')).not.toBeInTheDocument();
    });

    it('handles missing error message in failed state', () => {
      mockDeploymentStoreState.status = 'failed';
      mockDeploymentStoreState.errorMessage = null;

      render(<DeploymentWizard />);

      // Should show error badge but no error details
      const badge = screen.getByTestId('badge-destructive');
      expect(badge).toHaveTextContent('Deployment Failed');

      // Should show error alert without specific message
      const alert = screen.getByTestId('alert-destructive');
      expect(alert).toBeInTheDocument();
    });

    it('handles missing troubleshooting URL in failed state', () => {
      mockDeploymentStoreState.status = 'failed';
      mockDeploymentStoreState.errorMessage = 'Some error';
      mockDeploymentStoreState.troubleshootingUrl = null;

      render(<DeploymentWizard />);

      // Should not show troubleshooting link
      expect(screen.queryByRole('link', { name: 'View troubleshooting guide →' })).not.toBeInTheDocument();
    });

    it('handles platform selection without platform info', () => {
      mockDeploymentStoreState.platform = 'unknown' as any;

      render(<DeploymentWizard />);

      // Should not crash
      const select = screen.getByTestId('select-input');
      expect(select).toHaveValue('unknown');

      // Should not show platform info
      expect(screen.queryByText('Fastest deploy experience')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<DeploymentWizard />);

      const cardTitle = screen.getByTestId('card-title');
      expect(cardTitle.tagName).toBe('H2');
    });

    it('progress has proper attributes', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.progress = 50;

      render(<DeploymentWizard />);

      const progressContainer = screen.getByTestId('progress').closest('div');
      expect(progressContainer).toHaveTextContent('Deployment Progress');
      expect(progressContainer).toHaveTextContent('50%');
    });

    it('deployment logs have proper ARIA attributes', () => {
      mockDeploymentStoreState.status = 'inProgress';
      mockDeploymentStoreState.logs = [
        { timestamp: new Date().toISOString(), level: 'info', message: 'Test log' },
      ];

      render(<DeploymentWizard />);

      const scrollArea = screen.getByTestId('scroll-area');
      const logContainer = scrollArea.querySelector('[role="log"]');
      expect(logContainer).toHaveAttribute('aria-live', 'polite');
      expect(logContainer).toHaveAttribute('aria-atomic', 'true');
    });

    it('all interactive elements have proper labels', () => {
      render(<DeploymentWizard />);

      // Select should have proper label
      expect(screen.getByTestId('select-label')).toHaveTextContent('Select Deployment Platform');

      // Buttons should have proper names
      const deployButton = screen.getByRole('button', { name: 'Select a platform to deploy' });
      expect(deployButton).toBeInTheDocument();
    });

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<DeploymentWizard />);

      // Test tab through select
      await user.tab();
      expect(screen.getByTestId('select-input')).toHaveFocus();

      // Test tab through deploy button
      await user.tab();
      const deployButton = screen.getByRole('button', { name: 'Select a platform to deploy' });
      expect(deployButton).toHaveFocus();
    });
  });

  describe('Error Handling', () => {
    it('handles API errors gracefully', () => {
      mockDeploymentStoreState.startDeployment.mockRejectedValueOnce(new Error('Network error'));

      render(<DeploymentWizard />);

      // Should not crash
      expect(() => {
        screen.getByRole('button', { name: 'Select a platform to deploy' });
      }).not.toThrow();
    });

    it('handles store state corruption', () => {
      // Simulate invalid state
      mockDeploymentStoreState.platform = undefined;

      render(<DeploymentWizard />);

      // Should still render
      expect(screen.getByTestId('card')).toBeInTheDocument();
    });
  });
});
