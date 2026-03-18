/**
 * DocumentList Component
 * 
 * Redesigned for Mantis theme with glassmorphism and emerald accents.
 */

import * as React from 'react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/Dialog';
import type { KnowledgeDocument, DocumentStatus } from '../../types/knowledgeBase';
import { formatFileSize, getFileTypeNameFromMimeType } from '../../utils/fileValidation';
import { FileText, Trash2, RefreshCcw, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

interface DocumentListProps {
  documents: KnowledgeDocument[];
  onDelete: (id: number) => void;
  onRetry: (id: number) => void;
  onPollStatus?: (id: number) => void;
}

function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) return 'Just now';
  if (diffMinutes < 60) return `${diffMinutes}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  
  return date.toLocaleDateString();
}

function getStatusBadgeVariant(status: DocumentStatus): 'default' | 'success' | 'warning' | 'destructive' {
  switch (status) {
    case 'ready':
      return 'success';
    case 'processing':
      return 'warning';
    case 'error':
      return 'destructive';
    default:
      return 'default';
  }
}

export function DocumentList({ documents, onDelete, onRetry }: DocumentListProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = React.useState(false);
  const [documentToDelete, setDocumentToDelete] = React.useState<KnowledgeDocument | null>(null);

  const handleDeleteClick = (doc: KnowledgeDocument) => {
    setDocumentToDelete(doc);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = () => {
    if (documentToDelete) {
      onDelete(documentToDelete.id);
    }
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setDocumentToDelete(null);
  };

  if (documents.length === 0) {
    return (
      <div
        data-testid="empty-state"
        role="status"
        className="flex flex-col items-center justify-center py-24 text-center animate-in fade-in duration-700"
      >
        <div className="mb-8 rounded-[32px] bg-emerald-500/5 p-8 border border-emerald-500/10 shadow-[0_0_40px_rgba(16,185,129,0.05)] relative group overflow-hidden">
          <div className="absolute inset-0 bg-emerald-500/[0.02] group-hover:scale-150 transition-transform duration-1000" />
          <FileText className="h-12 w-12 text-emerald-500/40 relative z-10" />
        </div>
        <h3 className="text-xl font-black text-white tracking-tight uppercase mb-3">Void Archive</h3>
        <p className="text-emerald-900/40 max-w-xs font-bold text-xs uppercase tracking-widest leading-loose">
          Terminal indicates zero data fragments. Initiate document intake to begin training.
        </p>
      </div>
    );
  }

  return (
    <>
      <div data-testid="document-list" className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-white/[0.03]">
              <th className="px-8 py-6 text-left text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Signature</th>
              <th className="px-8 py-6 text-left text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Protocol</th>
              <th className="px-8 py-6 text-left text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Payload</th>
              <th className="px-8 py-6 text-left text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Status</th>
              <th className="px-8 py-6 text-left text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Injection</th>
              <th className="px-8 py-6 text-right text-[10px] font-black text-emerald-900/40 uppercase tracking-[0.3em]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.02]">
            {documents.map((doc) => (
              <tr
                key={doc.id}
                data-testid={`document-row-${doc.id}`}
                className="group hover:bg-emerald-500/[0.02] transition-all duration-500"
              >
                <td className="px-8 py-6">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-white/[0.03] border border-white/[0.05] flex items-center justify-center text-emerald-900/40 group-hover:text-emerald-400 group-hover:border-emerald-500/20 group-hover:bg-emerald-500/5 transition-all duration-500">
                      <FileText size={18} />
                    </div>
                    <span className="text-sm font-bold text-white/90 group-hover:text-emerald-400 transition-colors truncate max-w-[240px]">
                      {doc.filename}
                    </span>
                  </div>
                </td>
                <td className="px-8 py-6">
                  <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-900/40 group-hover:text-emerald-900/60 transition-colors">
                    {getFileTypeNameFromMimeType(doc.fileType)}
                  </span>
                </td>
                <td className="px-8 py-6">
                  <span className="text-[10px] font-black text-emerald-900/30 group-hover:text-emerald-900/50 transition-colors uppercase tracking-[0.1em]">
                    {formatFileSize(doc.fileSize)}
                  </span>
                </td>
                <td 
                  className="px-8 py-6" 
                  data-testid={`document-status-${doc.id}`}
                  role="status"
                  aria-live="polite"
                >
                  <div className="flex items-center gap-3">
                    {doc.status === 'processing' && (
                      <div className="relative flex items-center justify-center">
                        <RefreshCcw size={14} className="text-amber-500 animate-spin" />
                        <div className="absolute inset-0 animate-ping rounded-full border border-amber-500/20" />
                      </div>
                    )}
                    {doc.status === 'ready' && (
                      <CheckCircle2 size={14} className="text-emerald-500 shadow-glow" />
                    )}
                    {doc.status === 'error' && (
                      <AlertCircle size={14} className="text-red-500 shadow-glow" />
                    )}
                    <Badge
                      data-testid={`status-badge-${doc.id}`}
                      variant={getStatusBadgeVariant(doc.status)}
                      className={`
                        font-black uppercase tracking-[0.25em] text-[8px] px-2.5 py-1 rounded-lg border backdrop-blur-md
                        ${doc.status === 'ready' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : ''}
                        ${doc.status === 'processing' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20 shadow-[0_0_15px_rgba(245,158,11,0.1)]' : ''}
                        ${doc.status === 'error' ? 'bg-red-500/10 text-red-400 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : ''}
                        ${doc.status === 'pending' ? 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20' : ''}
                      `}
                    >
                      {doc.status}
                    </Badge>
                  </div>
                  {doc.status === 'error' && doc.errorMessage && (
                    <p className="mt-2 text-[9px] font-bold text-red-400/60 leading-tight uppercase tracking-widest max-w-[200px]" role="alert">
                      {doc.errorMessage}
                    </p>
                  )}
                </td>
                <td className="px-8 py-6">
                  <div className="flex items-center gap-2 text-emerald-900/40 group-hover:text-emerald-900/60 transition-colors">
                    <Clock size={12} />
                    <span className="text-[10px] font-black uppercase tracking-[0.1em]">
                      {formatRelativeTime(doc.createdAt)}
                    </span>
                  </div>
                </td>
                <td className="px-8 py-6 text-right" data-testid={`document-actions-${doc.id}`}>
                  <div className="flex items-center justify-end gap-2 text-emerald-900/20 transition-all duration-500 opacity-0 group-hover:opacity-100 transform translate-x-4 group-hover:translate-x-0">
                    {doc.status === 'error' && (
                      <button
                        onClick={() => onRetry(doc.id)}
                        className="p-2 bg-emerald-500/5 hover:bg-emerald-500/20 border border-emerald-500/10 text-emerald-400 rounded-xl transition-all duration-300"
                        title="Retry Reprocessing"
                      >
                        <RefreshCcw size={14} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteClick(doc)}
                      className="p-2 bg-red-500/5 hover:bg-red-500/20 border border-red-500/10 text-red-500 rounded-xl transition-all duration-300"
                      title="Decommission Document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent
          className="bg-[#080808] border border-white/[0.05] shadow-[0_0_100px_rgba(0,0,0,0.8)] p-10 max-w-lg rounded-[40px] overflow-hidden backdrop-blur-3xl"
          role="alertdialog"
        >
          <div className="absolute inset-0 bg-gradient-to-b from-red-500/[0.03] to-transparent pointer-events-none" />
          <DialogHeader className="relative z-10 space-y-6">
            <div className="w-16 h-16 rounded-[24px] bg-red-500/10 flex items-center justify-center text-red-500 border border-red-500/20 mb-2 mx-auto">
              <Trash2 size={32} />
            </div>
            <DialogTitle className="text-3xl font-black text-white text-center leading-none tracking-tight">Decommission Fragment?</DialogTitle>
            <DialogDescription className="text-emerald-900/60 font-medium text-center text-lg leading-relaxed">
              Confirm erasure of <span className="text-white font-black italic">&quot;{documentToDelete?.filename}&quot;</span> from the neural core. This operation is irreversible.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="relative z-10 mt-12 grid grid-cols-2 gap-4">
            <button
              onClick={handleCancelDelete}
              className="h-14 px-8 rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-[0.3em] hover:bg-white/10 transition-all duration-500"
            >
              Abort
            </button>
            <button
              onClick={handleConfirmDelete}
              className="h-14 px-8 rounded-2xl bg-red-600 text-white font-black text-[10px] uppercase tracking-[0.3em] hover:bg-red-500 transition-all duration-500 shadow-[0_0_30px_rgba(220,38,38,0.2)]"
            >
              Finalize Erasure
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
