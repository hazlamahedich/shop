/** ConfidenceIndicator component.
 *
 * Story 1.13: Bot Preview Mode
 *
 * Displays a visual confidence indicator for bot responses.
 * Shows confidence score with color coding and explanation.
 */

import * as React from 'react';

export interface ConfidenceIndicatorProps {
  /** Confidence score (0-100) */
  confidence: number;
  /** Confidence level label */
  confidenceLevel: 'high' | 'medium' | 'low';
  /** Optional className for styling */
  className?: string;
  /** Whether to show detailed technical info */
  showDetails?: boolean;
  /** Optional metadata about the response */
  metadata?: {
    intent: string;
    faqMatched: boolean;
    productsFound: number;
    llmProvider: string;
  };
}

/**
 * Get color class based on confidence level
 */
function getConfidenceColor(level: 'high' | 'medium' | 'low'): string {
  switch (level) {
    case 'high':
      return 'bg-green-500';
    case 'medium':
      return 'bg-yellow-500';
    case 'low':
      return 'bg-red-500';
  }
}

/**
 * Get text color class based on confidence level
 */
function getConfidenceTextColor(level: 'high' | 'medium' | 'low'): string {
  switch (level) {
    case 'high':
      return 'text-green-700';
    case 'medium':
      return 'text-yellow-700';
    case 'low':
      return 'text-red-700';
  }
}

/**
 * Get explanation text for low confidence
 */
function getConfidenceExplanation(level: 'high' | 'medium' | 'low'): string | null {
  if (level === 'low') {
    return 'Low confidence - Consider adding an FAQ entry for this question.';
  }
  if (level === 'medium') {
    return 'Medium confidence - Bot response may vary.';
  }
  return null;
}

export function ConfidenceIndicator({
  confidence,
  confidenceLevel,
  className = '',
  showDetails = false,
  metadata,
}: ConfidenceIndicatorProps) {
  const barColor = getConfidenceColor(confidenceLevel);
  const textColor = getConfidenceTextColor(confidenceLevel);
  const explanation = getConfidenceExplanation(confidenceLevel);
  const barWidth = `${Math.max(0, Math.min(100, confidence))}%`;

  return (
    <div className={`confidence-indicator ${className}`} data-testid="confidence-indicator">
      <div className="flex items-center gap-2 text-sm">
        <span className="font-medium text-gray-700">Confidence:</span>
        <span
          className={`font-bold ${textColor}`}
          aria-label={`Confidence level: ${confidenceLevel}, score: ${confidence}%`}
        >
          {confidence}%
        </span>
        <span className={`text-xs px-2 py-0.5 rounded ${textColor} bg-opacity-20 ${barColor} bg-opacity-10`}>
          {confidenceLevel.charAt(0).toUpperCase() + confidenceLevel.slice(1)}
        </span>
      </div>

      {/* Confidence bar */}
      <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden" role="progressbar" aria-valuenow={confidence} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`h-full ${barColor} transition-all duration-300 ease-out`}
          style={{ width: barWidth }}
        />
      </div>

      {/* Explanation for low/medium confidence */}
      {explanation && (
        <p className={`mt-1 text-xs ${textColor}`}>
          {explanation}
        </p>
      )}

      {/* Technical details (optional) */}
      {showDetails && metadata && (
        <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
          <div className="grid grid-cols-2 gap-1">
            <span className="font-medium">Intent:</span>
            <span>{metadata.intent}</span>
            <span className="font-medium">FAQ Match:</span>
            <span>{metadata.faqMatched ? 'Yes' : 'No'}</span>
            <span className="font-medium">Products:</span>
            <span>{metadata.productsFound}</span>
            <span className="font-medium">Provider:</span>
            <span>{metadata.llmProvider}</span>
          </div>
        </div>
      )}
    </div>
  );
}
