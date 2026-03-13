/**
 * Knowledge Base Types
 *
 * Story 8-8: Frontend - Knowledge Base Page
 * Type definitions for knowledge base documents
 */

export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface KnowledgeDocument {
  id: number;
  filename: string;
  fileType: string;
  fileSize: number;
  status: DocumentStatus;
  errorMessage?: string;
  chunkCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentListResponse {
  documents: KnowledgeDocument[];
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  fileType: string;
  fileSize: number;
  status: DocumentStatus;
  createdAt: string;
}

export interface DocumentStatusResponse {
  status: DocumentStatus;
  progress: number;
  chunkCount: number;
  errorMessage?: string;
}
