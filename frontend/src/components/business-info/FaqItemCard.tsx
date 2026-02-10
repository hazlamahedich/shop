/**
 * FaqItemCard Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Displays a single FAQ item in the FAQ list with:
 * - Question (truncated at 50 chars if needed)
 * - Answer preview
 * - Keywords display (if provided)
 * - Edit and Delete action buttons
 * - Drag handle for reordering
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { Edit2, Trash2, GripVertical, Tag } from 'lucide-react';
import type { FaqItem } from '../../stores/businessInfoStore';

export interface FaqItemCardProps {
  /** The FAQ item to display */
  faq: FaqItem;
  /** Callback when edit button is clicked */
  onEdit: (faq: FaqItem) => void;
  /** Callback when delete button is clicked */
  onDelete: (faq: FaqItem) => void;
  /** Whether actions are disabled (during delete operations) */
  disabled?: boolean;
  /** Whether this card is being dragged */
  isDragging?: boolean;
}

/**
 * Truncate text to a maximum length and add ellipsis
 */
function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * FaqItemCard Component
 *
 * A card displaying an FAQ item with:
 * - Question text
 * - Answer preview (truncated)
 * - Keywords (if provided)
 * - Edit and Delete action buttons
 * - Drag handle for reordering
 */
export const FaqItemCard: React.FC<FaqItemCardProps> = ({
  faq,
  onEdit,
  onDelete,
  disabled = false,
  isDragging = false,
}) => {
  // Truncate question for display if needed
  const displayQuestion = truncateText(faq.question, 50);
  const isQuestionTruncated = faq.question.length > 50;

  // Truncate answer for preview
  const answerPreview = truncateText(faq.answer, 100);

  // Parse keywords for display
  const keywordList = faq.keywords
    ? faq.keywords.split(',').map((k) => k.trim()).filter(Boolean)
    : [];

  const handleEditClick = () => {
    onEdit(faq);
  };

  const handleDeleteClick = () => {
    onDelete(faq);
  };

  return (
    <div
      className={`group bg-white border rounded-lg p-4 transition-all duration-200 ${
        isDragging
          ? 'border-primary/50 shadow-lg opacity-75'
          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
      }`}
      role="article"
      aria-label={`FAQ: ${displayQuestion}`}
    >
      <div className="flex items-start gap-3">
        {/* Drag Handle */}
        <div
          className="flex-shrink-0 cursor-grab active:cursor-grabbing text-gray-400 hover:text-gray-600 p-1 -ml-1"
          aria-label="Drag to reorder this FAQ item"
          draggable={true}
        >
          <GripVertical size={18} strokeWidth={2} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Question */}
          <h3 className="text-sm font-semibold text-gray-900 mb-1">
            {displayQuestion}
            {isQuestionTruncated && (
              <span className="font-normal text-gray-500 ml-1">...</span>
            )}
          </h3>

          {/* Answer Preview */}
          <p className="text-sm text-gray-600 mb-2 line-clamp-2">
            {answerPreview}
          </p>

          {/* Keywords */}
          {keywordList.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {keywordList.slice(0, 3).map((keyword, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-md"
                >
                  <Tag size={10} strokeWidth={2} />
                  {keyword}
                </span>
              ))}
              {keywordList.length > 3 && (
                <span className="text-xs text-gray-500">
                  +{keywordList.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Edit Button */}
          <button
            type="button"
            onClick={handleEditClick}
            disabled={disabled}
            className="p-2 text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Edit FAQ: ${displayQuestion}`}
          >
            <Edit2 size={16} strokeWidth={2} />
          </button>

          {/* Delete Button */}
          <button
            type="button"
            onClick={handleDeleteClick}
            disabled={disabled}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label={`Delete FAQ: ${displayQuestion}`}
          >
            <Trash2 size={16} strokeWidth={2} />
          </button>
        </div>
      </div>
    </div>
  );
};
