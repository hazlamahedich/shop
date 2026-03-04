/**
 * Export button component for merchant data export.
 * Story 6-3: Merchant CSV Export
 * 
 * Provides a button to trigger complete merchant data export (GDPR compliance).
 */

import { useDataExport } from '../hooks/useDataExport';

interface ExportButtonProps {
  merchantId: number;
  className?: string;
}

export function ExportButton({ merchantId, className = '' }: ExportButtonProps) {
  const { exportData, isExporting, error } = useDataExport(merchantId);

  return (
    <div className="export-button-container">
      <button
        onClick={exportData}
        disabled={isExporting}
        className={`export-button ${className}`}
        aria-label="Export all merchant data"
      >
        {isExporting ? (
          <>
            <span className="spinner" aria-hidden="true"></span>
            Exporting...
          </>
        ) : (
          <>
            <svg
              className="download-icon"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
            Export All Data
          </>
        )}
      </button>

      {error && (
        <div className="export-error" role="alert">
          {error}
        </div>
      )}

      <style>{`
        .export-button-container {
          display: inline-block;
        }

        .export-button {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          font-size: 1rem;
          font-weight: 500;
          color: white;
          background-color: #3b82f6;
          border: none;
          border-radius: 0.5rem;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .export-button:hover:not(:disabled) {
          background-color: #2563eb;
        }

        .export-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .download-icon {
          width: 1.25rem;
          height: 1.25rem;
        }

        .spinner {
          display: inline-block;
          width: 1rem;
          height: 1rem;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .export-error {
          margin-top: 0.5rem;
          padding: 0.75rem;
          font-size: 0.875rem;
          color: #dc2626;
          background-color: #fef2f2;
          border: 1px solid #fecaca;
          border-radius: 0.5rem;
        }
      `}</style>
    </div>
  );
}
