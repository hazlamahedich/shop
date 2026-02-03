/** Prerequisite Checklist Component.

Displays onboarding prerequisites with checkboxes and help sections.
Deploys only when all items are checked (guard logic).

Features:
- shadcn/ui components (Card, Checkbox, Button, Collapsible, Progress)
- Zustand state management with localStorage persistence
- WCAG AA accessibility compliance
- Keyboard navigation support
- Screen reader announcements
*/

import * as React from "react";
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

export interface PrerequisiteItem {
  key: PrerequisiteKey;
  title: string;
  description: string;
  helpUrl: string;
  helpContent: string[];
}

const PREREQUISITES: PrerequisiteItem[] = [
  {
    key: "cloudAccount",
    title: "Cloud Provider Account",
    description: "Fly.io, Railway, or Render account with payment method",
    helpUrl: "https://fly.io/docs/hands-on/start/",
    helpContent: [
      "1. Sign up at fly.io, railway.app, or render.com",
      "2. Add a payment method to your account",
      "3. Verify your email address",
      "4. Keep your API credentials handy for deployment",
    ],
  },
  {
    key: "facebookAccount",
    title: "Facebook Business Account",
    description: "Meta Business account and Facebook Page created",
    helpUrl: "https://developers.facebook.com/docs/development/create-an-app/",
    helpContent: [
      "1. Create a Meta Business account at business.facebook.com",
      "2. Create a Facebook Page for your business",
      "3. Note your Page ID for configuration",
      "4. You'll need this during bot setup",
    ],
  },
  {
    key: "shopifyAccess",
    title: "Shopify Admin Access",
    description: "Store admin access with API permissions",
    helpUrl: "https://help.shopify.com/en/manual/products/product-collections",
    helpContent: [
      "1. Log in to your Shopify admin panel",
      "2. Navigate to Settings > Apps and sales channels",
      "3. Ensure you have admin-level permissions",
      "4. Have your store URL ready (e.g., mystore.myshopify.com)",
    ],
  },
  {
    key: "llmProviderChoice",
    title: "LLM Provider",
    description: "Ollama (local) or cloud API key selected",
    helpUrl: "https://ollama.com/download",
    helpContent: [
      "Option 1: Ollama (Free, Local)",
      "  - Download from ollama.com",
      "  - Install on your machine",
      "  - No API key needed",
      "",
      "Option 2: Cloud Provider (Paid, Scalable)",
      "  - OpenAI: Get API key from platform.openai.com",
      "  - Anthropic: Get API key from console.anthropic.com",
      "  - Google: Get API key from console.cloud.google.com",
    ],
  },
];

export function PrerequisiteChecklist(): React.ReactElement {
  const { isComplete, completedCount, totalCount, cloudAccount, facebookAccount, shopifyAccess, llmProviderChoice, togglePrerequisite } =
    onboardingStore();

  const stateMap: Record<PrerequisiteKey, boolean> = {
    cloudAccount,
    facebookAccount,
    shopifyAccess,
    llmProviderChoice,
  };

  const progressPercentage = (completedCount() / totalCount) * 100;

  return (
    <div className="w-full max-w-2xl mx-auto p-4" data-theme="onboarding" data-testid="prerequisite-checklist">
      <Card>
        <CardHeader>
          <CardTitle>Setup Prerequisites</CardTitle>
          <CardDescription>
            Complete these items before deploying your bot. <strong>Setup time: 30-60 minutes</strong>
          </CardDescription>
          <div className="mt-4" role="status" aria-live="polite" aria-atomic="true">
            <p className="text-sm text-slate-600 mb-2" data-testid="progress-text">
              Progress: {completedCount()} of {totalCount} items completed
            </p>
            <Progress value={completedCount()} max={totalCount} />
          </div>
        </CardHeader>

        <CardContent>
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            {PREREQUISITES.map((item) => (
              <div key={item.key} className="border-b border-slate-100 pb-4 last:border-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <Checkbox
                      id={item.key}
                      label={item.title}
                      description={item.description}
                      checked={stateMap[item.key]}
                      onChange={() => togglePrerequisite(item.key)}
                      dataTestId={`checkbox-${item.key}`}
                    />
                  </div>
                </div>

                <div className="mt-3 ml-7">
                  <Collapsible>
                    <CollapsibleTrigger data-testid={`help-button-${item.key}`}>
                      Get help
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-2">
                      <div className="bg-slate-50 rounded-md p-3 text-sm text-slate-700" data-testid={`help-section-${item.key}`}>
                        <p className="font-medium mb-2">Setup Instructions:</p>
                        <ul className="list-disc list-inside space-y-1">
                          {item.helpContent.map((line, idx) => (
                            <li key={idx} className="whitespace-pre-line">
                              {line}
                            </li>
                          ))}
                        </ul>
                        <a
                          href={item.helpUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block mt-3 text-blue-600 hover:text-blue-700 underline"
                        >
                          Open full documentation →
                        </a>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>
                </div>
              </div>
            ))}
          </form>
        </CardContent>

        <CardFooter>
          <Button
            variant="default"
            size="lg"
            disabled={!isComplete()}
            className="w-full"
            title={isComplete() ? "Ready to deploy" : "Complete all prerequisites first"}
            dataTestId="deploy-button"
          >
            {isComplete() ? "Deploy Now" : "Complete all prerequisites to deploy"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
}
