/**
 * Celebration Animation Component
 *
 * Reusable confetti celebration with:
 * - Accessibility support (prefers-reduced-motion)
 * - Toggle on/off
 * - Customizable intensity
 * - Different celebration types
 */

import * as React from "react";
import { useReducedMotion } from "framer-motion";
import confetti from "canvas-confetti";
import { Sparkles, PartyPopper, Star } from "lucide-react";

export type CelebrationType = "confetti" | "sparkles" | "stars" | "complete";

export interface CelebrationAnimationProps {
  type?: CelebrationType;
  intensity?: "low" | "medium" | "high";
  enabled?: boolean;
  onComplete?: () => void;
  trigger?: boolean;
  className?: string;
}

export function useCelebration() {
  const prefersReducedMotion = useReducedMotion();
  const [enabled, setEnabled] = React.useState(true);

  const celebrate = React.useCallback(
    (type: CelebrationType = "confetti", intensity: "low" | "medium" | "high" = "medium") => {
      if (!enabled || prefersReducedMotion) return;

      const configs = {
        confetti: {
          low: { particleCount: 30, spread: 50, origin: { y: 0.7 } },
          medium: { particleCount: 50, spread: 70, origin: { y: 0.6 } },
          high: { particleCount: 100, spread: 100, origin: { y: 0.5 } },
        },
        sparkles: {
          low: { particleCount: 20, spread: 40, origin: { y: 0.8 }, colors: ["#d7fff3", "#82d3ff"] },
          medium: { particleCount: 40, spread: 60, origin: { y: 0.7 }, colors: ["#d7fff3", "#82d3ff", "#00f5d4"] },
          high: { particleCount: 80, spread: 80, origin: { y: 0.6 }, colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"] },
        },
        stars: {
          low: { particleCount: 25, spread: 45, origin: { y: 0.7 }, shapes: ["star"] },
          medium: { particleCount: 50, spread: 65, origin: { y: 0.6 }, shapes: ["star"] },
          high: { particleCount: 100, spread: 90, origin: { y: 0.5 }, shapes: ["star"] },
        },
        complete: {
          low: {
            particleCount: 50,
            spread: 70,
            origin: { y: 0.6 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4"],
            disableForReducedMotion: true,
            ticks: 100,
          },
          medium: {
            particleCount: 100,
            spread: 100,
            origin: { y: 0.5 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"],
            disableForReducedMotion: true,
            ticks: 150,
          },
          high: {
            particleCount: 150,
            spread: 120,
            origin: { y: 0.4 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"],
            disableForReducedMotion: true,
            ticks: 200,
          },
        },
      };

      const config = configs[type][intensity];
      confetti(config);
    },
    [enabled, prefersReducedMotion],
  );

  return { celebrate, enabled, setEnabled, prefersReducedMotion };
}

export function CelebrationAnimation({
  type = "confetti",
  intensity = "medium",
  enabled = true,
  trigger = false,
  onComplete,
  className = "",
}: CelebrationAnimationProps): React.ReactElement | null {
  const prefersReducedMotion = useReducedMotion();

  React.useEffect(() => {
    if (trigger && enabled && !prefersReducedMotion) {
      const configs = {
        confetti: {
          low: { particleCount: 30, spread: 50, origin: { y: 0.7 } },
          medium: { particleCount: 50, spread: 70, origin: { y: 0.6 } },
          high: { particleCount: 100, spread: 100, origin: { y: 0.5 } },
        },
        sparkles: {
          low: { particleCount: 20, spread: 40, origin: { y: 0.8 }, colors: ["#d7fff3", "#82d3ff"] },
          medium: { particleCount: 40, spread: 60, origin: { y: 0.7 }, colors: ["#d7fff3", "#82d3ff", "#00f5d4"] },
          high: { particleCount: 80, spread: 80, origin: { y: 0.6 }, colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"] },
        },
        stars: {
          low: { particleCount: 25, spread: 45, origin: { y: 0.7 } },
          medium: { particleCount: 50, spread: 65, origin: { y: 0.6 } },
          high: { particleCount: 100, spread: 90, origin: { y: 0.5 } },
        },
        complete: {
          low: {
            particleCount: 50,
            spread: 70,
            origin: { y: 0.6 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4"],
            ticks: 100,
          },
          medium: {
            particleCount: 100,
            spread: 100,
            origin: { y: 0.5 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"],
            ticks: 150,
          },
          high: {
            particleCount: 150,
            spread: 120,
            origin: { y: 0.4 },
            colors: ["#d7fff3", "#82d3ff", "#00f5d4", "#10b981"],
            ticks: 200,
          },
        },
      };

      const config = configs[type][intensity];
      confetti({
        ...config,
        disableForReducedMotion: true,
      });

      // Call completion callback after animation
      const duration = intensity === "low" ? 1000 : intensity === "medium" ? 1500 : 2000;
      const timer = setTimeout(() => {
        onComplete?.();
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [trigger, enabled, prefersReducedMotion, type, intensity, onComplete]);

  // Don't render anything - this component just triggers confetti
  return null;
}

/**
 * Static celebration icons (for use when animations are disabled)
 */
export function CelebrationIcon({ type = "confetti", className = "" }: { type?: CelebrationType; className?: string }) {
  const icons = {
    confetti: PartyPopper,
    sparkles: Sparkles,
    stars: Star,
    complete: PartyPopper,
  };

  const Icon = icons[type || "confetti"];
  return <Icon className={className} />;
}
