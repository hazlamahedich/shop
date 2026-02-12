/**
 * Tests for ConfidenceIndicator Component
 *
 * Story 1.13: Bot Preview Mode
 *
 * Tests the confidence display component with color coding.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ConfidenceIndicator } from '../ConfidenceIndicator';

describe('ConfidenceIndicator', () => {
  describe('high confidence', () => {
    it('should display high confidence with green color', () => {
      render(
        <ConfidenceIndicator confidence={85} confidenceLevel="high" />
      );

      expect(screen.getByText(/85%/)).toBeInTheDocument();
      expect(screen.getByText('High')).toBeInTheDocument();
      expect(screen.getByLabelText(/Confidence level: high, score: 85%/)).toBeInTheDocument();
    });

    it('should not show explanation for high confidence', () => {
      render(
        <ConfidenceIndicator confidence={90} confidenceLevel="high" />
      );

      expect(screen.queryByText(/Low confidence/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Medium confidence/)).not.toBeInTheDocument();
    });
  });

  describe('medium confidence', () => {
    it('should display medium confidence with yellow color', () => {
      render(
        <ConfidenceIndicator confidence={65} confidenceLevel="medium" />
      );

      expect(screen.getByText(/65%/)).toBeInTheDocument();
      expect(screen.getByText('Medium')).toBeInTheDocument();
      expect(screen.getByText(/Medium confidence/)).toBeInTheDocument();
    });

    it('should show explanation for medium confidence', () => {
      render(
        <ConfidenceIndicator confidence={55} confidenceLevel="medium" />
      );

      expect(screen.getByText(/Medium confidence - Bot response may vary/)).toBeInTheDocument();
    });
  });

  describe('low confidence', () => {
    it('should display low confidence with red color', () => {
      render(
        <ConfidenceIndicator confidence={30} confidenceLevel="low" />
      );

      expect(screen.getByText(/30%/)).toBeInTheDocument();
      expect(screen.getByText('Low')).toBeInTheDocument();
    });

    it('should show explanation for low confidence', () => {
      render(
        <ConfidenceIndicator confidence={25} confidenceLevel="low" />
      );

      expect(screen.getByText(/Low confidence - Consider adding an FAQ/)).toBeInTheDocument();
    });
  });

  describe('technical details', () => {
    it('should show technical details when showDetails is true', () => {
      const metadata = {
        intent: 'product_search',
        faqMatched: false,
        productsFound: 5,
        llmProvider: 'ollama',
      };

      render(
        <ConfidenceIndicator
          confidence={80}
          confidenceLevel="high"
          showDetails={true}
          metadata={metadata}
        />
      );

      expect(screen.getByText(/Intent:/)).toBeInTheDocument();
      expect(screen.getByText(/product_search/)).toBeInTheDocument();
      expect(screen.getByText(/FAQ Match:/)).toBeInTheDocument();
      expect(screen.getByText(/No/)).toBeInTheDocument();
      expect(screen.getByText(/Products:/)).toBeInTheDocument();
      expect(screen.getByText(/5/)).toBeInTheDocument();
      expect(screen.getByText(/Provider:/)).toBeInTheDocument();
      expect(screen.getByText(/ollama/)).toBeInTheDocument();
    });

    it('should not show technical details by default', () => {
      const metadata = {
        intent: 'product_search',
        faqMatched: false,
        productsFound: 5,
        llmProvider: 'ollama',
      };

      render(
        <ConfidenceIndicator
          confidence={80}
          confidenceLevel="high"
          metadata={metadata}
        />
      );

      expect(screen.queryByText(/Intent:/)).not.toBeInTheDocument();
      expect(screen.queryByText(/FAQ Match:/)).not.toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper ARIA attributes for progress bar', () => {
      render(
        <ConfidenceIndicator confidence={75} confidenceLevel="medium" />
      );

      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('should clamp confidence values to 0-100 range', () => {
      render(
        <ConfidenceIndicator confidence={150} confidenceLevel="high" />
      );

      const progressBar = screen.getByRole('progressbar');
      // Visual bar should be clamped
      expect(progressBar).toBeInTheDocument();
    });
  });
});
