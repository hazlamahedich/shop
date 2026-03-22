/**
 * FaqItemCard Component
 *
 * Designed for "Mantis HUD"
 */

import * as React from 'react';
import { Edit2, Trash2, GripVertical, Tag } from 'lucide-react';
import type { FaqItem } from '../../stores/businessInfoStore';

export interface FaqItemCardProps {
  faq: FaqItem;
  onEdit: (faq: FaqItem) => void;
  onDelete: (faq: FaqItem) => void;
  disabled?: boolean;
  isDragging?: boolean;
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export const FaqItemCard: React.FC<FaqItemCardProps> = ({
  faq,
  onEdit,
  onDelete,
  disabled = false,
  isDragging = false,
}) => {
  const displayQuestion = truncateText(faq.question, 50);
  const isQuestionTruncated = faq.question.length > 50;
  const answerPreview = truncateText(faq.answer, 100);
  const keywordList = faq.keywords
    ? faq.keywords.split(',').map((k) => k.trim()).filter(Boolean)
    : [];

  const handleEditClick = () => onEdit(faq);
  const handleDeleteClick = () => onDelete(faq);

  return (
    <div
      className={`group bg-[#1f1f25]/80 backdrop-blur-md border rounded-xl p-4 transition-all duration-300 ${
        isDragging
          ? 'border-[#00f5d4]/50 shadow-[0_0_20px_rgba(0,245,212,0.2)] opacity-75'
          : 'border-[#3a4a46]/20 hover:border-[#00f5d4]/30 hover:shadow-[0_0_15px_rgba(0,245,212,0.1)]'
      }`}
      role="article"
      aria-label={`FAQ: ${displayQuestion}`}
    >
      <div className="flex items-start gap-4">
        {/* Drag Handle */}
        <div
          className="flex-shrink-0 cursor-grab active:cursor-grabbing text-[#3a4a46] hover:text-[#00f5d4] p-1 -ml-1 transition-colors"
          aria-label="Drag to reorder this FAQ item"
          draggable={true}
        >
          <GripVertical size={18} strokeWidth={2} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-bold text-[#e4e1e9] mb-1 font-['Inter']">
            {displayQuestion}
            {isQuestionTruncated && (
              <span className="font-normal text-[#b9cac4]/50 ml-1">...</span>
            )}
          </h3>

          <p className="text-xs text-[#b9cac4]/80 mb-3 line-clamp-2 leading-relaxed font-['Inter']">
            {answerPreview}
          </p>

          {keywordList.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {keywordList.slice(0, 3).map((keyword, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-[#1b1b20] border border-[#3a4a46]/30 text-[#b9cac4] text-[10px] uppercase font-bold tracking-widest rounded-md font-['Space_Grotesk']"
                >
                  <Tag size={10} strokeWidth={2} className="text-[#00dfc1]" />
                  {keyword}
                </span>
              ))}
              {keywordList.length > 3 && (
                <span className="text-[10px] text-[#3a4a46] font-bold uppercase tracking-widest mt-1">
                  +{keywordList.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col items-center gap-2 flex-shrink-0 border-l border-[#3a4a46]/20 pl-4 ml-2">
          <button
            type="button"
            onClick={handleEditClick}
            disabled={disabled}
            className="p-2.5 text-[#b9cac4] bg-[#1b1b20] border border-[#3a4a46]/30 hover:text-[#00dfc1] hover:border-[#00f5d4]/40 hover:bg-[#00f5d4]/5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed group/btn"
            aria-label={`Edit FAQ: ${displayQuestion}`}
          >
            <Edit2 size={14} strokeWidth={2.5} className="group-hover/btn:drop-shadow-[0_0_8px_rgba(0,245,212,0.5)]" />
          </button>

          <button
            type="button"
            onClick={handleDeleteClick}
            disabled={disabled}
            className="p-2.5 text-[#b9cac4] bg-[#1b1b20] border border-[#3a4a46]/30 hover:text-[#ffb4ab] hover:border-[#ffb4ab]/40 hover:bg-[#ffb4ab]/5 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed group/btn"
            aria-label={`Delete FAQ: ${displayQuestion}`}
          >
            <Trash2 size={14} strokeWidth={2.5} className="group-hover/btn:drop-shadow-[0_0_8px_rgba(255,180,171,0.5)]" />
          </button>
        </div>
      </div>
    </div>
  );
};
