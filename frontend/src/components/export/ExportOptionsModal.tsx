/**
 * Export Options Modal Component
 *
 * Modal for configuring export filters before generating CSV
 */

import * as React from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../ui/Dialog";
import { Button } from "../ui/Button";
import { useExportStore } from "../../stores/exportStore";
import type { ExportRequest } from "../../services/export";
import { useConversationStore } from "../../stores/conversationStore";

export function ExportOptionsModal() {
  const {
    isOptionsModalOpen,
    closeOptionsModal,
    setExportOptions,
    startExport,
  } = useExportStore();

  const { filters } = useConversationStore();

  // Local state for form options
  const [options, setOptions] = React.useState<ExportRequest>({});

  // Initialize options from current filters when modal opens
  React.useEffect(() => {
    if (isOptionsModalOpen) {
      const initialOptions: ExportRequest = {};

      if (filters.searchQuery) {
        initialOptions.search = filters.searchQuery;
      }
      if (filters.dateRange.from) {
        initialOptions.dateFrom = filters.dateRange.from;
      }
      if (filters.dateRange.to) {
        initialOptions.dateTo = filters.dateRange.to;
      }
      if (filters.statusFilters.length > 0) {
        initialOptions.status = filters.statusFilters;
      }
      if (filters.sentimentFilters.length > 0) {
        initialOptions.sentiment = filters.sentimentFilters;
      }
      if (filters.hasHandoffFilter !== null) {
        initialOptions.hasHandoff = filters.hasHandoffFilter;
      }

      setOptions(initialOptions);
    }
  }, [isOptionsModalOpen, filters]);

  const handleExport = () => {
    setExportOptions(options);
    closeOptionsModal();
    startExport();
  };

  const handleCancel = () => {
    closeOptionsModal();
  };

  const clearAllFilters = () => {
    setOptions({});
  };

  const hasActiveFilters = Object.keys(options).length > 0;

  return (
    <Dialog open={isOptionsModalOpen} onOpenChange={closeOptionsModal}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Export Conversations</DialogTitle>
          <DialogDescription>
            Configure filters to export specific conversations, or export all conversations.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Current Filters Summary */}
          <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-slate-700">
                {hasActiveFilters
                  ? `${Object.keys(options).length} filter(s) applied`
                  : "No filters - export all conversations"}
              </div>
              {hasActiveFilters && (
                <button
                  onClick={clearAllFilters}
                  className="text-xs text-blue-600 hover:text-blue-800"
                >
                  Clear all
                </button>
              )}
            </div>

            {hasActiveFilters && (
              <ul className="mt-2 space-y-1 text-xs text-slate-600">
                {options.search && (
                  <li>• Search: "{options.search}"</li>
                )}
                {options.dateFrom && options.dateTo && (
                  <li>• Date: {options.dateFrom} to {options.dateTo}</li>
                )}
                {options.dateFrom && !options.dateTo && (
                  <li>• From: {options.dateFrom}</li>
                )}
                {!options.dateFrom && options.dateTo && (
                  <li>• To: {options.dateTo}</li>
                )}
                {options.status && options.status.length > 0 && (
                  <li>• Status: {options.status.join(", ")}</li>
                )}
                {options.sentiment && options.sentiment.length > 0 && (
                  <li>• Sentiment: {options.sentiment.join(", ")}</li>
                )}
                {options.hasHandoff !== undefined && (
                  <li>• Handoff: {options.hasHandoff ? "Yes" : "No"}</li>
                )}
              </ul>
            )}
          </div>

          {/* Export Info */}
          <div className="rounded-md bg-blue-50 p-3">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong> Export is limited to 10,000 conversations. Apply filters to reduce the export size if needed.
            </p>
          </div>

          {/* Info about CSV format */}
          <div className="space-y-1">
            <p className="text-xs text-slate-600">
              The CSV file will include:
            </p>
            <ul className="ml-4 list-disc space-y-1 text-xs text-slate-600">
              <li>Conversation ID and masked Customer ID</li>
              <li>Dates, Status, and Sentiment</li>
              <li>Message count and order status</li>
              <li>LLM provider, tokens, and estimated cost</li>
              <li>Last message preview</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button onClick={handleExport}>
            Export CSV
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
