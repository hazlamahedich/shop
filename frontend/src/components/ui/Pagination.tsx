/**
 * Pagination Component
 *
 * Industrial Technical Dashboard design with terminal aesthetics.
 * Displays pagination controls for navigating data sets.
 */

import React from 'react';
import { ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  total: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onPerPageChange: (perPage: number) => void;
  isLoading?: boolean;
}

const PER_PAGE_OPTIONS = [10, 20, 50, 100];

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  total,
  perPage,
  onPageChange,
  onPerPageChange,
  isLoading = false,
}) => {
  const startItem = total === 0 ? 0 : (currentPage - 1) * perPage + 1;
  const endItem = Math.min(currentPage * perPage, total);

  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const showEllipsisStart = currentPage > 3;
    const showEllipsisEnd = currentPage < totalPages - 2;

    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);
      
      if (showEllipsisStart) {
        pages.push('ellipsis');
      }
      
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);
      
      for (let i = start; i <= end; i++) {
        if (!pages.includes(i)) {
          pages.push(i);
        }
      }
      
      if (showEllipsisEnd) {
        pages.push('ellipsis');
      }
      
      if (!pages.includes(totalPages)) {
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div 
      className="flex items-center justify-between w-full"
      style={{ fontFamily: 'JetBrains Mono, monospace' }}
    >
      {/* Page navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1 || isLoading}
          className="px-4 py-2.5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          style={{
            backgroundColor: '#080808',
            border: '1px solid #2f2f2f',
            color: currentPage <= 1 ? '#6a6a6a' : '#FFFFFF',
            fontSize: '10px',
            fontWeight: 600,
            letterSpacing: '0.1em',
          }}
          aria-label="Previous page"
        >
          &lt; PREV
        </button>

        {getPageNumbers().map((page, index) => (
          page === 'ellipsis' ? (
            <span 
              key={`ellipsis-${index}`}
              className="px-2"
              style={{ color: '#6a6a6a', fontSize: '11px' }}
            >
              ...
            </span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              disabled={isLoading}
              className="px-3 py-2.5 transition-all"
              style={{
                backgroundColor: page === currentPage ? '#00FF88' : '#080808',
                border: '1px solid #2f2f2f',
                color: page === currentPage ? '#0C0C0C' : '#8a8a8a',
                fontSize: '11px',
                fontWeight: page === currentPage ? 700 : 500,
              }}
              aria-label={`Go to page ${page}`}
              aria-current={page === currentPage ? 'page' : undefined}
            >
              {page}
            </button>
          )
        ))}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || isLoading}
          className="px-4 py-2.5 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
          style={{
            backgroundColor: '#080808',
            border: '1px solid #2f2f2f',
            color: currentPage >= totalPages ? '#6a6a6a' : '#FFFFFF',
            fontSize: '10px',
            fontWeight: 600,
            letterSpacing: '0.1em',
          }}
          aria-label="Next page"
        >
          NEXT &gt;
        </button>
      </div>
    </div>
  );
};

export default Pagination;
