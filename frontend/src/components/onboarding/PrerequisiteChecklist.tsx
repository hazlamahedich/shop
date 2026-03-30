/**
 * Interactive Prerequisite Checklist with Celebrations
 *
 * Features:
 * - Mode-aware prerequisites (general vs ecommerce)
 * - Interactive help sections with demos
 * - Real-time validation with green checkmarks
 * - Celebration animations on completion
 * - Better accessibility and contrast
 * - Clear time estimates
 */

import * as React from "react";
import { motion, useReducedMotion } from "framer-motion";
import confetti from "canvas-confetti";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "../ui/Card";
import { Checkbox } from "../ui/Checkbox";
import { Button } from "../ui/Button";
import { Collapsible, CollapsibleTrigger, CollapsibleContent } from "../ui/Collapsible";
import { Progress } from "../ui/Progress";
import { onboardingStore, PrerequisiteKey } from "../../stores/onboardingStore";
import { OnboardingMode } from "../../types/onboarding";
import { Check, Clock, ChevronDown, ChevronUp, Sparkles, ExternalLink } from "lucide-react";

export interface PrerequisiteItem {
  key: PrerequisiteKey;
  title: string;
  description: string;
  helpUrl: string;
  helpContent: string[];
  showInModes: OnboardingMode[];
  whyMatters?: string;
  estimatedTime?: string;
}

export interface PrerequisiteChecklistProps {
  mode?: OnboardingMode;
}

const PREREQUISITES: PrerequisiteItem[] = [
  {
    key: "cloudAccount",
    title: "Cloud Provider Account",
    description: "Create an account to host your assistant online",
    whyMatters: "This puts your assistant on the internet so customers can use it 24/7",
    estimatedTime: "5 minutes",
    helpUrl: "https://fly.io/docs/hands-on/start/",
    helpContent: [
      "💡 Quick start with Fly.io (recommended):",
      "1. Go to fly.io and click 'Sign Up'",
      "2. Add a credit card (free tier covers most usage)",
      "3. Verify your email",
      "",
      "⏱️  Takes 5 minutes • 💰 Free tier available",
    ],
    showInModes: ["general", "ecommerce"],
  },
  {
    key: "facebookAccount",
    title: "Facebook Business Account",
    description: "Connect your Facebook page to send messages",
    whyMatters: "Your assistant will reply to customers on Facebook Messenger automatically",
    estimatedTime: "10 minutes",
    helpUrl: "https://developers.facebook.com/docs/development/create-an-app/",
    helpContent: [
      "📱 Set up your Facebook Business:",
      "1. Go to business.facebook.com",
      "2. Create your Business account (free)",
      "3. Create or connect your Facebook Page",
      "4. Note your Page ID from 'About' section",
      "",
      "⏱️  Takes 10 minutes • 💰 Totally free",
    ],
    showInModes: ["ecommerce"],
  },
  {
    key: "shopifyAccess",
    title: "Shopify Admin Access",
    description: "Connect your store to show products in chat",
    whyMatters: "Customers can browse and buy your products without leaving the conversation",
    estimatedTime: "5 minutes",
    helpUrl: "https://help.shopify.com/en/manual/products/product-collections",
    helpContent: [
      "🛍️  Get your Shopify ready:",
      "1. Log in to your Shopify admin",
      "2. Go to Settings > Apps and sales channels",
      "3. Make sure you have admin permissions",
      "4. Copy your store URL (e.g., mystore.myshopify.com)",
      "",
      "⏱️  Takes 5 minutes • ✅ You're already logged in!",
    ],
    showInModes: ["ecommerce"],
  },
  {
    key: "llmProviderChoice",
    title: "Choose AI Provider",
    description: "Pick the AI brain for your assistant",
    whyMatters: "This powers your assistant's intelligence - how it understands and responds to customers",
    estimatedTime: "5 minutes",
    helpUrl: "https://ollama.com/download",
    helpContent: [
      "🤖 Two great options:",
      "",
      "Option 1: Ollama (Free, runs on your computer)",
      "  • No cost, totally private",
      "  • Download from ollama.com",
      "  • Runs on your machine",
      "",
      "Option 2: Cloud AI (Paid, more powerful)",
      "  • OpenAI: ~$10-50/mo",
      "  • Anthropic: ~$10-50/mo",
      "  • Faster, smarter, scales better",
      "",
      "⏱️  Takes 5 minutes",
    ],
    showInModes: ["general", "ecommerce"],
  },
];

