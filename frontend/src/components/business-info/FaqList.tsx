/**
 * FaqList Component
 *
 * Story 1.11: Business Info & FAQ Configuration
 *
 * Displays a list of FAQ items with:
 * - Add FAQ Item button
 * - List of FAQ items with Edit/Delete actions
 * - Drag-and-drop reordering support
 * - Empty state when no FAQs exist
 * - Loading and error states
 *
 * WCAG 2.1 AA accessible.
 */

import * as React from 'react';
import { PlusCircle, MessageSquare, AlertCircle } from 'lucide-react';
import { useBusinessInfoStore, type FaqItem, type FaqCreateRequest, type FaqUpdateRequest } from '../../stores/businessInfoStore';
import { FaqItemCard } from './FaqItemCard';
import { FaqForm } from './FaqForm';

export interface FaqListProps {
  /** Optional CSS class name */
  className?: string;
}

/**
 * FaqList Component
 *
 * Displays and manages FAQ items with:
 * - Add/Edit/Delete functionality
 * - Drag-and-drop reordering
 * - Empty state and loading states
 * - Error handling
 */
export const FaqList: React.FC<FaqListProps> = ({ className = '' }) => {
  const {
    faqs,
    faqsLoadingState,
    error,
    createFaq,
    updateFaq,
    deleteFaq,
    reorderFaqs,
    clearError,
  } = useBusinessInfoStore();

  // UI state
  const [isFormOpen, setIsFormOpen] = React.useState(false);
  const [editingFaq, setEditingFaq] = React.useState<FaqItem | null>(null);
  const [isSaving, setIsSaving] = React.useState(false);
  const [draggedItem, setDraggedItem] = React.useState<FaqItem | null>(null);
  const [dragOverItem, setDragOverItem] = React.useState<FaqItem | null>(null);

  // Handle add FAQ button click
  const handleAddClick = () => {
    setEditingFaq(null);
    setIsFormOpen(true);
    clearError();
  };

  // Handle edit button click
  const handleEditClick = (faq: FaqItem) => {
    setEditingFaq(faq);
    setIsFormOpen(true);
    clearError();
  };

  // Handle delete button click
  const handleDeleteClick = async (faq: FaqItem) => {
    // In a real app, you'd show a confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to delete the FAQ "${faq.question}"?`
    );
    if (!confirmed) return;

    try {
      await deleteFaq(faq.id);
    } catch (error) {
      console.error('Failed to delete FAQ:', error);
    }
  };

  // Handle form save
  const handleFormSave = async (data: FaqCreateRequest | FaqUpdateRequest) => {
    setIsSaving(true);

    try {
      if (editingFaq) {
        await updateFaq(editingFaq.id, data);
      } else {
        await createFaq(data as FaqCreateRequest);
      }
      setIsFormOpen(false);
      setEditingFaq(null);
    } catch (error) {
      console.error('Failed to save FAQ:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle form cancel
  const handleFormCancel = () => {
    setIsFormOpen(false);
    setEditingFaq(null);
  };

  // Drag and drop handlers
  const handleDragStart = (faq: FaqItem) => {
    setDraggedItem(faq);
  };

  const handleDragOver = (e: React.DragEvent, faq: FaqItem) => {
    e.preventDefault();
    if (draggedItem && draggedItem.id !== faq.id) {
      setDragOverItem(faq);
    }
  };

  const handleDragEnd = async () => {
    if (draggedItem && dragOverItem && draggedItem.id !== dragOverItem.id) {
      // Create new order by swapping positions
      const newOrder = [...faqs];
      const draggedIndex = newOrder.findIndex((f) => f.id === draggedItem.id);
      const overIndex = newOrder.findIndex((f) => f.id === dragOverItem.id);

      // Remove dragged item and insert at new position
      newOrder.splice(draggedIndex, 1);
      newOrder.splice(overIndex, 0, draggedItem);

      // Get IDs in new order
      const newOrderIds = newOrder.map((f) => f.id);

      try {
        await reorderFaqs(newOrderIds);
      } catch (error) {
        console.error('Failed to reorder FAQs:', error);
      }
    }

    setDraggedItem(null);
    setDragOverItem(null);
  };

  // Loading state
  if (faqsLoadingState === 'loading' && faqs.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center py-12 ${className}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mb-4" />
        <p className="text-sm text-gray-600">Loading FAQ items...</p>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">FAQ Items</h2>
          <p className="text-sm text-gray-500">
            Create frequently asked questions for automatic bot responses.
          </p>
        </div>
        <button
          type="button"
          onClick={handleAddClick}
          disabled={faqsLoadingState === 'loading'}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary rounded-lg hover:bg-primary/90 focus:ring-2 focus:ring-primary focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <PlusCircle size={18} />
          Add FAQ Item
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div
          role="alert"
          className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3"
        >
          <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
          <button
            type="button"
            onClick={clearError}
            className="text-red-600 hover:text-red-800"
            aria-label="Dismiss error"
          >
            ×
          </button>
        </div>
      )}

      {/* FAQ List */}
      {faqs.length === 0 ? (
        // Empty state
        <div className="text-center py-12 px-6 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
          <MessageSquare size={48} className="mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No FAQ items yet</h3>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            Create FAQ items to help your bot automatically answer common customer questions.
          </p>
          <button
            type="button"
            onClick={handleAddClick}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary bg-primary/10 rounded-lg hover:bg-primary/20 transition-colors"
          >
            <PlusCircle size={18} />
            Create your first FAQ
          </button>
        </div>
      ) : (
        // FAQ items
        <div className="space-y-3">
          {faqs.map((faq) => (
            <div
              key={faq.id}
              draggable={true}
              onDragStart={() => handleDragStart(faq)}
              onDragOver={(e) => handleDragOver(e, faq)}
              onDragEnd={handleDragEnd}
              className={dragOverItem?.id === faq.id ? 'cursor-move' : ''}
            >
              <FaqItemCard
                faq={faq}
                onEdit={handleEditClick}
                onDelete={handleDeleteClick}
                disabled={faqsLoadingState === 'loading'}
                isDragging={draggedItem?.id === faq.id}
              />
            </div>
          ))}
        </div>
      )}

      {/* Help text */}
      {faqs.length > 0 && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Tip:</strong> Drag and drop FAQ items to reorder them. The bot will use
            this order when multiple FAQs match a customer's question.
          </p>
        </div>
      )}

      {/* FAQ Form Modal */}
      <FaqForm
        faq={editingFaq}
        isOpen={isFormOpen}
        onSave={handleFormSave}
        onCancel={handleFormCancel}
        disabled={isSaving}
      />
    </div>
  );
};
