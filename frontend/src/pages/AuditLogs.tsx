import React from 'react';
import { FileText } from 'lucide-react';
import { AuditLogViewer } from '../components/retention/AuditLogViewer';

const AuditLogs: React.FC = () => {
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
              <span className="text-emerald-400 mantis-glow-text">System Audit Logs</span>
            </li>
          </ol>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-10 py-16 space-y-16">
        {/* Page Header */}
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 blur-3xl opacity-20 -z-10" />
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-8">
            <div className="space-y-4">
              <h1 className="text-6xl font-black tracking-tight text-white mantis-glow-text leading-none">
                Compliance Audit
              </h1>
              <p className="text-xl text-emerald-900/60 font-medium max-w-2xl leading-relaxed">
                Track data deletion activities and system-level events for GDPR/CCPA compliance and security transparency.
              </p>
            </div>
            <div className="flex items-center gap-3 px-6 py-2.5 bg-emerald-500/5 text-emerald-400 border border-emerald-500/10 rounded-2xl text-[10px] font-black uppercase tracking-[0.3em] backdrop-blur-md shadow-2xl">
              <FileText size={14} className="text-emerald-500 shadow-glow" />
              <span>Retention Protocol Active</span>
            </div>
          </div>
        </div>

        <AuditLogViewer />
      </main>
    </div>
  );
};

export default AuditLogs;

