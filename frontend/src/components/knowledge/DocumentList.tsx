/**
 * DocumentList Component
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Displays list of uploaded documents with status indicators
 */

import * as React from 'react';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/Dialog';
import type { KnowledgeDocument, DocumentStatus } from '../../types/knowledgeBase';
import { formatFileSize, getFileTypeNameFromMimeType } from '../../utils/fileValidation';

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
  if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes === 1 ? '' : 's'} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
  
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

function SpinnerIcon() {
  return (
    <svg
      className="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
      role="img"
    >
      <title>Processing</title>
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
      role="img"
    >
      <title>Delete</title>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
      />
    </svg>
  );
}

function RetryIcon() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
      role="img"
    >
      <title>Retry</title>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
      role="img"
    >
      <title>Ready</title>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
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
        className="flex flex-col items-center justify-center py-12 text-center"
      >
        <div className="mb-4 rounded-full bg-slate-100 p-4">
          <svg
            className="h-8 w-8 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-slate-900">No documents uploaded yet</h3>
        <p className="mt-1 text-sm text-slate-500">
          Upload your first document to start building your knowledge base.
        </p>
      </div>
    );
  }

  return (
    <>
      <div data-testid="document-list" className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Type</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Size</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Uploaded</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.map((doc) => (
              <tr
                key={doc.id}
                data-testid={`document-row-${doc.id}`}
                className="border-b border-slate-100 hover:bg-slate-50"
              >
                <td className="px-4 py-3">
                  <span className="text-sm font-medium text-slate-900 truncate max-w-xs block">
                    {doc.filename}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-slate-600">{getFileTypeNameFromMimeType(doc.fileType)}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-slate-600">{formatFileSize(doc.fileSize)}</span>
                </td>
                <td 
                  className="px-4 py-3" 
                  data-testid={`document-status-${doc.id}`}
                  role="status"
                  aria-live="polite"
                >
                  <div className="flex items-center gap-2">
                    {doc.status === 'processing' && (
                      <span data-testid={`spinner-${doc.id}`}>
                        <SpinnerIcon />
                      </span>
                    )}
                    {doc.status === 'ready' && (
                      <span className="text-green-500" aria-hidden="true">
                        <CheckIcon />
                      </span>
                    )}
                    <Badge
                      data-testid={`status-badge-${doc.id}`}
                      variant={getStatusBadgeVariant(doc.status)}
                      aria-label={`Status: ${doc.status}`}
                      className={`
                        ${doc.status === 'pending' ? 'bg-gray-100 text-gray-800 border-gray-200' : ''}
                      `}
                    >
                      {doc.status}
                    </Badge>
                  </div>
                  {doc.status === 'error' && doc.errorMessage && (
                    <p className="mt-1 text-xs text-red-600" role="alert">
                      {doc.errorMessage}
                    </p>
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-sm text-slate-600">
                    {formatRelativeTime(doc.createdAt)}
                  </span>
                </td>
                <td className="px-4 py-3" data-testid={`document-actions-${doc.id}`}>
                  <div className="flex items-center gap-2">
                    {doc.status === 'error' && (
                      <Button
                        data-testid={`retry-document-${doc.id}`}
                        variant="ghost"
                        size="sm"
                        onClick={() => onRetry(doc.id)}
                        aria-label={`Retry ${doc.filename}`}
                      >
                        <RetryIcon />
                      </Button>
                    )}
                    <Button
                      data-testid={`delete-document-${doc.id}`}
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteClick(doc)}
                      aria-label={`Delete ${doc.filename}`}
                    >
                      <DeleteIcon />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-description"
        >
          <DialogHeader>
            <DialogTitle id="delete-dialog-title">Delete Document</DialogTitle>
            <DialogDescription id="delete-dialog-description">
              Are you sure you want to delete <strong>{documentToDelete?.filename}</strong>? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4">
            <button
              type="button"
              className="inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 disabled:pointer-events-none disabled:opacity-50 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 h-10 px-4 py-2"
              onClick={handleCancelDelete}
            >
              Cancel
            </button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
