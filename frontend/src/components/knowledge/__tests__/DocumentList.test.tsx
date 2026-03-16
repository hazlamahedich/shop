/**
 * Component Test: DocumentList
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests document list rendering and interactions
 *
 * @tags component knowledge-base story-8-8 document-list
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { DocumentList } from '../DocumentList';
import type { KnowledgeDocument, DocumentStatus } from '../../../types/knowledgeBase';

function createDocument(overrides: Partial<KnowledgeDocument> = {}): KnowledgeDocument {
  return {
    id: Math.floor(Math.random() * 1000),
    filename: 'test-document.pdf',
    fileType: 'application/pdf',
    fileSize: 1024,
    status: 'ready',
    chunkCount: 5,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...overrides,
  };
}

describe('DocumentList', () => {
  const mockOnDelete = vi.fn();
  const mockOnRetry = vi.fn();
  const mockOnPollStatus = vi.fn();

  const defaultProps = {
    documents: [] as KnowledgeDocument[],
    onDelete: mockOnDelete,
    onRetry: mockOnRetry,
    onPollStatus: mockOnPollStatus,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Empty State', () => {
    it('shows empty state when no documents', () => {
      render(<DocumentList {...defaultProps} documents={[]} />);

      expect(screen.getByTestId('empty-state')).toBeInTheDocument();
      expect(screen.getByText(/no documents uploaded yet/i)).toBeInTheDocument();
    });

    it('shows upload prompt in empty state', () => {
      render(<DocumentList {...defaultProps} documents={[]} />);

      expect(screen.getByText(/upload your first document/i)).toBeInTheDocument();
    });
  });

  describe('Document Rendering', () => {
    it('renders document list with correct columns', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Size')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Uploaded')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders multiple documents', () => {
      const documents = [
        createDocument({ id: 1, filename: 'doc1.pdf' }),
        createDocument({ id: 2, filename: 'doc2.txt' }),
        createDocument({ id: 3, filename: 'doc3.md' }),
      ];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText('doc1.pdf')).toBeInTheDocument();
      expect(screen.getByText('doc2.txt')).toBeInTheDocument();
      expect(screen.getByText('doc3.md')).toBeInTheDocument();
    });

    it('displays document filename', () => {
      const documents = [createDocument({ id: 1, filename: 'product-catalog.pdf' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText('product-catalog.pdf')).toBeInTheDocument();
    });

    it('displays file type correctly', () => {
      const testCases = [
        { fileType: 'application/pdf', expected: 'PDF' },
        { fileType: 'text/plain', expected: 'TXT' },
        { fileType: 'text/markdown', expected: 'MD' },
        { fileType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', expected: 'DOCX' },
      ];

      testCases.forEach(({ fileType, expected }) => {
        const documents = [createDocument({ id: 1, fileType })];
        const { unmount } = render(<DocumentList {...defaultProps} documents={documents} />);

        expect(screen.getByText(expected)).toBeInTheDocument();
        unmount();
      });
    });

    it('displays file size in correct format', () => {
      const testCases = [
        { fileSize: 512, expected: '512 B' },
        { fileSize: 1024, expected: '1 KB' },
        { fileSize: 1536000, expected: '1.5 MB' },
        { fileSize: 5242880, expected: '5 MB' },
      ];

      testCases.forEach(({ fileSize, expected }) => {
        const documents = [createDocument({ id: 1, fileSize })];
        const { unmount } = render(<DocumentList {...defaultProps} documents={documents} />);

        expect(screen.getByText(new RegExp(expected, 'i'))).toBeInTheDocument();
        unmount();
      });
    });

    it('displays relative time for upload date', () => {
      const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
      const documents = [createDocument({ id: 1, createdAt: twoHoursAgo })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText(/2 hours ago/i)).toBeInTheDocument();
    });
  });

  describe('Status Indicators (AC4, AC5)', () => {
    it('shows spinner for processing documents (AC4)', () => {
      const documents = [createDocument({ id: 1, status: 'processing' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(within(row).getByTestId('spinner-1')).toBeInTheDocument();
      expect(within(row).getByTestId('status-badge-1')).toHaveTextContent(/processing/i);
    });

    it('shows checkmark for ready documents', () => {
      const documents = [createDocument({ id: 1, status: 'ready' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(within(row).getByTestId('status-badge-1')).toHaveTextContent(/ready/i);
    });

    it('shows error message for failed documents (AC5)', () => {
      const documents = [
        createDocument({
          id: 1,
          status: 'error',
          errorMessage: 'Failed to process: Invalid PDF format',
        }),
      ];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(within(row).getByText(/error/i)).toBeInTheDocument();
      expect(within(row).getByText(/invalid pdf format/i)).toBeInTheDocument();
    });

    it('shows retry button for error documents (AC5)', () => {
      const documents = [createDocument({ id: 1, status: 'error' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const retryButton = screen.getByTestId('retry-document-1');
      expect(retryButton).toBeInTheDocument();
    });

    it('shows pending status for pending documents', () => {
      const documents = [createDocument({ id: 1, status: 'pending' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(within(row).getByText(/pending/i)).toBeInTheDocument();
    });

    it('applies correct status badge colors', () => {
      const statusColors: Array<{ status: DocumentStatus; expectedClass: string }> = [
        { status: 'processing', expectedClass: 'yellow' },
        { status: 'ready', expectedClass: 'green' },
        { status: 'error', expectedClass: 'red' },
        { status: 'pending', expectedClass: 'gray' },
      ];

      statusColors.forEach(({ status, expectedClass }) => {
        const documents = [createDocument({ id: 1, status })];
        const { unmount } = render(<DocumentList {...defaultProps} documents={documents} />);

        const badge = screen.getByTestId('status-badge-1');
        expect(badge.className.toLowerCase()).toContain(expectedClass);
        unmount();
      });
    });
  });

  describe('Delete Functionality (AC3)', () => {
    it('shows delete button for each document', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByTestId('delete-document-1')).toBeInTheDocument();
    });

    it('shows confirmation dialog when delete clicked (AC3)', () => {
      const documents = [createDocument({ id: 1, filename: 'important.pdf' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      fireEvent.click(deleteButton);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toBeInTheDocument();
      expect(within(dialog).getByText(/delete document/i)).toBeInTheDocument();
      expect(within(dialog).getByText(/important\.pdf/)).toBeInTheDocument();
    });

    it('calls onDelete when confirmed (AC3)', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      fireEvent.click(deleteButton);

      const dialog = screen.getByRole('alertdialog');
      const confirmButton = within(dialog).getByRole('button', { name: /delete/i });
      fireEvent.click(confirmButton);

      expect(mockOnDelete).toHaveBeenCalledWith(1);
    });

    it('does not call onDelete when cancelled', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      fireEvent.click(deleteButton);

      const dialog = screen.getByRole('alertdialog');
      const cancelButton = within(dialog).getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(mockOnDelete).not.toHaveBeenCalled();
    });

    it('closes dialog when cancelled', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      fireEvent.click(deleteButton);

      const dialog = screen.getByRole('alertdialog');
      const cancelButton = within(dialog).getByRole('button', { name: /cancel/i });
      fireEvent.click(cancelButton);

      expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument();
    });
  });

  describe('Retry Functionality (AC5)', () => {
    it('calls onRetry when retry button clicked', () => {
      const documents = [createDocument({ id: 1, status: 'error' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const retryButton = screen.getByTestId('retry-document-1');
      fireEvent.click(retryButton);

      expect(mockOnRetry).toHaveBeenCalledWith(1);
    });

    it('does not show retry button for non-error documents', () => {
      const statuses: DocumentStatus[] = ['pending', 'processing', 'ready'];

      statuses.forEach((status) => {
        const documents = [createDocument({ id: 1, status })];
        const { unmount } = render(<DocumentList {...defaultProps} documents={documents} />);

        expect(screen.queryByTestId('retry-document-1')).not.toBeInTheDocument();
        unmount();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper table structure', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(6);
    });

    it('has accessible status badges', () => {
      const documents = [createDocument({ id: 1, status: 'processing' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const badge = screen.getByTestId('status-badge-1');
      expect(badge.getAttribute('aria-label')).toMatch(/processing/i);
    });

    it('has accessible delete button', () => {
      const documents = [createDocument({ id: 1, filename: 'test.pdf' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      expect(deleteButton.getAttribute('aria-label')).toMatch(/delete test\.pdf/i);
    });

    it('has accessible retry button', () => {
      const documents = [createDocument({ id: 1, status: 'error', filename: 'failed.pdf' })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const retryButton = screen.getByTestId('retry-document-1');
      expect(retryButton.getAttribute('aria-label')).toMatch(/retry failed\.pdf/i);
    });

    it('has accessible dialog with proper ARIA', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      fireEvent.click(deleteButton);

      const dialog = screen.getByRole('alertdialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby');
      expect(dialog).toHaveAttribute('aria-describedby');
    });

    it('supports keyboard navigation', () => {
      const documents = [createDocument({ id: 1 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const deleteButton = screen.getByTestId('delete-document-1');
      deleteButton.focus();
      expect(deleteButton).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('handles very long filenames gracefully', () => {
      const longName = 'a'.repeat(100) + '.pdf';
      const documents = [createDocument({ id: 1, filename: longName })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(row).toBeInTheDocument();
    });

    it('handles special characters in filename', () => {
      const specialName = "test's document (v2).pdf";
      const documents = [createDocument({ id: 1, filename: specialName })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText(specialName)).toBeInTheDocument();
    });

    it('handles zero chunk count', () => {
      const documents = [createDocument({ id: 1, chunkCount: 0 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      const row = screen.getByTestId('document-row-1');
      expect(row).toBeInTheDocument();
    });

    it('handles very large file sizes', () => {
      const documents = [createDocument({ id: 1, fileSize: 10 * 1024 * 1024 })];
      render(<DocumentList {...defaultProps} documents={documents} />);

      expect(screen.getByText(/10 mb/i)).toBeInTheDocument();
    });
  });
});
