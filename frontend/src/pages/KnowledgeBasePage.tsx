import React, { useState, useEffect, useCallback } from 'react';
import { RefreshCw, ShieldAlert, Database, Plus, Library } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../context/ToastContext';
import { DocumentList } from '../components/knowledge/DocumentList';
import { DocumentUploader } from '../components/knowledge/DocumentUploader';
import { knowledgeBaseApi } from '../services/knowledgeBase';
import type { KnowledgeDocument } from '../types/knowledgeBase';
import { GlassCard } from '../components/ui/GlassCard';

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

  return (
    <div className="min-h-screen bg-[#050505] text-emerald-50">
      {/* Breadcrumb Navigation */}
      <nav className="border-b border-emerald-500/10 bg-black/20 backdrop-blur-xl" aria-label="Breadcrumb">
        <div className="max-w-7xl mx-auto px-10 py-4">
          <ol className="flex items-center gap-3 text-[11px] font-black uppercase tracking-[0.2em]">
            <li>
              <a href="/dashboard" className="text-emerald-900/40 hover:text-emerald-400 transition-all duration-500">
                Primary Dashboard
              </a>
            </li>
            <li className="text-emerald-900/20">/</li>
            <li>
              <span className="text-emerald-400 mantis-glow-text">Knowledge Engine</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-10 py-16 space-y-16">
        {!isGeneralMode ? (
          <div className="flex flex-col items-center justify-center py-20 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            <GlassCard accent="mantis" className="text-center max-w-2xl p-16 border-red-500/20 bg-red-500/[0.02]">
              <div className="mb-10 rounded-[32px] bg-red-500/10 p-10 inline-flex border border-red-500/20 shadow-[0_0_40px_rgba(239,68,68,0.15)]">
                <ShieldAlert size={48} className="text-red-500 shadow-glow" />
              </div>
              <h2 className="text-5xl font-black text-white mb-6 tracking-tight mantis-glow-text leading-none">
                Labyrinth Restricted
              </h2>
              <p className="text-xl text-emerald-900/60 leading-relaxed font-medium mb-10 max-w-lg mx-auto">
                The Knowledge Base requires <span className="text-emerald-400 font-black tracking-widest uppercase text-sm ml-1">General Mode</span> authorization.
                Switch your core protocol in <a href="/settings" className="text-emerald-400 hover:text-emerald-300 underline underline-offset-4 decoration-emerald-500/30 font-bold transition-all">Settings</a> to begin neural training.
              </p>
              <div className="pt-8 border-t border-red-500/10 flex justify-center gap-4">
                <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-red-500/60 bg-red-500/5 px-4 py-2 rounded-xl">
                  Protocol: Restricted
                </span>
              </div>
            </GlassCard>
          </div>
        ) : (
          <>
            {/* Page Header */}
            <div className="relative group">
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 blur-3xl opacity-20 -z-10" />
              <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
                <div className="space-y-4">
                  <h1 className="text-6xl font-black tracking-tight text-white mantis-glow-text leading-none">
                    Knowledge Base
                  </h1>
                  <p className="text-xl text-emerald-900/60 font-medium max-w-2xl leading-relaxed">
                    Train your autonomous agent with specialized expertise. Inject technical manuals, protocols, or FAQ schematics to enhance neural resonance.
                  </p>
                </div>
                <div className="flex items-center gap-3 px-6 py-2.5 bg-emerald-500/5 text-emerald-400 border border-emerald-500/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] backdrop-blur-md shadow-2xl">
                  <Database size={14} className="text-emerald-500 shadow-glow" />
                  <span>Neural Core Active</span>
                </div>
              </div>
            </div>

            {/* Document Intake Section */}
            <div className="space-y-8">
              <div className="flex items-center gap-4 px-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                  <Plus size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-black uppercase tracking-[0.3em] text-emerald-400 mb-0.5">Document Intake</h3>
                  <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-900/40">Inject raw data into the LLM context</p>
                </div>
              </div>
              
              <GlassCard accent="mantis" className="p-8 border-emerald-500/10 bg-emerald-500/[0.02]">
                <DocumentUploader
                  onUpload={handleUpload}
                  isUploading={isUploading}
                  uploadProgress={uploadProgress}
                />
              </GlassCard>
            </div>

            {/* Corpus Library Section */}
            <div className="space-y-8">
              <div className="flex items-center justify-between px-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                    <Library size={20} />
                  </div>
                  <div>
                    <h3 className="text-sm font-black uppercase tracking-[0.3em] text-emerald-400 mb-0.5">Corpus Library</h3>
                    <p className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-900/40">Manage indexed document fragments</p>
                  </div>
                </div>
                <button
                  onClick={fetchDocuments}
                  className="p-2.5 bg-white/5 border border-white/10 text-emerald-900/60 rounded-xl hover:bg-white/10 hover:text-emerald-400 transition-all duration-500 group"
                  title="Reload Indices"
                >
                  <RefreshCw size={16} className={isLoading ? 'animate-spin text-emerald-400' : 'group-hover:rotate-180 transition-transform duration-700'} />
                </button>
              </div>

              <GlassCard className="p-0 overflow-hidden border-emerald-500/10 bg-emerald-500/[0.01]">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-32 gap-6" role="status">
                    <div className="relative">
                      <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-emerald-500 shadow-[0_0_30px_rgba(16,185,129,0.3)]" />
                      <div className="absolute inset-0 animate-ping rounded-full h-16 w-16 border border-emerald-500/20" />
                    </div>
                    <div className="text-center">
                      <span className="text-emerald-900/40 font-black uppercase tracking-[0.4em] text-[11px] block animate-pulse">Scanning Neural Paths</span>
                      <span className="text-[9px] font-black text-emerald-900/20 uppercase tracking-widest mt-2 block">Loading Dataset Fragments...</span>
                    </div>
                  </div>
                ) : error ? (
                  <div className="text-center py-32">
                    <div className="p-10 bg-red-500/5 border border-red-500/10 rounded-[40px] inline-block backdrop-blur-3xl relative overflow-hidden group">
                      <div className="absolute inset-0 bg-red-500/[0.02] -z-10 group-hover:scale-110 transition-transform duration-1000" />
                      <div className="mb-6 rounded-2xl bg-red-500/10 p-5 inline-flex border border-red-500/20 shadow-glow">
                        <ShieldAlert size={24} className="text-red-500" />
                      </div>
                      <p className="text-[11px] font-black text-red-500/60 uppercase tracking-[0.3em] mb-4">Fragment Access Failure</p>
                      <p className="text-red-200/60 font-medium max-w-sm mb-8 leading-relaxed italic">&quot;{error}&quot;</p>
                      <button
                        onClick={fetchDocuments}
                        className="h-12 px-8 bg-red-500 text-black rounded-2xl flex items-center gap-3 transition-all duration-500 hover:bg-red-400 font-black text-[10px] uppercase tracking-[0.3em] shadow-[0_0_30px_rgba(239,68,68,0.2)] mx-auto"
                      >
                        <RefreshCw size={14} />
                        Re-initialize Sync
                      </button>
                    </div>
                  </div>
                ) : (
                  <DocumentList
                    documents={documents}
                    onDelete={handleDelete}
                    onRetry={handleRetry}
                  />
                )}
              </GlassCard>
            </div>
          </>
        )}
      </main>
    </div>
  );
};

export default KnowledgeBasePage;
