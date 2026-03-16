/**
 * DocumentUploader Component
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Drag-and-drop file upload component with validation
 */

import * as React from 'react';
import { Progress } from '../ui/Progress';
import { isValidDocumentFile, ACCEPTED_FILE_TYPES } from '../../utils/fileValidation';

interface DocumentUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number;
}

function UploadIcon() {
  return (
    <svg
      className="h-12 w-12 text-slate-400"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
      />
    </svg>
  );
}

export function DocumentUploader({ onUpload, isUploading, uploadProgress }: DocumentUploaderProps) {
  const [isDragOver, setIsDragOver] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileValidation = (file: File): boolean => {
    const validation = isValidDocumentFile(file);
    if (!validation.valid) {
      setError(validation.error || 'Invalid file');
      return false;
    }
    setError(null);
    return true;
  };

  const handleFileSelect = (file: File) => {
    if (isUploading) return;
    if (handleFileValidation(file)) {
      onUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (isUploading) return;
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (isUploading) return;
    
    const files = e.dataTransfer?.files;
    if (files && files.length > 0 && e.dataTransfer.types.includes('Files')) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    if (isUploading) return;
    fileInputRef.current?.click();
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
    e.target.value = '';
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (isUploading) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fileInputRef.current?.click();
    }
  };

  const acceptString = ACCEPTED_FILE_TYPES.join(',');

  return (
    <div className="w-full" role="status" aria-live="polite">
      <div
        data-testid="upload-zone"
        role="button"
        tabIndex={isUploading ? -1 : 0}
        aria-label="Upload files by dragging and dropping or clicking to browse"
        aria-disabled={isUploading}
        className={`
          relative flex flex-col items-center justify-center p-8
          border-2 border-dashed rounded-lg cursor-pointer
          transition-colors duration-200
          ${isDragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-slate-400'}
          ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
        aria-dropeffect={isDragOver ? 'copy' : 'none'}
      >
        {isUploading ? (
          <div className="w-full" data-testid="upload-progress">
            <p className="text-sm text-slate-600 mb-2 text-center">Uploading...</p>
            <div data-testid="progress-bar">
              <Progress 
                value={uploadProgress} 
                role="progressbar" 
                aria-valuenow={uploadProgress} 
                aria-valuemin={0} 
                aria-valuemax={100}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1 text-center">{uploadProgress}%</p>
          </div>
        ) : (
          <>
            <div data-testid="upload-icon">
              <UploadIcon />
            </div>
            <p className="mt-4 text-sm text-slate-600">
              <span className="font-medium">Drag and drop files here</span>
            </p>
            <p className="mt-1 text-sm text-slate-500">or click to browse</p>
            <p className="mt-2 text-xs text-slate-400">
              {ACCEPTED_FILE_TYPES.join(', ').replace(/\./g, '').toUpperCase()} • Max 10MB
            </p>
          </>
        )}

        <input
          ref={fileInputRef}
          data-testid="file-input"
          type="file"
          accept={acceptString}
          onChange={handleInputChange}
          aria-label="File upload"
          className="hidden"
          disabled={isUploading}
        />
      </div>

      {error && (
        <div role="alert" className="mt-2 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}
    </div>
  );
}
