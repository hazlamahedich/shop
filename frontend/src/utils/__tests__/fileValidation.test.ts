/**
 * Unit Test: File Validation Utilities
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Tests file validation logic for document uploads
 *
 * @tags unit knowledge-base story-8-8 file-validation
 */

import { describe, it, expect } from 'vitest';
import {
  validateFileType,
  validateFileSize,
  formatFileSize,
  getFileExtension,
  isValidDocumentFile,
} from '../fileValidation';

describe('fileValidation', () => {
  describe('validateFileType', () => {
    it('accepts PDF files', () => {
      const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts TXT files', () => {
      const file = new File(['test'], 'test.txt', { type: 'text/plain' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts MD files', () => {
      const file = new File(['test'], 'test.md', { type: 'text/markdown' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts DOCX files', () => {
      const file = new File(['test'], 'test.docx', {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      });
      expect(validateFileType(file)).toBe(true);
    });

    it('rejects EXE files', () => {
      const file = new File(['test'], 'test.exe', { type: 'application/octet-stream' });
      expect(validateFileType(file)).toBe(false);
    });

    it('rejects JS files', () => {
      const file = new File(['test'], 'test.js', { type: 'text/javascript' });
      expect(validateFileType(file)).toBe(false);
    });

    it('rejects PNG files', () => {
      const file = new File(['test'], 'test.png', { type: 'image/png' });
      expect(validateFileType(file)).toBe(false);
    });

    it('accepts uppercase extensions', () => {
      const file = new File(['test'], 'test.PDF', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts mixed case extensions', () => {
      const file = new File(['test'], 'test.PdF', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts files without extension if MIME type is valid', () => {
      const file = new File(['test'], 'noextension', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });

    it('accepts files with multiple dots in name', () => {
      const file = new File(['test'], 'my.document.v2.pdf', { type: 'application/pdf' });
      expect(validateFileType(file)).toBe(true);
    });
  });

  describe('validateFileSize', () => {
    const TEN_MB = 10 * 1024 * 1024;

    it('accepts file smaller than 10MB', () => {
      const file = new File(['x'.repeat(5 * 1024 * 1024)], 'small.pdf');
      Object.defineProperty(file, 'size', { value: 5 * 1024 * 1024 });
      expect(validateFileSize(file)).toBe(true);
    });

    it('accepts file exactly 10MB', () => {
      const file = new File(['x'.repeat(TEN_MB)], 'exact.pdf');
      Object.defineProperty(file, 'size', { value: TEN_MB });
      expect(validateFileSize(file)).toBe(true);
    });

    it('rejects file larger than 10MB', () => {
      const file = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf');
      Object.defineProperty(file, 'size', { value: 11 * 1024 * 1024 });
      expect(validateFileSize(file)).toBe(false);
    });

    it('accepts very small files', () => {
      const file = new File(['test'], 'tiny.txt');
      Object.defineProperty(file, 'size', { value: 100 });
      expect(validateFileSize(file)).toBe(true);
    });

    it('accepts zero-byte files', () => {
      const file = new File([], 'empty.txt');
      Object.defineProperty(file, 'size', { value: 0 });
      expect(validateFileSize(file)).toBe(true);
    });

    it('rejects file 1 byte over limit', () => {
      const file = new File(['x'], 'over.pdf');
      Object.defineProperty(file, 'size', { value: TEN_MB + 1 });
      expect(validateFileSize(file)).toBe(false);
    });

    it('handles edge case: 10MB - 1 byte', () => {
      const file = new File(['x'], 'under.pdf');
      Object.defineProperty(file, 'size', { value: TEN_MB - 1 });
      expect(validateFileSize(file)).toBe(true);
    });
  });

  describe('formatFileSize', () => {
    it('formats bytes correctly', () => {
      expect(formatFileSize(0)).toBe('0 B');
      expect(formatFileSize(100)).toBe('100 B');
      expect(formatFileSize(512)).toBe('512 B');
      expect(formatFileSize(1023)).toBe('1023 B');
    });

    it('formats kilobytes correctly', () => {
      expect(formatFileSize(1024)).toBe('1 KB');
      expect(formatFileSize(1536)).toBe('1.5 KB');
      expect(formatFileSize(5120)).toBe('5 KB');
      expect(formatFileSize(10240)).toBe('10 KB');
      expect(formatFileSize(1024 * 100)).toBe('100 KB');
      expect(formatFileSize(1024 * 500)).toBe('500 KB');
    });

    it('formats megabytes correctly', () => {
      expect(formatFileSize(1024 * 1024)).toBe('1 MB');
      expect(formatFileSize(1024 * 1024 * 1.5)).toBe('1.5 MB');
      expect(formatFileSize(1024 * 1024 * 5)).toBe('5 MB');
      expect(formatFileSize(1024 * 1024 * 10)).toBe('10 MB');
      expect(formatFileSize(1024 * 1024 * 100)).toBe('100 MB');
    });

    it('rounds to 1 decimal place', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB');
      expect(formatFileSize(2560)).toBe('2.5 KB');
      expect(formatFileSize(1024 * 1024 * 1.23)).toBe('1.2 MB');
      expect(formatFileSize(1024 * 1024 * 5.67)).toBe('5.7 MB');
    });

    it('handles very large files', () => {
      expect(formatFileSize(1024 * 1024 * 1024)).toBe('1 GB');
      expect(formatFileSize(1024 * 1024 * 1024 * 5)).toBe('5 GB');
    });
  });

  describe('getFileExtension', () => {
    it('extracts PDF extension', () => {
      expect(getFileExtension('document.pdf')).toBe('pdf');
    });

    it('extracts TXT extension', () => {
      expect(getFileExtension('notes.txt')).toBe('txt');
    });

    it('extracts MD extension', () => {
      expect(getFileExtension('readme.md')).toBe('md');
    });

    it('extracts DOCX extension', () => {
      expect(getFileExtension('report.docx')).toBe('docx');
    });

    it('handles uppercase extensions', () => {
      expect(getFileExtension('document.PDF')).toBe('pdf');
      expect(getFileExtension('document.TXT')).toBe('txt');
    });

    it('handles mixed case extensions', () => {
      expect(getFileExtension('document.PdF')).toBe('pdf');
      expect(getFileExtension('document.TxT')).toBe('txt');
    });

    it('returns empty string for no extension', () => {
      expect(getFileExtension('noextension')).toBe('');
    });

    it('handles multiple dots in filename', () => {
      expect(getFileExtension('my.document.v2.pdf')).toBe('pdf');
      expect(getFileExtension('file.name.with.dots.txt')).toBe('txt');
    });

    it('handles hidden files', () => {
      expect(getFileExtension('.gitignore')).toBe('');
      expect(getFileExtension('.env')).toBe('');
      expect(getFileExtension('.hidden.pdf')).toBe('pdf');
    });

    it('handles filenames with spaces', () => {
      expect(getFileExtension('my document.pdf')).toBe('pdf');
      expect(getFileExtension('report final v2.txt')).toBe('txt');
    });

    it('handles filenames with special characters', () => {
      expect(getFileExtension("test's file.pdf")).toBe('pdf');
      expect(getFileExtension('file (copy).txt')).toBe('txt');
      expect(getFileExtension('file-v1.2.md')).toBe('md');
    });
  });

  describe('isValidDocumentFile', () => {
    const createMockFile = (name: string, size: number, type: string): File => {
      const file = new File(['x'.repeat(size)], name, { type });
      Object.defineProperty(file, 'size', { value: size });
      return file;
    };

    it('returns valid for small PDF', () => {
      const file = createMockFile('test.pdf', 1024, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('returns valid for 10MB PDF', () => {
      const size = 10 * 1024 * 1024;
      const file = createMockFile('large.pdf', size, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
      expect(result.error).toBeUndefined();
    });

    it('returns invalid for file too large', () => {
      const size = 11 * 1024 * 1024;
      const file = createMockFile('toolarge.pdf', size, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('too large');
      expect(result.error).toContain('10 MB');
    });

    it('returns invalid for wrong file type', () => {
      const file = createMockFile('test.exe', 1024, 'application/octet-stream');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toContain('Invalid file type');
      expect(result.error).toContain('.pdf, .txt, .md, .docx');
    });

    it('returns invalid for file too large and wrong type (reports size first)', () => {
      const size = 11 * 1024 * 1024;
      const file = createMockFile('toolarge.exe', size, 'application/octet-stream');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(false);
      expect(result.error).toBeDefined();
    });

    it('validates all accepted file types', () => {
      const testCases = [
        { name: 'test.pdf', type: 'application/pdf' },
        { name: 'test.txt', type: 'text/plain' },
        { name: 'test.md', type: 'text/markdown' },
        {
          name: 'test.docx',
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        },
      ];

      testCases.forEach(({ name, type }) => {
        const file = createMockFile(name, 1024, type);
        const result = isValidDocumentFile(file);
        expect(result.valid).toBe(true);
      });
    });

    it('validates files with uppercase extensions', () => {
      const file = createMockFile('TEST.PDF', 1024, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
    });

    it('validates files with mixed case extensions', () => {
      const file = createMockFile('Test.PdF', 1024, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
    });

    it('accepts files without extensions if MIME type is valid', () => {
      const file = createMockFile('noextension', 1024, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
    });

    it('validates zero-byte files', () => {
      const file = createMockFile('empty.txt', 0, 'text/plain');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
    });

    it('validates files with special characters in name', () => {
      const file = createMockFile("test's file (v2).pdf", 1024, 'application/pdf');
      const result = isValidDocumentFile(file);
      expect(result.valid).toBe(true);
    });
  });

  describe('Integration: validateFileType + validateFileSize', () => {
    const createMockFile = (name: string, size: number, type: string): File => {
      const file = new File(['x'.repeat(size)], name, { type });
      Object.defineProperty(file, 'size', { value: size });
      return file;
    };

    it('accepts valid PDF under size limit', () => {
      const file = createMockFile('valid.pdf', 5 * 1024 * 1024, 'application/pdf');
      expect(validateFileType(file)).toBe(true);
      expect(validateFileSize(file)).toBe(true);
    });

    it('rejects PDF over size limit', () => {
      const file = createMockFile('large.pdf', 11 * 1024 * 1024, 'application/pdf');
      expect(validateFileType(file)).toBe(true);
      expect(validateFileSize(file)).toBe(false);
    });

    it('rejects EXE under size limit', () => {
      const file = createMockFile('malware.exe', 1024, 'application/octet-stream');
      expect(validateFileType(file)).toBe(false);
      expect(validateFileSize(file)).toBe(true);
    });

    it('rejects EXE over size limit', () => {
      const file = createMockFile('large.exe', 11 * 1024 * 1024, 'application/octet-stream');
      expect(validateFileType(file)).toBe(false);
      expect(validateFileSize(file)).toBe(false);
    });
  });
});