export function PrerequisiteChecklist({
  mode = "ecommerce",
}: PrerequisiteChecklistProps): React.ReactElement {
  const prefersReducedMotion = useReducedMotion();
  const {
    isComplete,
    completedCount,
    totalCount,
    cloudAccount,
    facebookAccount,
    shopifyAccess,
    llmProviderChoice,
    togglePrerequisite,
  } = onboardingStore();

  const [openHelpSection, setOpenHelpSection] = React.useState<string | null>(null);
  const [celebrated, setCelebrated] = React.useState(false);

  const stateMap: Record<PrerequisiteKey, boolean> = {
    cloudAccount,
    facebookAccount,
    shopifyAccess,
    llmProviderChoice,
  };

  // Filter prerequisites based on mode
  const visiblePrerequisites = PREREQUISITES.filter((p) =>
    p.showInModes.includes(mode),
  );

  const progressPercentage = (completedCount() / totalCount) * 100;

  // Trigger celebration when all complete
  React.useEffect(() => {
    if (isComplete() && !celebrated && !prefersReducedMotion) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#d7fff3", "#82d3ff", "#00f5d4"],
      });
      setCelebrated(true);
    }
  }, [isComplete, celebrated, prefersReducedMotion]);

  const toggleHelp = (key: string) => {
    setOpenHelpSection(openHelpSection === key ? null : key);
  };

  return (
    <div
      className="w-full max-w-2xl mx-auto p-4"
      data-theme="onboarding"
      data-testid="prerequisite-checklist"
    >
      <Card className="border-white/10 bg-white/5">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <CardTitle className="text-white">Get Ready for Setup</CardTitle>
              <CardDescription className="text-white/60">
                Complete these items to deploy your assistant. Each one has clear instructions.
              </CardDescription>
            </div>
            {isComplete() && (
              <motion.div
                initial={prefersReducedMotion ? {} : { scale: 0 }}
                animate={{ scale: 1 }}
                className="flex items-center gap-2 px-3 py-2 bg-emerald-500/20 rounded-full border border-emerald-500/30"
              >
                <Sparkles size={16} className="text-emerald-400" />
                <span className="text-sm font-bold text-emerald-400">All done!</span>
              </motion.div>
            )}
          </div>

          <div
            className="mt-4 space-y-3"
            role="status"
            aria-live="polite"
            aria-atomic="true"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-white/70" data-testid="progress-text">
                {completedCount()} of {totalCount()} completed
              </p>
              <div className="flex items-center gap-1.5 text-xs text-white/50">
                <Clock size={14} />
                <span>
                  {mode === "general" ? "~15-25" : "~25-35"} minutes total
                </span>
              </div>
            </div>
            <Progress value={completedCount()} max={totalCount()} />
          </div>
        </CardHeader>

        <CardContent>
          <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
            {visiblePrerequisites.map((item, idx) => {
              const isChecked = stateMap[item.key];
              const isOpen = openHelpSection === item.key;

              return (
                <motion.div
                  key={item.key}
                  initial={prefersReducedMotion ? {} : { opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: prefersReducedMotion ? 0 : idx * 0.1 }}
                  className={`
                    rounded-xl border-2 transition-all duration-300
                    ${isChecked
                      ? "border-emerald-500/50 bg-emerald-500/10"
                      : "border-white/10 bg-white/5"
                    }
                  `}
                >
                  <div className="p-4 space-y-3">
                    {/* Checkbox and Title */}
                    <div className="flex items-start gap-3">
                      <Checkbox
                        id={item.key}
                        label={item.title}
                        description={item.description}
                        checked={isChecked}
                        onChange={() => togglePrerequisite(item.key)}
                        dataTestId={`checkbox-${item.key}`}
                      />
                    </div>

                    {/* Why This Matters */}
                    {item.whyMatters && (
                      <div className="ml-7 pl-4 border-l-2 border-emerald-500/30">
                        <p className="text-xs text-white/60 italic">
                          💡 {item.whyMatters}
                        </p>
                      </div>
                    )}

                    {/* Help Section */}
                    <div className="ml-7">
                      <Collapsible open={isOpen} onOpenChange={() => toggleHelp(item.key)}>
                        <CollapsibleTrigger
                          data-testid={`help-button-${item.key}`}
                          className={`
                            flex items-center gap-2 text-xs font-bold uppercase tracking-wider transition-colors
                            ${isOpen ? "text-emerald-400" : "text-white/50 hover:text-white/70"}
                          `}
                        >
                          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                          {isOpen ? "Hide" : "Show"} instructions
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-3">
                          <motion.div
                            initial={prefersReducedMotion ? {} : { opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: "auto" }}
                            className="bg-black/30 rounded-lg p-4 border border-white/10"
                            data-testid={`help-section-${item.key}`}
                          >
                            <p className="text-xs font-bold text-white/70 mb-2">How to complete:</p>
                            <ul className="space-y-1">
                              {item.helpContent.map((line, idx) => (
                                <li
                                  key={idx}
                                  className="text-xs text-white/60 whitespace-pre-line font-mono"
                                >
                                  {line}
                                </li>
                              ))}
                            </ul>
                            <a
                              href={item.helpUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 mt-3 text-xs text-emerald-400 hover:text-emerald-300 font-bold transition-colors"
                            >
                              Open full guide
                              <ExternalLink size={12} />
                            </a>
                          </motion.div>
                        </CollapsibleContent>
                      </Collapsible>
                    </div>
                  </div>
                </motion.div>
              );
            })}
          </form>
        </CardContent>

        <CardFooter>
          <Button
            variant="default"
            size="lg"
            disabled={!isComplete()}
            className="w-full"
            title={isComplete() ? "All prerequisites complete!" : "Complete all prerequisites to continue"}
            dataTestId="deploy-button"
          >
            {isComplete() ? (
              <span className="flex items-center gap-2">
                <Check size={16} />
                Continue to Deployment
              </span>
            ) : (
              `Complete ${totalCount() - completedCount()} more item${totalCount() - completedCount() > 1 ? 's' : ''} to continue`
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
