/**
 * File Validation Utilities
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Validates file types and sizes for document uploads
 */

export const ACCEPTED_FILE_TYPES = ['.pdf', '.txt', '.md', '.docx'];
export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'text/plain',
  'text/markdown',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];

/**
 * Validates if file type is accepted (checks both extension and MIME type)
 */
export function validateFileType(file: File): boolean {
  const extension = getFileExtension(file.name);
  
  if (extension) {
    const normalizedExtension = extension.toLowerCase();
    return ACCEPTED_FILE_TYPES.includes(`.${normalizedExtension}`);
  }

  return ACCEPTED_MIME_TYPES.includes(file.type);
}

/**
 * Validates if file size is within limits
 */
export function validateFileSize(file: File, maxSize: number = MAX_FILE_SIZE): boolean {
  return file.size <= maxSize;
}

/**
 * Formats file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB'];
  const k = 1024;
  const i = Math.min(Math.floor(Math.log(bytes) / Math.log(k)), units.length - 1);
  const size = bytes / Math.pow(k, i);

  // Round to 1 decimal place
  const rounded = Math.round(size * 10) / 10;

  return `${rounded} ${units[i]}`;
}

/**
 * Extracts file extension from filename
 */
export function getFileExtension(filename: string): string {
  if (!filename) return '';

  const parts = filename.split('.');
  
  // Handle files without extension or hidden files
  if (parts.length < 2 || (parts.length === 2 && parts[0] === '')) {
    return '';
  }

  return parts[parts.length - 1].toLowerCase();
}

/**
 * Validates file for document upload
 * Returns validation result with error message if invalid
 */
export function isValidDocumentFile(
  file: File
): { valid: boolean; error?: string } {
  // Check file size first (more critical error)
  if (!validateFileSize(file)) {
    return {
      valid: false,
      error: `File too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`,
    };
  }

  // Check file type
  if (!validateFileType(file)) {
    return {
      valid: false,
      error: `Invalid file type. Please upload ${ACCEPTED_FILE_TYPES.join(', ')} files.`,
    };
  }

  return { valid: true };
}

/**
 * Gets human-readable file type from extension
 */
export function getFileTypeName(filename: string): string {
  const extension = getFileExtension(filename);

  const typeMap: Record<string, string> = {
    pdf: 'PDF',
    txt: 'TXT',
    md: 'MD',
    docx: 'DOCX',
  };

  return typeMap[extension] || 'Unknown';
}

/**
 * Gets human-readable file type from MIME type
 */
export function getFileTypeNameFromMimeType(mimeType: string): string {
  const mimeMap: Record<string, string> = {
    'application/pdf': 'PDF',
    'text/plain': 'TXT',
    'text/markdown': 'MD',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
  };

  return mimeMap[mimeType] || 'Unknown';
}
