/**
 * BudgetProgressBar Component Tests
 *
 * Story 3-7: Visual Budget Progress
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { BudgetProgressBar } from './BudgetProgressBar';
import type { BudgetProgress } from '../../types/cost';

describe('BudgetProgressBar', () => {
  beforeEach(() => {
    // Mock IntersectionObserver for animations
    vi.stubGlobal('IntersectionObserver', vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  describe('Loading State', () => {
    it('should render skeleton when loading', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={null} loading={true} />
      );

      // Check for skeleton elements (animate-pulse class creates these)
      const skeletonElements = container.querySelectorAll('.animate-pulse');
      expect(skeletonElements.length).toBeGreaterThan(0);

      // Should have skeleton divs for header and content
      expect(container.querySelector('.h-6.bg-gray-200')).toBeDefined();
      expect(container.querySelector('.h-8.bg-gray-200')).toBeDefined();
    });
  });

  describe('No Budget Cap (no_limit status)', () => {
    const noLimitProgress: BudgetProgress = {
      monthlySpend: 12.50,
      budgetCap: null,
      budgetPercentage: null,
      budgetStatus: 'no_limit',
      daysSoFar: 15,
      daysInMonth: 28,
      dailyAverage: 0.83,
      projectedSpend: 23.24,
      projectionAvailable: true,
      projectedExceedsBudget: false,
    };

    it('should display monthly spend without budget cap', () => {
      render(<BudgetProgressBar budgetProgress={noLimitProgress} />);

      expect(screen.getByText('$12.50 spent this month')).toBeDefined();
      expect(screen.getByText('No budget cap configured')).toBeDefined();
    });

    it('should show no_limit status indicator', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={noLimitProgress} />
      );

      // Should show gray dot for no_limit status
      const statusDot = container.querySelector('.bg-gray-500');
      expect(statusDot).toBeDefined();
    });

    it('should not show progress bar when no budget cap', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={noLimitProgress} />
      );

      // Progress bar should not be rendered
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeNull();
    });
  });

  describe('Green Status (< 50% budget used)', () => {
    const greenProgress: BudgetProgress = {
      monthlySpend: 15.00,
      budgetCap: 50.00,
      budgetPercentage: 30.0,
      budgetStatus: 'green',
      daysSoFar: 15,
      daysInMonth: 28,
      dailyAverage: 1.00,
      projectedSpend: 28.00,
      projectionAvailable: true,
      projectedExceedsBudget: false,
    };

    it('should display monthly spend and budget cap', () => {
      render(<BudgetProgressBar budgetProgress={greenProgress} />);

      expect(screen.getByText('$15.00')).toBeDefined(); // monthly spend
      expect(screen.getByText('$50.00')).toBeDefined(); // budget cap
    });

    it('should show green progress bar with correct percentage', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={greenProgress} />
      );

      // Check for progress bar
      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toBeDefined();
      expect(progressBar).toHaveAttribute('aria-valuenow', '30');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');

      // Should have green background
      const progressFill = container.querySelector('.bg-green-500');
      expect(progressFill).toBeDefined();
    });

    it('should show percentage and remaining budget', () => {
      render(<BudgetProgressBar budgetProgress={greenProgress} />);

      expect(screen.getByText('30.0% of budget used')).toBeDefined();
      expect(screen.getByText(/\$35\.00 remaining/)).toBeDefined();
    });

    it('should show green status text', () => {
      render(<BudgetProgressBar budgetProgress={greenProgress} />);

      expect(screen.getByText('On track - well within budget')).toBeDefined();
    });

    it('should have accessible ARIA labels', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={greenProgress} />
      );

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute(
        'aria-label',
        'Budget progress: 30% of $50.00 used'
      );
    });
  });

  describe('Yellow Status (50-80% budget used)', () => {
    const yellowProgress: BudgetProgress = {
      monthlySpend: 35.00,
      budgetCap: 50.00,
      budgetPercentage: 70.0,
      budgetStatus: 'yellow',
      daysSoFar: 20,
      daysInMonth: 28,
      dailyAverage: 1.75,
      projectedSpend: 49.00,
      projectionAvailable: true,
      projectedExceedsBudget: false,
    };

    it('should display yellow status text', () => {
      render(<BudgetProgressBar budgetProgress={yellowProgress} />);

      expect(
        screen.getByText('Caution - more than half budget used')
      ).toBeDefined();
    });

    it('should show yellow progress bar', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={yellowProgress} />
      );

      const progressFill = container.querySelector('.bg-yellow-500');
      expect(progressFill).toBeDefined();
    });

    it('should not show warning alert for yellow status', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={yellowProgress} />
      );

      const alert = container.querySelector('[role="alert"]');
      expect(alert).toBeNull();
    });
  });

  describe('Red Status (>= 80% budget used)', () => {
    const redProgress: BudgetProgress = {
      monthlySpend: 42.50,
      budgetCap: 50.00,
      budgetPercentage: 85.0,
      budgetStatus: 'red',
      daysSoFar: 22,
      daysInMonth: 28,
      dailyAverage: 1.93,
      projectedSpend: 54.04,
      projectionAvailable: true,
      projectedExceedsBudget: true,
    };

    it('should display red status text', () => {
      render(<BudgetProgressBar budgetProgress={redProgress} />);

      expect(screen.getByText('Warning - approaching budget limit')).toBeDefined();
    });

    it('should show red progress bar', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={redProgress} />
      );

      const progressFill = container.querySelector('.bg-red-500');
      expect(progressFill).toBeDefined();
    });

    it('should show warning alert with action recommendation', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={redProgress} />
      );

      const alert = container.querySelector('[role="alert"]');
      expect(alert).toBeDefined();
      expect(alert?.textContent).toContain('85.0% of your monthly budget');
      expect(alert?.textContent).toContain('Consider reducing usage');
    });

    it('should animate the red status indicator', () => {
      const { container } = render(
        <BudgetProgressBar budgetProgress={redProgress} />
      );

      // Red status should have animate-pulse
      const statusDot = container.querySelector('.bg-red-500.animate-pulse');
      expect(statusDot).toBeDefined();
    });
  });

  describe('Edge Cases', () => {
    it('should handle null budgetProgress', () => {
      render(<BudgetProgressBar budgetProgress={null} loading={false} />);

      expect(screen.getByText('Budget Progress')).toBeDefined();
      expect(screen.getByText('Unable to load budget data')).toBeDefined();
    });

    it('should clamp percentage at 100%', () => {
      const overBudgetProgress: BudgetProgress = {
        monthlySpend: 60.00,
        budgetCap: 50.00,
        budgetPercentage: 120.0,
        budgetStatus: 'red',
        daysSoFar: 25,
        daysInMonth: 28,
        dailyAverage: 2.40,
        projectedSpend: 67.20,
        projectionAvailable: true,
        projectedExceedsBudget: true,
      };

      const { container } = render(
        <BudgetProgressBar budgetProgress={overBudgetProgress} />
      );

      const progressBar = container.querySelector('[role="progressbar"]');
      expect(progressBar).toHaveAttribute('aria-valuenow', '100');
    });

    it('should handle zero monthly spend', () => {
      const zeroSpendProgress: BudgetProgress = {
        monthlySpend: 0,
        budgetCap: 50.00,
        budgetPercentage: 0,
        budgetStatus: 'green',
        daysSoFar: 5,
        daysInMonth: 28,
        dailyAverage: 0,
        projectedSpend: 0,
        projectionAvailable: true,
        projectedExceedsBudget: false,
      };

      render(<BudgetProgressBar budgetProgress={zeroSpendProgress} />);

      expect(screen.getByText('$0.00')).toBeDefined(); // Should show $0.00
      expect(screen.getByText('0.0% of budget used')).toBeDefined();
    });
  });

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <BudgetProgressBar
          budgetProgress={null}
          loading={false}
          className="custom-class"
        />
      );

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper.className).toContain('custom-class');
    });
  });
});
