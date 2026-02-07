/**
 * Export Progress Component
 *
 * Displays export progress with status indicator and metadata
 */

import { Progress } from "../ui/Progress";
import { useExportStore } from "../../stores/exportStore";

export interface ExportProgressProps {
  className?: string;
}

export function ExportProgress({ className = "" }: ExportProgressProps) {
  const { status, progress, metadata, error } = useExportStore();

  // Don't render if idle
  if (status === "idle") {
    return null;
  }

  const getStatusMessage = () => {
    switch (status) {
      case "preparing":
        return "Preparing export...";
      case "exporting":
        return "Generating CSV file...";
      case "completed":
        return metadata
          ? `Export complete! ${metadata.exportCount} conversations exported.`
          : "Export complete!";
      case "error":
        return error || "Export failed. Please try again.";
      default:
        return "";
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "preparing":
      case "exporting":
        return "text-blue-600";
      case "completed":
        return "text-green-600";
      case "error":
        return "text-red-600";
      default:
        return "text-slate-700";
    }
  };

  return (
    <div className={`rounded-lg border border-slate-200 bg-white p-4 shadow-sm ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className={`text-sm font-medium ${getStatusColor()}`}>
            {getStatusMessage()}
          </p>
          {(status === "preparing" || status === "exporting") && (
            <div className="mt-2">
              <Progress value={progress} max={100} />
            </div>
          )}
          {status === "completed" && metadata && (
            <p className="mt-1 text-xs text-slate-500">
              File: {metadata.filename} • {new Date(metadata.exportDate).toLocaleString()}
            </p>
          )}
        </div>
        {status === "error" && (
          <button
            onClick={() => useExportStore.getState().clearError()}
            className="ml-4 rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Dismiss error"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
