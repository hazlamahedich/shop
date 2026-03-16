/**
 * Knowledge Base Page
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Allows merchants to upload and manage documents for the knowledge base
 *
 * ATDD Checklist:
 * [x] AC1: Documents list displays with status indicators
 * [x] AC2: File upload accepts PDF/TXT/MD/DOCX up to 10MB
 * [x] AC3: Delete with confirmation removes document
 * [x] AC4: Processing documents show spinner/progress
 * [x] AC5: Error documents show error message + retry
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../context/ToastContext';
import { DocumentList } from '../components/knowledge/DocumentList';
import { DocumentUploader } from '../components/knowledge/DocumentUploader';
import { knowledgeBaseApi } from '../services/knowledgeBase';
import type { KnowledgeDocument } from '../types/knowledgeBase';

const KnowledgeBasePage: React.FC = () => {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const merchant = useAuthStore((state) => state.merchant);
  const { toast } = useToast();

  const isGeneralMode = merchant?.onboardingMode === 'general';

  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const docs = await knowledgeBaseApi.getDocuments();
      setDocuments(docs);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load documents';
      setError(message);
      toast(message, 'error');
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (isGeneralMode) {
      fetchDocuments();
    }
  }, [isGeneralMode, fetchDocuments]);

  const handleUpload = async (file: File) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);

      const newDoc = await knowledgeBaseApi.uploadDocument(file, (progress) => {
        setUploadProgress(progress);
      });

      setDocuments((prev) => [...prev, { ...newDoc, chunkCount: 0, updatedAt: newDoc.createdAt }]);
      toast(`${file.name} uploaded successfully`, 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to upload document';
      toast(message, 'error');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDelete = async (documentId: number) => {
    try {
      await knowledgeBaseApi.deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
      toast('Document deleted successfully', 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete document';
      toast(message, 'error');
    }
  };

  const handleRetry = async (documentId: number) => {
    try {
      await knowledgeBaseApi.reprocessDocument(documentId);
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === documentId
            ? { ...doc, status: 'processing' as const, errorMessage: undefined }
            : doc
        )
      );
      toast('Document reprocessing started', 'success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reprocess document';
      toast(message, 'error');
    }
  };

  if (!isGeneralMode) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="text-center max-w-md">
          <div className="mb-4 rounded-full bg-slate-100 p-4 inline-flex">
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
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2">
            Knowledge Base Unavailable
          </h2>
          <p className="text-slate-600">
            The knowledge base feature is only available in General mode.
            Switch to General mode in Settings to access this feature.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Knowledge Base</h1>
        <p className="mt-2 text-sm text-gray-600">
          Upload documents to train your bot with custom knowledge. Supported formats: PDF, TXT, MD, DOCX (max 10MB).
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Document</h2>
        <DocumentUploader
          onUpload={handleUpload}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
        />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Documents</h2>
        {isLoading ? (
          <div className="flex items-center justify-center py-12" role="status">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <span className="sr-only">Loading documents...</span>
          </div>
        ) : error ? (
          <div className="text-center py-12 text-red-600">
            <p>{error}</p>
            <button
              onClick={fetchDocuments}
              className="mt-4 text-blue-600 hover:underline"
            >
              Try again
            </button>
          </div>
        ) : (
          <DocumentList
            documents={documents}
            onDelete={handleDelete}
            onRetry={handleRetry}
          />
        )}
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
