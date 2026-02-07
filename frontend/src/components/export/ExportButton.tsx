/**
 * Export Button Component
 *
 * Button to trigger CSV export with loading state and feedback
 */

import { Button } from "../ui/Button";
import { useExportStore } from "../../stores/exportStore";

export interface ExportButtonProps {
  className?: string;
  disabled?: boolean;
}

export function ExportButton({ className = "", disabled = false }: ExportButtonProps) {
  const { status, openOptionsModal } = useExportStore();
  const isLoading = status === "preparing" || status === "exporting";
  const isCompleted = status === "completed";

  const handleClick = () => {
    openOptionsModal();
  };

  return (
    <Button
      onClick={handleClick}
      disabled={disabled || isLoading}
      variant="default"
      size="default"
      className={className}
      dataTestId="export-button"
    >
      {isLoading ? (
        <>
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
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
          Exporting...
        </>
      ) : isCompleted ? (
        <>
          <svg
            className="mr-2 h-4 w-4 text-green-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          Export Complete
        </>
      ) : (
        <>
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Export CSV
        </>
      )}
    </Button>
  );
}
