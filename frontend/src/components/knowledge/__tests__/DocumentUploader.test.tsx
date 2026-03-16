/**
 * Component Test: DocumentUploader
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests drag-and-drop file upload component
 *
 * @tags component knowledge-base story-8-8 document-uploader
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DocumentUploader } from '../DocumentUploader';

describe('DocumentUploader', () => {
  const mockOnUpload = vi.fn();
  const defaultProps = {
    onUpload: mockOnUpload,
    isUploading: false,
    uploadProgress: 0,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Drop Zone Rendering', () => {
    it('renders upload zone with correct styling', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone).toBeInTheDocument();
      expect(uploadZone).toHaveClass('border-dashed');
    });

    it('displays upload icon', () => {
      render(<DocumentUploader {...defaultProps} />);

      expect(screen.getByTestId('upload-icon')).toBeInTheDocument();
    });

    it('displays upload instruction text', () => {
      render(<DocumentUploader {...defaultProps} />);

      expect(screen.getByText(/drag and drop files here/i)).toBeInTheDocument();
      expect(screen.getByText(/or click to browse/i)).toBeInTheDocument();
    });

    it('displays accepted file formats', () => {
      render(<DocumentUploader {...defaultProps} />);

      expect(screen.getByText(/pdf, txt, md, docx/i)).toBeInTheDocument();
      expect(screen.getByText(/max 10mb/i)).toBeInTheDocument();
    });

    it('has correct input accept attribute', () => {
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      expect(fileInput).toHaveAttribute('accept', '.pdf,.txt,.md,.docx');
    });
  });

  describe('Drag and Drop (AC2)', () => {
    it('highlights on drag over', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      fireEvent.dragOver(uploadZone);

      expect(uploadZone).toHaveClass('border-blue-500');
      expect(uploadZone).toHaveClass('bg-blue-50');
    });

    it('removes highlight on drag leave', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      fireEvent.dragOver(uploadZone);
      fireEvent.dragLeave(uploadZone);

      expect(uploadZone).not.toHaveClass('border-blue-500');
    });

    it('calls onUpload when file dropped', async () => {
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      const dataTransfer = {
        files: [file],
        types: ['Files'],
      };

      fireEvent.drop(uploadZone, { dataTransfer });

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('does not call onUpload when non-file dropped', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      const dataTransfer = {
        files: [],
        types: ['text/plain'],
      };

      fireEvent.drop(uploadZone, { dataTransfer });

      expect(mockOnUpload).not.toHaveBeenCalled();
    });
  });

  describe('File Picker (AC2)', () => {
    it('triggers file picker on click', async () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      const fileInput = screen.getByTestId('file-input');

      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.click(uploadZone);

      expect(clickSpy).toHaveBeenCalled();
    });

    it('calls onUpload when file selected', async () => {
      const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');

      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('does not call onUpload when no file selected', async () => {
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');

      await userEvent.upload(fileInput, []);

      expect(mockOnUpload).not.toHaveBeenCalled();
    });
  });

  describe('File Validation', () => {
    it('accepts PDF files', async () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('accepts TXT files', async () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('accepts MD files', async () => {
      const file = new File(['test'], 'test.md', { type: 'text/markdown' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('accepts DOCX files', async () => {
      const file = new File(['test'], 'test.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('shows error for invalid file type', async () => {
      const file = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(mockOnUpload).not.toHaveBeenCalled();
      });
      expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
    });

    it('shows error for file too large', async () => {
      const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' });
      Object.defineProperty(largeFile, 'size', { value: 11 * 1024 * 1024 });

      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      fireEvent.change(fileInput, { target: { files: [largeFile] } });

      await waitFor(() => {
        expect(mockOnUpload).not.toHaveBeenCalled();
      });
      expect(screen.getByText(/file too large/i)).toBeInTheDocument();
      expect(screen.getByText(/maximum size is 10\s*mb/i)).toBeInTheDocument();
    });

    it('clears error when valid file selected after error', async () => {
      const invalidFile = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      const validFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');

      fireEvent.change(fileInput, { target: { files: [invalidFile] } });
      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
      });

      fireEvent.change(fileInput, { target: { files: [validFile] } });
      await waitFor(() => {
        expect(screen.queryByText(/invalid file type/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Upload Progress', () => {
    it('shows progress bar when uploading', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={50} />);

      expect(screen.getByTestId('upload-progress')).toBeInTheDocument();
    });

    it('displays correct progress percentage', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={75} />);

      expect(screen.getByText(/75%/)).toBeInTheDocument();
    });

    it('displays uploading message with filename', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={50} />);

      expect(screen.getByText(/uploading/i)).toBeInTheDocument();
    });

    it('hides progress bar when not uploading', () => {
      render(<DocumentUploader {...defaultProps} isUploading={false} />);

      expect(screen.queryByTestId('upload-progress')).not.toBeInTheDocument();
    });

    it('animates progress bar', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={50} />);

      const progressBar = screen.getByTestId('progress-bar');
      expect(progressBar).toHaveStyle({ width: '50%' });
    });

    it('disables drop zone during upload', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={50} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone).toHaveAttribute('aria-disabled', 'true');
    });
  });

  describe('Accessibility', () => {
    it('has accessible upload zone with button role', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone).toHaveAttribute('role', 'button');
      expect(uploadZone.getAttribute('aria-label')).toMatch(/upload|drag.*drop/i);
    });

    it('has accessible file input with label', () => {
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      expect(fileInput).toHaveAttribute('type', 'file');
      expect(fileInput.getAttribute('aria-label')).toMatch(/file upload/i);
    });

    it('supports keyboard navigation with Enter key', async () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      const fileInput = screen.getByTestId('file-input');

      uploadZone.focus();
      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.keyDown(uploadZone, { key: 'Enter' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('supports keyboard navigation with Space key', async () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      const fileInput = screen.getByTestId('file-input');

      uploadZone.focus();
      const clickSpy = vi.spyOn(fileInput, 'click');

      fireEvent.keyDown(uploadZone, { key: ' ' });

      expect(clickSpy).toHaveBeenCalled();
    });

    it('has tabIndex for keyboard focus', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone).toHaveAttribute('tabIndex', '0');
    });

    it('announces drag state to screen readers', () => {
      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      fireEvent.dragOver(uploadZone);

      expect(uploadZone).toHaveAttribute('aria-dropeffect', 'copy');
    });

    it('has accessible progress bar', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} uploadProgress={50} />);

      const progressBar = screen.getByTestId('upload-progress');
      expect(progressBar).toHaveAttribute('role', 'progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('has live region for error announcements', async () => {
      const file = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        const errorMessage = screen.getByText(/invalid file type/i);
        expect(errorMessage.closest('[role="alert"]')).toBeInTheDocument();
      });
    });
  });

  describe('Disabled State', () => {
    it('disables during upload', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone).toHaveAttribute('aria-disabled', 'true');
    });

    it('prevents file selection when disabled', async () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} />);

      const uploadZone = screen.getByTestId('upload-zone');
      fireEvent.click(uploadZone);

      expect(mockOnUpload).not.toHaveBeenCalled();
    });

    it('prevents drop when disabled', async () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} isUploading={true} />);

      const uploadZone = screen.getByTestId('upload-zone');

      const dataTransfer = {
        files: [file],
        types: ['Files'],
      };

      fireEvent.drop(uploadZone, { dataTransfer });

      expect(mockOnUpload).not.toHaveBeenCalled();
    });

    it('shows disabled styling', () => {
      render(<DocumentUploader {...defaultProps} isUploading={true} />);

      const uploadZone = screen.getByTestId('upload-zone');
      expect(uploadZone.className.toLowerCase()).toContain('opacity');
    });
  });

  describe('Edge Cases', () => {
    it('handles multiple files dropped (only uses first)', async () => {
      const file1 = new File(['test1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['test2'], 'test2.pdf', { type: 'application/pdf' });

      render(<DocumentUploader {...defaultProps} />);

      const uploadZone = screen.getByTestId('upload-zone');

      const dataTransfer = {
        files: [file1, file2],
        types: ['Files'],
      };

      fireEvent.drop(uploadZone, { dataTransfer });

      expect(mockOnUpload).toHaveBeenCalledTimes(1);
      expect(mockOnUpload).toHaveBeenCalledWith(file1);
    });

    it('handles empty file list', async () => {
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, []);

      expect(mockOnUpload).not.toHaveBeenCalled();
    });

    it('handles files without extension', async () => {
      const file = new File(['test'], 'noextension', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(mockOnUpload).toHaveBeenCalledWith(file);
      });
    });

    it('handles case-insensitive file extensions', async () => {
      const file = new File(['test'], 'test.PDF', { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });

    it('handles exactly 10MB file', async () => {
      const exactSizeFile = new File(['x'.repeat(10 * 1024 * 1024)], 'exact.pdf', { type: 'application/pdf' });
      Object.defineProperty(exactSizeFile, 'size', { value: 10 * 1024 * 1024 });

      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, exactSizeFile);

      expect(mockOnUpload).toHaveBeenCalledWith(exactSizeFile);
    });

    it('handles files with special characters in name', async () => {
      const file = new File(['test'], "test's file (v2).pdf", { type: 'application/pdf' });
      render(<DocumentUploader {...defaultProps} />);

      const fileInput = screen.getByTestId('file-input');
      await userEvent.upload(fileInput, file);

      expect(mockOnUpload).toHaveBeenCalledWith(file);
    });
  });
});
