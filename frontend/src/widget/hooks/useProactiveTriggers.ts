import * as React from 'react';
import type {
  TriggerType,
  ProactiveTrigger,
  ProactiveEngagementConfig,
} from '../types/widget';
import { DEFAULT_PROACTIVE_CONFIG, DEFAULT_PROACTIVE_THRESHOLDS } from '../types/widget';

const COOLDOWN_STORAGE_KEY = 'widget-proactive-cooldown';
const DISMISSED_STORAGE_KEY = 'widget-proactive-dismissed';

interface UseProactiveTriggersOptions {
  config?: ProactiveEngagementConfig;
  onTrigger?: (trigger: ProactiveTrigger) => void;
  productViewCount?: number;
  cartHasItems?: boolean;
}

interface UseProactiveTriggersReturn {
  activeTrigger: ProactiveTrigger | null;
  dismissedTriggers: Set<string>;
  triggerProactive: (type: TriggerType) => void;
  dismissTrigger: () => void;
  resetTrigger: (type: TriggerType) => void;
  isActive: boolean;
}

function getCooldowns(): Record<string, number> {
  if (typeof window === 'undefined') return {};
  try {
    const stored = sessionStorage.getItem(COOLDOWN_STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch {
    return {};
  }
}

function setCooldown(type: TriggerType, minutes: number): void {
  if (typeof window === 'undefined') return;
  try {
    const cooldowns = getCooldowns();
    cooldowns[type] = Date.now() + minutes * 60 * 1000;
    sessionStorage.setItem(COOLDOWN_STORAGE_KEY, JSON.stringify(cooldowns));
  } catch {
    // sessionStorage not available
  }
}

function isInCooldown(type: TriggerType): boolean {
  const cooldowns = getCooldowns();
  return cooldowns[type] !== undefined && cooldowns[type] > Date.now();
}

function getDismissedTriggers(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    const stored = sessionStorage.getItem(DISMISSED_STORAGE_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  } catch {
    return new Set();
  }
}

function setDismissedTrigger(type: TriggerType): void {
  if (typeof window === 'undefined') return;
  try {
    const dismissed = getDismissedTriggers();
    dismissed.add(type);
    sessionStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify([...dismissed]));
  } catch {
    // sessionStorage not available
  }
}

function trackTriggerFired(type: TriggerType): void {
  if (process.env.NODE_ENV === 'development') {
    console.debug('[Proactive]', type, 'triggered');
  }
}

export function useProactiveTriggers(
  options: UseProactiveTriggersOptions = {}
): UseProactiveTriggersReturn {
  const {
    config = DEFAULT_PROACTIVE_CONFIG,
    onTrigger,
    productViewCount = 0,
    cartHasItems = false,
  } = options;

  const [activeTrigger, setActiveTrigger] = React.useState<ProactiveTrigger | null>(null);
  const [dismissedTriggers, setDismissedTriggersState] = React.useState<Set<string>>(
    getDismissedTriggers
  );

  const pageLoadTime = React.useRef(Date.now());
  const hasFiredRef = React.useRef<Set<string>>(new Set());

  const triggers = React.useMemo(() => {
    return config.enabled ? config.triggers.filter((t) => t.enabled) : [];
  }, [config]);

  const fireTrigger = React.useCallback(
    (trigger: ProactiveTrigger) => {
      const type = trigger.type;

      if (hasFiredRef.current.has(type)) return;
      if (dismissedTriggers.has(type)) return;
      if (isInCooldown(type)) return;

      hasFiredRef.current.add(type);
      setCooldown(type, trigger.cooldown);
      trackTriggerFired(type);
      setActiveTrigger(trigger);
      onTrigger?.(trigger);
    },
    [dismissedTriggers, onTrigger]
  );

  const triggerProactive = React.useCallback(
    (type: TriggerType) => {
      const trigger = triggers.find((t) => t.type === type);
      if (trigger) {
        fireTrigger(trigger);
      }
    },
    [triggers, fireTrigger]
  );

  const dismissTrigger = React.useCallback(() => {
    if (activeTrigger) {
      setDismissedTrigger(activeTrigger.type);
      setDismissedTriggersState((prev) => new Set([...prev, activeTrigger.type]));
    }
    setActiveTrigger(null);
  }, [activeTrigger]);

  const resetTrigger = React.useCallback((type: TriggerType) => {
    hasFiredRef.current.delete(type);
    try {
      const cooldowns = getCooldowns();
      delete cooldowns[type];
      sessionStorage.setItem(COOLDOWN_STORAGE_KEY, JSON.stringify(cooldowns));

      const dismissed = getDismissedTriggers();
      dismissed.delete(type);
      sessionStorage.setItem(DISMISSED_STORAGE_KEY, JSON.stringify([...dismissed]));

      setDismissedTriggersState(new Set(dismissed));
    } catch {
      // sessionStorage not available
    }
  }, []);

  React.useEffect(() => {
    const exitIntentTrigger = triggers.find((t) => t.type === 'exit_intent');
    if (!exitIntentTrigger) return;

    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0 && !hasFiredRef.current.has('exit_intent')) {
        fireTrigger(exitIntentTrigger);
      }
    };

    document.addEventListener('mouseleave', handleMouseLeave);
    return () => document.removeEventListener('mouseleave', handleMouseLeave);
  }, [triggers, fireTrigger]);

  React.useEffect(() => {
    const timeTrigger = triggers.find((t) => t.type === 'time_on_page');
    if (!timeTrigger || !timeTrigger.threshold) return;

    const thresholdMs = timeTrigger.threshold * 1000;
    const elapsed = Date.now() - pageLoadTime.current;
    const remaining = thresholdMs - elapsed;

    if (remaining <= 0) {
      fireTrigger(timeTrigger);
      return;
    }

    const timerId = setTimeout(() => {
      fireTrigger(timeTrigger);
    }, remaining);

    return () => clearTimeout(timerId);
  }, [triggers, fireTrigger]);

  React.useEffect(() => {
    const scrollTrigger = triggers.find((t) => t.type === 'scroll_depth');
    if (!scrollTrigger || !scrollTrigger.threshold) return;

    let ticking = false;

    const handleScroll = () => {
      if (ticking) return;
      if (hasFiredRef.current.has('scroll_depth')) return;

      ticking = true;
      requestAnimationFrame(() => {
        const scrollTop = window.scrollY;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercent = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;

        if (scrollPercent >= scrollTrigger.threshold!) {
          fireTrigger(scrollTrigger);
        }
        ticking = false;
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [triggers, fireTrigger]);

  React.useEffect(() => {
    const productViewTrigger = triggers.find((t) => t.type === 'product_view');
    if (!productViewTrigger || !productViewTrigger.threshold) return;

    if (
      productViewCount >= productViewTrigger.threshold &&
      !hasFiredRef.current.has('product_view')
    ) {
      fireTrigger(productViewTrigger);
    }
  }, [productViewCount, triggers, fireTrigger]);

  React.useEffect(() => {
    const cartTrigger = triggers.find((t) => t.type === 'cart_abandonment');
    if (!cartTrigger) return;

    const handleMouseLeave = (e: MouseEvent) => {
      if (e.clientY <= 0) {
        if (cartHasItems && !hasFiredRef.current.has('cart_abandonment')) {
          fireTrigger(cartTrigger);
        }
      }
    };

    const handleBeforeUnload = () => {
      if (cartHasItems && !hasFiredRef.current.has('cart_abandonment')) {
        setCooldown('cart_abandonment', cartTrigger.cooldown);
        setDismissedTrigger('cart_abandonment');
        hasFiredRef.current.add('cart_abandonment');
      }
    };

    document.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      document.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [cartHasItems, triggers, fireTrigger]);

  return {
    activeTrigger,
    dismissedTriggers,
    triggerProactive,
    dismissTrigger,
    resetTrigger,
    isActive: activeTrigger !== null,
  };
}

export { DEFAULT_PROACTIVE_THRESHOLDS };
