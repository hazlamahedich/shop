/**
 * Pagination Component Tests
 *
 * Tests pagination controls and interactions
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Pagination from './Pagination';

describe('Pagination', () => {
  const defaultProps = {
    currentPage: 1,
    totalPages: 5,
    total: 100,
    perPage: 20,
    onPageChange: vi.fn(),
    onPerPageChange: vi.fn(),
  };

  it('renders pagination info correctly', () => {
    render(<Pagination {...defaultProps} />);

    // Use custom matchers that check text content across multiple elements
    const infoText = screen.getByText((content, element) => {
      const hasText = (node: Element | null) => {
        return node?.textContent === 'Showing 1 to 20 of 100 results';
      };
      const elementHasText = hasText(element);
      const childrenDontHaveText = Array.from(element?.children || []).every(
        (child) => !hasText(child as Element)
      );
      return elementHasText && childrenDontHaveText;
    });
    expect(infoText).toBeInTheDocument();

    const pageText = screen.getByText((content, element) => {
      const hasText = (node: Element | null) => {
        return node?.textContent === 'Page 1 of 5';
      };
      const elementHasText = hasText(element);
      const childrenDontHaveText = Array.from(element?.children || []).every(
        (child) => !hasText(child as Element)
      );
      return elementHasText && childrenDontHaveText;
    });
    expect(pageText).toBeInTheDocument();
  });

  it('renders last page info correctly', () => {
    render(<Pagination {...defaultProps} currentPage={5} total={95} />);

    // Page 5: items 81-95 (not 81-100 as total is 95)
    const infoText = screen.getByText((content, element) => {
      const hasText = (node: Element | null) => {
        return node?.textContent === 'Showing 81 to 95 of 95 results';
      };
      const elementHasText = hasText(element);
      const childrenDontHaveText = Array.from(element?.children || []).every(
        (child) => !hasText(child as Element)
      );
      return elementHasText && childrenDontHaveText;
    });
    expect(infoText).toBeInTheDocument();
  });

  it('disables prev button on first page', () => {
    render(<Pagination {...defaultProps} currentPage={1} />);

    const prevButton = screen.getByLabelText('Previous page');
    expect(prevButton).toBeDisabled();
  });

  it('disables next button on last page', () => {
    render(<Pagination {...defaultProps} currentPage={5} totalPages={5} />);

    const nextButton = screen.getByLabelText('Next page');
    expect(nextButton).toBeDisabled();
  });

  it('calls onPageChange with next page when next button clicked', async () => {
    const user = userEvent.setup();
    render(<Pagination {...defaultProps} currentPage={1} />);

    const nextButton = screen.getByLabelText('Next page');
    await user.click(nextButton);

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(2);
  });

  it('calls onPageChange with previous page when prev button clicked', async () => {
    const user = userEvent.setup();
    render(<Pagination {...defaultProps} currentPage={2} />);

    const prevButton = screen.getByLabelText('Previous page');
    await user.click(prevButton);

    expect(defaultProps.onPageChange).toHaveBeenCalledWith(1);
  });

  it('calls onPerPageChange when per page selection changes', async () => {
    const user = userEvent.setup();
    render(<Pagination {...defaultProps} />);

    const select = screen.getByRole('combobox');
    await user.selectOptions(select, '50');

    expect(defaultProps.onPerPageChange).toHaveBeenCalledWith(50);
  });

  it('shows loading state when isLoading is true', () => {
    render(<Pagination {...defaultProps} isLoading={true} />);

    const prevButton = screen.getByLabelText('Previous page');
    const nextButton = screen.getByLabelText('Next page');
    const select = screen.getByRole('combobox');

    expect(prevButton).toBeDisabled();
    expect(nextButton).toBeDisabled();
    expect(select).toBeDisabled();
  });

  it('shows all per page options', () => {
    render(<Pagination {...defaultProps} />);

    screen.getByRole('combobox');
    const options = screen.getAllByRole('option');

    expect(options).toHaveLength(4);
    expect(options[0]).toHaveValue('10');
    expect(options[1]).toHaveValue('20');
    expect(options[2]).toHaveValue('50');
    expect(options[3]).toHaveValue('100');
  });
});
