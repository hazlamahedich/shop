/**
 * DocumentUploader Component
 * 
 * Mantis-themed drag-and-drop file upload with technical glass aesthetics.
 */

import * as React from 'react';
import { Upload, Cloud, FileCode2, ShieldAlert, Sparkles } from 'lucide-react';
import { isValidDocumentFile, ACCEPTED_FILE_TYPES } from '../../utils/fileValidation';

interface DocumentUploaderProps {
  onUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number;
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
    <div className="w-full space-y-4" role="status" aria-live="polite">
      <div
        data-testid="upload-zone"
        role="button"
        tabIndex={isUploading ? -1 : 0}
        aria-label="Upload files by dragging and dropping or clicking to browse"
        aria-disabled={isUploading}
        className={`
          relative group flex flex-col items-center justify-center py-20 px-10
          border-2 border-dashed rounded-[40px] cursor-pointer
          transition-all duration-700 overflow-hidden
          ${isDragOver 
            ? 'border-emerald-500 bg-emerald-500/[0.05] shadow-[0_0_80px_rgba(16,185,129,0.15)] scale-[1.01]' 
            : 'border-white/[0.05] bg-black/40 hover:border-emerald-500/30 hover:bg-emerald-500/[0.03]'}
          ${isUploading ? 'opacity-50 cursor-not-allowed border-emerald-500/20' : ''}
        `}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onKeyDown={handleKeyDown}
      >
        {/* Animated Background Gradients */}
        <div className={`absolute inset-0 bg-gradient-to-b from-emerald-500/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-1000 ${isDragOver ? 'opacity-100' : ''}`} />
        <div className="absolute top-0 left-1/4 w-1/2 h-px bg-gradient-to-r from-transparent via-emerald-500/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
        
        {isUploading ? (
          <div className="w-full max-w-sm relative z-10 space-y-8" data-testid="upload-progress">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <Cloud size={48} className="text-emerald-500 animate-pulse" />
                <div className="absolute inset-0 animate-ping rounded-full border-2 border-emerald-500/20" />
              </div>
              <p className="text-[11px] font-black text-emerald-400 tracking-[0.5em] uppercase text-center ml-[0.5em]">Neural Injection In Progress</p>
            </div>
            
            <div className="space-y-3">
              <div data-testid="progress-bar" className="h-1 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/[0.05]">
                <div 
                  className="h-full bg-emerald-500 transition-all duration-700 ease-out shadow-[0_0_20px_rgba(16,185,129,0.8)] relative"
                  style={{ width: `${uploadProgress}%` }}
                >
                  <div className="absolute top-0 right-0 w-8 h-full bg-white/20 blur-sm animate-pulse" />
                </div>
              </div>
              <div className="flex justify-between items-center px-1">
                <span className="text-[9px] font-black text-emerald-900/40 uppercase tracking-widest">Protocol: Uplink</span>
                <span className="text-[10px] font-mono font-black text-emerald-400">{uploadProgress}%</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col items-center">
            <div 
              data-testid="upload-icon" 
              className="mb-8 w-20 h-20 rounded-[32px] bg-white/[0.03] border border-white/[0.05] flex items-center justify-center text-emerald-900/20 group-hover:text-emerald-400 group-hover:bg-emerald-500/5 group-hover:border-emerald-500/20 group-hover:shadow-[0_0_40px_rgba(16,185,129,0.1)] group-hover:-translate-y-2 group-hover:rotate-[5deg] transition-all duration-700"
            >
              <Upload size={32} />
            </div>
            
            <div className="text-center space-y-3">
              <h4 className="text-xl font-black text-white tracking-tight uppercase group-hover:mantis-glow-text transition-all duration-700">
                Supply Neural Fragments
              </h4>
              <p className="text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em] group-hover:text-emerald-900/60 transition-colors">
                Drag drop corpus or <span className="text-emerald-400 underline underline-offset-4 decoration-emerald-500/30">browse protocols</span>
              </p>
            </div>

            <div className="mt-12 flex items-center gap-6">
              <div className="flex items-center gap-3">
                {ACCEPTED_FILE_TYPES.map(type => (
                  <div key={type} className="flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.02] border border-white/[0.05] rounded-xl text-emerald-900/30 group-hover:text-emerald-900/50 group-hover:border-white/[0.1] transition-all duration-500">
                    <FileCode2 size={10} />
                    <span className="text-[9px] font-black uppercase tracking-tighter">
                      {type.replace('.', '')}
                    </span>
                  </div>
                ))}
              </div>
              <div className="h-4 w-px bg-white/[0.05]" />
              <div className="flex items-center gap-2 text-[9px] font-black text-emerald-500/40 uppercase tracking-[0.2em]">
                <Sparkles size={10} />
                <span>Limit: 10MB</span>
              </div>
            </div>
          </div>
        )}

        <input
          ref={fileInputRef}
          data-testid="file-input"
          type="file"
          accept={acceptString}
          onChange={handleInputChange}
          className="hidden"
          disabled={isUploading}
        />
      </div>

      {error && (
        <div 
          role="alert" 
          className="p-6 bg-red-500/[0.03] border border-red-500/10 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-500 flex items-center justify-between"
        >
          <div className="flex items-center gap-4">
            <div className="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20">
              <ShieldAlert size={16} />
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black text-red-500 uppercase tracking-[0.2em]">Protocol Violation</p>
              <p className="text-xs font-bold text-red-400/80 tracking-tight italic">{error}</p>
            </div>
          </div>
          <button 
            onClick={() => setError(null)}
            className="text-[9px] font-black text-red-500/40 uppercase tracking-widest hover:text-red-500 transition-colors"
          >
            Acknowledge
          </button>
        </div>
      )}
    </div>
  );
}
