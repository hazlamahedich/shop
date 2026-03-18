/**
 * BudgetProjection Component Tests
 *
 * Story 3-7: Visual Budget Progress
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { BudgetProjection } from './BudgetProjection';
import type { BudgetProgress } from '../../types/cost';

describe('BudgetProjection', () => {
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
        <BudgetProjection budgetProgress={null} loading={true} />
      );

      // Check for skeleton elements (animate-pulse class creates these)
      const skeletonElements = container.querySelectorAll('.animate-pulse');
      expect(skeletonElements.length).toBeGreaterThan(0);

      // Should have skeleton divs for header and content
      expect(container.querySelector('.h-6.bg-gray-200')).toBeDefined();
      expect(container.querySelector('.h-16.bg-gray-200')).toBeDefined();
    });
  });

  describe('No Data State', () => {
    it('should show unable to load message when budgetProgress is null', () => {
      render(<BudgetProjection budgetProgress={null} loading={false} />);

      expect(screen.getByText('Unable to load projection data')).toBeDefined();
    });
  });

  describe('Projection Available (on track)', () => {
    const onTrackProgress: BudgetProgress = {
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

    it('should display calendar days progress', () => {
      render(<BudgetProjection budgetProgress={onTrackProgress} />);

      expect(screen.getByText('Days in month')).toBeDefined();
      expect(screen.getByText('15 / 28')).toBeDefined();
      expect(screen.getByText('54%')).toBeDefined(); // ~54% of month passed
    });

    it('should display daily average', () => {
      render(<BudgetProjection budgetProgress={onTrackProgress} />);

      expect(screen.getByText('Daily average')).toBeDefined();
      expect(screen.getByText('$1.00')).toBeDefined();
    });

    it('should show on-track projection message', () => {
      render(<BudgetProjection budgetProgress={onTrackProgress} />);

      expect(screen.getByText(/On track to spend/)).toBeDefined();
      expect(screen.getByText(/\$28\.00 this month/)).toBeDefined();
      expect(screen.getByText(/Based on daily average of/)).toBeDefined();

      // The projection subtext contains the daily average
      expect(screen.getByText(/Based on daily average of \$1\.00/)).toBeDefined();
    });

    it('should show info level styling (blue)', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={onTrackProgress} />
      );

      // Should have blue styling for info level
      expect(container.querySelector('.bg-blue-50')).toBeDefined();
      expect(container.querySelector('.text-blue-600')).toBeDefined();

      // Should not show warning indicator
      expect(screen.queryByText('Action needed')).toBeNull();
    });

    it('should show projected spend vs budget bar', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={onTrackProgress} />
      );

      expect(screen.getByText('Projected spend')).toBeDefined();

      // Find the projected value in the comparison section
      const projectedValues = container.querySelectorAll('.font-medium.text-gray-900');
      const projectedValue = Array.from(projectedValues).find(el => el.textContent === '$28.00');
      expect(projectedValue).toBeDefined();

      // Check progress bar exists
      const progressBar = container.querySelector('.bg-blue-500');
      expect(progressBar).toBeDefined();
    });
  });

  describe('Projection Exceeds Budget (warning)', () => {
    const warningProgress: BudgetProgress = {
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

    it('should show warning level styling (amber)', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={warningProgress} />
      );

      // Should have amber styling for warning
      expect(container.querySelector('.bg-amber-50')).toBeDefined();
      expect(container.querySelector('.text-amber-600')).toBeDefined();
    });

    it('should show action needed indicator', () => {
      render(<BudgetProjection budgetProgress={warningProgress} />);

      expect(screen.getByText('Action needed')).toBeDefined();
    });

    it('should display warning message with excess amount', () => {
      render(<BudgetProjection budgetProgress={warningProgress} />);

      expect(screen.getByText(/Projected to exceed budget by/)).toBeDefined();
      expect(screen.getByText(/\$4\.04/)).toBeDefined(); // 54.04 - 50.00
    });

    it('should show percentage over budget', () => {
      render(<BudgetProjection budgetProgress={warningProgress} />);

      // (54.04 - 50) / 50 * 100 = ~8%
      expect(screen.getByText(/This is 8% over your budget/)).toBeDefined();
    });

    it('should show recommendation message', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={warningProgress} />
      );

      expect(container.textContent).toContain('Recommendation:');
      expect(container.textContent).toContain('increasing your budget cap');
    });

    it('should have left border accent for warning', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={warningProgress} />
      );

      // Should have left-4 border-l-amber-500
      const warningBox = container.querySelector('.border-l-4.border-l-amber-500');
      expect(warningBox).toBeDefined();
    });
  });

  describe('Insufficient Data for Projection', () => {
    const insufficientProgress: BudgetProgress = {
      monthlySpend: 3.50,
      budgetCap: 50.00,
      budgetPercentage: 7.0,
      budgetStatus: 'green',
      daysSoFar: 2,
      daysInMonth: 28,
      dailyAverage: 1.75,
      projectedSpend: null,
      projectionAvailable: false,
      projectedExceedsBudget: false,
    };

    it('should show insufficient data message', () => {
      render(<BudgetProjection budgetProgress={insufficientProgress} />);

      expect(screen.getByText('Insufficient data for projection')).toBeDefined();
    });

    it('should show explanation about needing 3 days of data', () => {
      render(<BudgetProjection budgetProgress={insufficientProgress} />);

      expect(
        screen.getByText(/Need at least 3 days of data/)
      ).toBeDefined();
      expect(screen.getByText(/currently 2 days/)).toBeDefined();
    });

    it('should still show calendar days progress', () => {
      render(<BudgetProjection budgetProgress={insufficientProgress} />);

      expect(screen.getByText('2 / 28')).toBeDefined();
    });

    it('should not show daily average or projection bar when unavailable', () => {
      const { container } = render(
        <BudgetProjection budgetProgress={insufficientProgress} />
      );

      // Daily average section should not be shown
      expect(container.textContent).not.toContain('Daily average');

      // Projected spend section should not show the bar
      expect(container.querySelector('.bg-gray-200.rounded-full.h-2')).toBeNull();
    });
  });

  describe('Edge Cases', () => {
    it('should handle first day of month (1 day)', () => {
      const firstDayProgress: BudgetProgress = {
        monthlySpend: 0.50,
        budgetCap: 50.00,
        budgetPercentage: 1.0,
        budgetStatus: 'green',
        daysSoFar: 1,
        daysInMonth: 28,
        dailyAverage: 0.50,
        projectedSpend: null,
        projectionAvailable: false,
        projectedExceedsBudget: false,
      };

      render(<BudgetProjection budgetProgress={firstDayProgress} />);

      expect(screen.getByText('1 / 28')).toBeDefined();
      expect(screen.getByText('4%')).toBeDefined(); // 1/28 = ~3.6% -> 4%
      expect(screen.getByText(/currently 1 day/)).toBeDefined();
    });

    it('should handle zero daily average', () => {
      const zeroAvgProgress: BudgetProgress = {
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

      render(<BudgetProjection budgetProgress={zeroAvgProgress} />);

      expect(screen.getByText('Daily average')).toBeDefined();
      expect(screen.getAllByText(/\$0\.00/).length).toBeGreaterThan(0);
    });

    it('should handle plural vs singular day display', () => {
      const singleDayProgress: BudgetProgress = {
        monthlySpend: 1.50,
        budgetCap: 50.00,
        budgetPercentage: 3.0,
        budgetStatus: 'green',
        daysSoFar: 1,
        daysInMonth: 28,
        dailyAverage: 1.50,
        projectedSpend: null,
        projectionAvailable: false,
        projectedExceedsBudget: false,
      };

      render(<BudgetProjection budgetProgress={singleDayProgress} />);

      // Should say "currently 1 day" not "days"
      expect(screen.getByText(/currently 1 day/)).toBeDefined();
    });
  });

  describe('Custom className', () => {
    it('should apply custom className', () => {
      const { container } = render(
        <BudgetProjection
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
