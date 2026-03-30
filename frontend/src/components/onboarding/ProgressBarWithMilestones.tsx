/**
 * Gamified Progress Bar with Milestones and Celebrations
 *
 * Features:
 * - Smooth animated progress bar
 * - Milestone celebrations with confetti
 * - Time estimates
 * - Accessibility support (respects prefers-reduced-motion)
 * - Encouraging messages at key milestones
 */

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import confetti from "canvas-confetti";
import { Check, Sparkles, Flame, Rocket, PartyPopper } from "lucide-react";

export interface Milestone {
  step: number;
  message: string;
  icon: string;
}

export interface ProgressBarWithMilestonesProps {
  currentStep: number;
  totalSteps: number;
  stepName: string;
  totalMinutes?: number;
  milestones?: Milestone[];
  showCelebration?: boolean;
  className?: string;
}

const DEFAULT_MILESTONES: Milestone[] = [
  { step: 1, message: "Great choice! 🎉", icon: "sparkles" },
  { step: 2, message: "Halfway there! Keep going!", icon: "fire" },
  { step: 3, message: "Almost done! 🚀", icon: "rocket" },
  { step: 4, message: "You did it! 🎊", icon: "party" },
];

const ICON_MAP = {
  sparkles: Sparkles,
  fire: Flame,
  rocket: Rocket,
  party: PartyPopper,
};

export function ProgressBarWithMilestones({
  currentStep,
  totalSteps,
  stepName,
  totalMinutes,
  milestones = DEFAULT_MILESTONES,
  showCelebration = true,
  className = "",
}: ProgressBarWithMilestonesProps): React.ReactElement {
  const prefersReducedMotion = useReducedMotion();
  const previousStep = React.useRef<number>(currentStep);
  const [celebrationEnabled, setCelebrationEnabled] = React.useState(true);

  const progressPercentage = (currentStep / totalSteps) * 100;
  const currentMilestone = milestones.find((m) => m.step === currentStep);

  // Trigger confetti on milestone reach (with motion preference check)
  React.useEffect(() => {
    if (
      showCelebration &&
      celebrationEnabled &&
      currentMilestone &&
      currentStep !== previousStep.current &&
      !prefersReducedMotion
    ) {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.7 },
        colors: ["#d7fff3", "#82d3ff", "#00f5d4"],
        disableForReducedMotion: true,
        ticks: 100,
      });
    }
    previousStep.current = currentStep;
  }, [currentStep, currentMilestone, showCelebration, celebrationEnabled, prefersReducedMotion]);

  const IconComponent = currentMilestone ? ICON_MAP[currentMilestone.icon as keyof typeof ICON_MAP] : null;

  return (
    <div className={`w-full space-y-4 ${className}`} role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={totalSteps} aria-label={`Step ${currentStep} of ${totalSteps}: ${stepName}`}>
      {/* Step and Time Info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-white/90">
            Step {currentStep} of {totalSteps}
          </span>
          <span className="text-white/40">•</span>
          <span className="text-sm text-white/70">{stepName}</span>
        </div>
        <div className="flex items-center gap-3">
          {totalMinutes && (
            <span className="text-xs text-white/50">
              ~{Math.round((totalMinutes / totalSteps) * (totalSteps - currentStep + 1))} min left
            </span>
          )}
          <motion.span
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="text-sm font-bold text-emerald-400"
          >
            {Math.round(progressPercentage)}%
          </motion.span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-2 bg-white/10 rounded-full overflow-hidden relative">
        <motion.div
          className="h-full bg-gradient-to-r from-emerald-500 via-cyan-500 to-emerald-400 relative"
          initial={{ width: 0 }}
          animate={{ width: `${progressPercentage}%` }}
          transition={
            prefersReducedMotion
              ? { duration: 0 }
              : { duration: 0.5, ease: "easeOut" }
          }
        >
          {/* Shimmer effect on progress bar */}
          {!prefersReducedMotion && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              animate={{
                x: ["-100%", "200%"],
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "linear",
              }}
            />
          )}
        </motion.div>
      </div>

      {/* Milestone Celebration */}
      {currentMilestone && (
        <motion.div
          initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: prefersReducedMotion ? 0 : 0.4 }}
          className="flex items-center gap-2 text-emerald-400 text-sm font-bold"
        >
          {IconComponent && <IconComponent size={16} />}
          <span>{currentMilestone.message}</span>
        </motion.div>
      )}

      {/* Celebration Toggle (for accessibility) */}
      <label className="flex items-center gap-2 text-xs text-white/40 cursor-pointer hover:text-white/60 transition-colors">
        <input
          type="checkbox"
          checked={celebrationEnabled}
          onChange={(e) => setCelebrationEnabled(e.target.checked)}
          className="w-3 h-3 rounded"
        />
        <span>Show celebrations (can be distracting)</span>
      </label>
    </div>
  );
}
