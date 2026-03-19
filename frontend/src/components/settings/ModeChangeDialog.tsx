/**
 * Mode Change Confirmation Dialog
 *
 * Story 8.7: Frontend - Settings Mode Toggle
 *
 * Displays confirmation dialog when changing merchant mode with appropriate warnings.
 * Implements accessibility features including focus management and keyboard navigation.
 */

import React, { useEffect, useRef } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../ui/Dialog';
import { Button } from '../ui/Button';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import type { OnboardingMode } from '../../types/onboarding';

export interface ModeChangeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  currentMode: OnboardingMode;
  targetMode: OnboardingMode;
  loading?: boolean;
}

export function ModeChangeDialog({
  isOpen,
  onClose,
  onConfirm,
  currentMode: _currentMode,
  targetMode,
  loading = false,
}: ModeChangeDialogProps) {
  const [acknowledged, setAcknowledged] = React.useState(false);
  const cancelButtonRef = useRef<HTMLButtonElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  // Reset acknowledgment when dialog opens/closes
  useEffect(() => {
    if (!isOpen) {
      setAcknowledged(false);
    }
  }, [isOpen]);

  // Focus cancel button when dialog opens, save trigger element
  useEffect(() => {
    if (isOpen) {
      triggerRef.current = document.activeElement as HTMLElement;
      if (cancelButtonRef.current) {
        cancelButtonRef.current.focus();
      }
    }
  }, [isOpen]);

  // Restore focus to trigger element when dialog closes
  const handleClose = () => {
    onClose();
    if (triggerRef.current && typeof triggerRef.current.focus === 'function') {
      triggerRef.current.focus();
    }
  };

  const isSwitchingToGeneral = targetMode === 'general';

  const title = isSwitchingToGeneral
    ? 'Switch to General Chatbot Mode?'
    : 'Switch to E-commerce Mode?';

  const description = isSwitchingToGeneral
    ? 'Warning: This will disable e-commerce features'
    : "You're about to enable e-commerce features";

  const features = isSwitchingToGeneral
    ? [
        'Product search will be disabled',
        'Shopping cart will be cleared',
        'Shopify integration will be disconnected',
      ]
    : [
        'Product search and recommendations',
        'Shopping cart management',
        'Shopify checkout integration',
        'Order tracking',
      ];

  const additionalInfo = isSwitchingToGeneral
    ? 'Your Shopify and Facebook data will be preserved but won\'t be used.'
    : 'To use these features, you\'ll need to connect your Shopify store.';

  const confirmButtonText = isSwitchingToGeneral
    ? 'Switch to General'
    : 'Switch to E-commerce';

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && handleClose()}>
      <DialogContent
        className="sm:max-w-lg"
        showCloseButton={!loading}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="mode-dialog-title"
        aria-describedby="mode-dialog-description"
      >
        <DialogHeader>
          <DialogTitle id="mode-dialog-title" className="flex items-center gap-2">
            {isSwitchingToGeneral && <AlertTriangle className="w-5 h-5 text-amber-500" />}
            {title}
          </DialogTitle>
          <DialogDescription id="mode-dialog-description">
            {description}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Feature list */}
          <div className="space-y-2">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`flex items-center gap-2 text-sm ${
                  isSwitchingToGeneral ? 'text-white/60' : 'text-white/70'
                }`}
              >
                <span className={isSwitchingToGeneral ? 'text-red-500' : 'text-green-500'}>
                  {isSwitchingToGeneral ? '✗' : '✓'}
                </span>
                {feature}
              </div>
            ))}
          </div>

          {/* Additional info */}
          <div
              className={`p-3 rounded-lg ${
                isSwitchingToGeneral
                  ? 'bg-amber-500/10 border border-amber-500/20'
                  : 'bg-blue-500/10 border border-blue-500/20'
              }`}
          >
              <p
                className={`text-sm ${
                  isSwitchingToGeneral ? 'text-amber-300' : 'text-blue-300'
                }`}
              >
              {additionalInfo}
            </p>
          </div>

          {/* Acknowledgment checkbox for switching to general */}
          {isSwitchingToGeneral && (
            <label className="flex items-start gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={acknowledged}
                onChange={(e) => setAcknowledged(e.target.checked)}
                className="mt-1 h-4 w-4 rounded border-white/20 text-emerald-500 focus:ring-emerald-500/50 bg-white/[0.03]"
                disabled={loading}
              />
              <span className="text-sm text-white/60">
                I understand that my store data will be preserved but inactive
              </span>
            </label>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            ref={cancelButtonRef}
            variant="outline"
            onClick={handleClose}
            disabled={loading}
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={loading || (isSwitchingToGeneral && !acknowledged)}
            className={isSwitchingToGeneral ? 'bg-amber-600 hover:bg-amber-700' : ''}
          >
            {loading ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Updating...
              </>
            ) : (
              <>
                {confirmButtonText}
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
